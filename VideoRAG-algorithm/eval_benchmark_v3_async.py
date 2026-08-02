"""
LLM-as-judge · 正反双序 + N-run多数票 — 异步并发版

相比 v3_majority.py 的改进：每题的 2×N 次评判调用全部并发发出，
vLLM continuous batching 自动合并 → 每题耗时 ≈ 单次调用耗时 + 小开销。

用法:
    python eval_benchmark_v3_async.py --collections 4 --runs 5 --concurrency 20
"""
import os, sys, json, time, argparse, asyncio
from collections import defaultdict, Counter
from openai import AsyncOpenAI

os.environ.setdefault("OLLAMA_HOST", "http://127.0.0.1:11435")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "reproduce", "winrate_comparison"))
from batch_winrate_eval_upload import sys_prompt, prompt as paper_prompt

METRICS = ['Comprehensiveness', 'Empowerment', 'Trustworthiness', 'Depth', 'Density', 'Overall Winner']
BASE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(BASE, "longervideos", "dataset.json")
ANSWER_ROOT = os.path.join(BASE, "longervideos", "benchmark-answers")
RESULTS_JSON = os.path.join(BASE, "longervideos", "eval_results_v3.json")
SUMMARY_MD = os.path.join(BASE, "longervideos", "eval_summary_v3.md")

VLLM_JUDGE_URL = os.environ.get("VLLM_JUDGE_URL", "http://127.0.0.1:8002/v1")
VLLM_JUDGE_MODEL = os.environ.get("VLLM_JUDGE_MODEL", "/home/gjw/models/Selene-1-Mini-Llama-3.1-8B")
JUDGE_TEMPERATURE = float(os.environ.get("JUDGE_TEMPERATURE", "0.7"))
JUDGE_MAX_RETRIES = int(os.environ.get("JUDGE_MAX_RETRIES", "2"))


def _read_answer(collection_id, qid, mode):
    path = os.path.join(ANSWER_ROOT, collection_id, f"q{qid}_{mode}.md")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        txt = f.read()
    parts = txt.split("\n\n", 1)
    return parts[1].strip() if len(parts) > 1 else txt.strip()


def _parse_eval_json(text):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        s = cleaned.find("{")
        e = cleaned.rfind("}")
        if s >= 0 and e > s:
            try:
                data = json.loads(cleaned[s:e+1])
            except:
                return None
        else:
            return None
    expected = {'Comprehensiveness', 'Empowerment', 'Trustworthiness', 'Depth', 'Density', 'Overall Winner'}
    if not expected.issubset(set(data.keys())):
        return None
    result = {}
    for k in expected:
        w = data[k].get("Winner", "")
        if "1" in w: result[k] = "A"
        elif "2" in w: result[k] = "B"
        else: return None
    return result


async def _judge_one_async(sem, client, model, prompt_text, label, run_i):
    """Single async judge call with retry. Returns dict or None."""
    async with sem:
        for retry in range(JUDGE_MAX_RETRIES + 1):
            try:
                resp = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": sys_prompt},
                              {"role": "user", "content": prompt_text}],
                    response_format={"type": "json_object"},
                    temperature=JUDGE_TEMPERATURE,
                    max_tokens=4096,
                )
                content = resp.choices[0].message.content
                parsed = _parse_eval_json(content)
                if parsed:
                    return (label, run_i, parsed)
            except Exception:
                pass
            if retry < JUDGE_MAX_RETRIES:
                await asyncio.sleep(1.5)
        return (label, run_i, None)  # failed


async def _judge_question(sem, client, model, qid, ans_e, ans_c, num_runs):
    """Fire all 2×num_runs calls concurrently, aggregate via majority vote."""
    query_text = "Evaluate the two answers."  # placeholder; real question used below
    ori_prompt = paper_prompt.format(query="Evaluate these answers", answer1=ans_e, answer2=ans_c)
    rev_prompt = paper_prompt.format(query="Evaluate these answers", answer1=ans_c, answer2=ans_e)

    tasks = []
    for run_i in range(num_runs):
        tasks.append(_judge_one_async(sem, client, model, ori_prompt, "ori", run_i))
        tasks.append(_judge_one_async(sem, client, model, rev_prompt, "rev", run_i))

    all_results = await asyncio.gather(*tasks)

    # Organize: label -> list of parsed dicts
    runs = {"ori": [], "rev": []}
    for label, run_i, parsed in all_results:
        if parsed is not None:
            runs[label].append(parsed)

    if len(runs["ori"]) == 0 or len(runs["rev"]) == 0:
        return None, None, None  # total failure

    # Majority vote: count entity vs causal wins across all ori+rev runs
    # ori: A=entity, B=causal    rev: A=causal, B=entity
    final = {}
    vote_detail = {}
    for m in METRICS:
        entity_votes = 0; causal_votes = 0
        for r in runs["ori"]:
            if r[m] == 'A': entity_votes += 1
            else: causal_votes += 1
        for r in runs["rev"]:
            if r[m] == 'A': causal_votes += 1
            else: entity_votes += 1
        total = entity_votes + causal_votes
        vote_detail[m] = f"e{entity_votes}/c{causal_votes}"
        if entity_votes > total / 2:
            final[m] = 'entity'
        elif causal_votes > total / 2:
            final[m] = 'causal'
        else:
            final[m] = 'tie'

    return final, vote_detail, runs


async def evaluate_async(collections, num_runs=5, concurrency=20):
    import urllib.request as _ur
    try:
        _ur.urlopen("http://127.0.0.1:8002/v1/models", timeout=2)
        client = AsyncOpenAI(api_key="EMPTY", base_url=VLLM_JUDGE_URL, timeout=120.0)
        model = VLLM_JUDGE_MODEL
        print(f"评判器: vLLM {model} @ {VLLM_JUDGE_URL}")
    except:
        client = AsyncOpenAI(api_key="ollama", base_url="http://127.0.0.1:11435/v1", timeout=120.0)
        model = "qwen2.5:14b"
        print(f"评判器: Ollama {model}")
    print(f"temperature={JUDGE_TEMPERATURE}, runs={num_runs}, 并发={concurrency}")
    sem = asyncio.Semaphore(concurrency)

    with open(DATASET) as f:
        dataset = json.load(f)

    stats = {m: {"entity": 0, "causal": 0} for m in METRICS}
    per_coll = {}
    raw_results = []
    skipped = tied = 0

    for cid in [c for c in collections if c in dataset]:
        questions = dataset[cid][0]["questions"]
        desc = dataset[cid][0]["description"]
        per_coll[cid] = {m: {"entity": 0, "causal": 0} for m in METRICS}
        print(f"\n=== 集合 {cid}: {desc} ({len(questions)}题) ===")

        for qi, q in enumerate(questions):
            qid = q["id"]
            ans_e = _read_answer(cid, qid, "entity_only")
            ans_c = _read_answer(cid, qid, "causal_only")
            if ans_e is None or ans_c is None:
                print(f"  q{qid}: 缺答案 跳过"); skipped += 1; continue

            t0 = time.time()
            final, vote_detail, runs = await _judge_question(sem, client, model, qid, ans_e, ans_c, num_runs)
            elapsed = time.time() - t0

            if final is None:
                print(f"  q{qid}: 全部调用失败 跳过 ({elapsed:.0f}s)"); skipped += 1; continue

            ow = final.get('Overall Winner')
            if ow == 'tie':
                print(f"  q{qid}: 无多数 ({elapsed:.0f}s) 票:{vote_detail['Overall Winner']} → 剔除"); tied += 1; continue

            # Count valid
            for m in METRICS:
                w = final[m]
                if w == 'entity':
                    stats[m]["entity"] += 1; per_coll[cid][m]["entity"] += 1
                elif w == 'causal':
                    stats[m]["causal"] += 1; per_coll[cid][m]["causal"] += 1

            print(f"  q{qid}: {ow:>6} ({elapsed:.0f}s) 票:{vote_detail['Overall Winner']}")

            raw_results.append({
                "collection": cid, "qid": qid, "question": q["question"],
                "final": final, "vote_detail": vote_detail,
                "ori_ok": len(runs.get("ori", [])), "rev_ok": len(runs.get("rev", [])),
            })

    # Write results
    with open(RESULTS_JSON, "w") as f:
        json.dump(raw_results, f, ensure_ascii=False, indent=2)

    valid_questions = len(raw_results)
    total_expected = sum(len(dataset[c][0]["questions"]) for c in collections if c in dataset)

    lines = [
        f"# EC-RAG(causal) vs 实体图(entity) · 正反双序 + {num_runs}-run多数票 (异步并发)",
        f"裁判: {model} (temperature={JUDGE_TEMPERATURE}, 并发={concurrency})",
        f"题目: {valid_questions}/{total_expected} 有效 (跳过{skipped}, 无多数剔除{tied})",
        "",
        "## 各维度胜率 (causal胜 / entity胜 / 有效题数)",
        "| 维度 | causal | entity | causal胜率 | 有效题数 |",
        "|---|---|---|---|---|",
    ]
    for m in METRICS:
        en, ca = stats[m]["entity"], stats[m]["causal"]
        t = en + ca
        lines.append(f"| {m} | {ca} | {en} | {100*ca//t}% | {t} |" if t else f"| {m} | — | — | — | — |")

    for cid in sorted(collections):
        lines.append(f"\n### 集合 {cid}")
        lines.append("| 维度 | causal | entity | causal胜率 | 有效题数 |"); lines.append("|---|---|---|---|---|")
        for m in METRICS:
            d = per_coll.get(cid, {}).get(m, {"entity": 0, "causal": 0})
            en, ca = d["entity"], d["causal"]
            t = en + ca
            lines.append(f"| {m} | {ca} | {en} | {100*ca//t}% | {t} |" if t else f"| {m} | — | — | — | — |")

    total_calls = valid_questions * 2 * num_runs
    lines.append(f"\n---\n总计 {total_calls} 次评判调用，{valid_questions} 题有效，{tied} 题无明确多数被剔除")

    summary = "\n".join(lines)
    with open(SUMMARY_MD, "w") as f:
        f.write(summary + "\n")
    print("\n" + summary)
    print(f"\n详细: {RESULTS_JSON}\n汇总: {SUMMARY_MD}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--collections", type=str, required=True)
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--concurrency", type=int, default=20, help="最大并发vLLM请求数")
    args = ap.parse_args()
    asyncio.run(evaluate_async([c.strip() for c in args.collections.split(",") if c.strip()],
                                num_runs=args.runs, concurrency=args.concurrency))


if __name__ == "__main__":
    main()
