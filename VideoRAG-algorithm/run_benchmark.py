"""
LongerVideos 大规模批处理 · EC-RAG 因果图 vs 实体图对比

对指定集合：
  1. 索引集合内所有视频（若 workdir 已建则跳过 → 断点续跑）
  2. 对每个问题，分别用 entity_only / causal_only 两种检索模式生成答案
  3. 答案落盘（若已存在则跳过 → 断点续跑）

用法:
    python run_benchmark.py --collections 0,3 --cuda 0
    python run_benchmark.py --collections 0            # 先跑通单集合

用我们调好的 ollama_config（qwen2.5:14b + qwen3-embedding:4b）。
"""
import os
import json
import argparse
import logging
import warnings
import multiprocessing
import traceback

warnings.filterwarnings("ignore")
logging.getLogger("httpx").setLevel(logging.WARNING)

os.environ.setdefault("OLLAMA_HOST", "http://127.0.0.1:11435")

BASE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(BASE, "longervideos", "dataset.json")
WORKDIR_ROOT = os.path.join(BASE, "longervideos", "ecrag-workdir")
ANSWER_ROOT = os.path.join(BASE, "longervideos", "benchmark-answers")
MODES = ["entity_only", "causal_only"]

def find_collection_dir(collection_id: str) -> str:
    """按集合号找到 longervideos/{id}-xxx 目录。"""
    for name in os.listdir(os.path.join(BASE, "longervideos")):
        if name.split("-")[0] == collection_id and os.path.isdir(
            os.path.join(BASE, "longervideos", name)
        ):
            return os.path.join(BASE, "longervideos", name)
    return None


def index_collection(collection_id: str, videorag_cls, llm_config):
    """索引一个集合内所有视频；若 workdir 已存在则复用（断点续跑）。"""
    coll_dir = find_collection_dir(collection_id)
    if coll_dir is None:
        print(f"[跳过] 集合 {collection_id}: 找不到目录")
        return None
    video_dir = os.path.join(coll_dir, "videos")
    if not os.path.isdir(video_dir):
        print(f"[跳过] 集合 {collection_id}: 无 videos/ 目录")
        return None
    video_files = sorted(f for f in os.listdir(video_dir) if f.endswith(".mp4"))
    if not video_files:
        print(f"[跳过] 集合 {collection_id}: 无 .mp4 视频（需先下载）")
        return None

    workdir = os.path.join(WORKDIR_ROOT, collection_id)
    video_paths = [os.path.join(video_dir, f) for f in video_files]
    print(f"[索引] 集合 {collection_id}: {len(video_paths)} 个视频 → {workdir}")

    videorag = videorag_cls(
        llm=llm_config,
        working_dir=workdir,
        enable_local=True,
        enable_event_causal=True,
    )
    # insert_video 内部对已索引视频会自动跳过（video_name in video_segments._data）
    videorag.insert_video(video_path_list=video_paths) # insert_video()内部是 /videorag/videorag.py 中VideoRAG的方法，这是触发_event_causal.py的地方
    return workdir


def query_collection(collection_id: str, workdir, dataset, videorag_cls, llm_config, QueryParam):
    """对集合的每个问题跑 entity_only / causal_only，答案落盘（已存在则跳过）。"""
    questions = dataset[collection_id][0]["questions"]
    answer_dir = os.path.join(ANSWER_ROOT, collection_id)
    os.makedirs(answer_dir, exist_ok=True)

    videorag = videorag_cls(
        llm=llm_config,
        working_dir=workdir,
        enable_local=True,
        enable_event_causal=True,
    )
    videorag.load_caption_model(debug=False)

    for q in questions:
        qid = q["id"]
        question = q["question"]
        for mode in MODES:
            out_path = os.path.join(answer_dir, f"q{qid}_{mode}.md")
            if os.path.exists(out_path):
                print(f"  [跳过] 集合{collection_id} q{qid} {mode}（已存在）")
                continue
            print(f"  [查询] 集合{collection_id} q{qid} {mode}: {question[:40]}")
            try:
                param = QueryParam(mode="videorag")
                param.wo_reference = True
                param.retrieval_mode = mode
                ans = videorag.query(query=question, param=param)
            except Exception as e:
                ans = f"[ERROR] {e}\n{traceback.format_exc()}"
                print(f"    !! 查询失败: {e}")
            with open(out_path, "w") as f:
                f.write(f"Collection: {collection_id}\nQID: {qid}\nMode: {mode}\n"
                        f"Question: {question}\n\n{ans}\n")


def main():
    ap = argparse.ArgumentParser(description="LongerVideos EC-RAG batch benchmark")
    ap.add_argument("--collections", type=str, required=True,
                    help="逗号分隔的集合号，如 0,3")
    ap.add_argument("--cuda", type=str, default=None,
                    help="可选：限定 CUDA_VISIBLE_DEVICES")
    ap.add_argument("--backend", type=str, default="ollama",
                    choices=["ollama", "vllm"],
                    help="推理后端：ollama（默认）或 vllm")
    args = ap.parse_args()

    if args.backend == "vllm":
        # vLLM LLM 服务独占 GPU0，主进程 (ImageBind / MiniCPM) 只用 GPU1+
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "1,2")
        os.environ.setdefault("VIDEORAG_CAPTION_GPUS", "1,2")
    if args.cuda is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = args.cuda

    multiprocessing.set_start_method("spawn", force=True)

    if args.backend == "vllm":
        from videorag._llm import vllm_config as active_config
        print(f"推理后端: vLLM (LLM:8000 + Embed:8001), 主进程GPU: {os.environ.get('CUDA_VISIBLE_DEVICES')}")
    else:
        from videorag._llm import ollama_config as active_config
        print("推理后端: Ollama (11435)")
    from videorag import VideoRAG, QueryParam

    with open(DATASET) as f:
        dataset = json.load(f)

    collections = [c.strip() for c in args.collections.split(",") if c.strip()]
    print(f"=== 批处理集合: {collections} ===")

    for cid in collections:
        if cid not in dataset:
            print(f"[跳过] 集合 {cid} 不在 dataset.json")
            continue
        print(f"\n{'='*60}\n集合 {cid}: {dataset[cid][0]['description']}\n{'='*60}")
        try:
            workdir = index_collection(cid, VideoRAG, active_config) # index_collection() 调用 videorag.insert_video()，内部自动触发 _event_causal.py 的抽取逻辑 
            if workdir is None:
                continue
            query_collection(cid, workdir, dataset, VideoRAG, active_config, QueryParam) # 再次调用VideoRAG
        except Exception as e:
            print(f"[集合 {cid} 出错] {e}\n{traceback.format_exc()}")
            continue

    print("\n=== 批处理完成 ===")


if __name__ == "__main__":
    main()

