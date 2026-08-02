"""
Event-Causal Knowledge Graph Module (EC-RAG, Yan et al. 2026)

Faithful implementation of the State-Event-State (SES) Memory Constructor and the
bidirectional retrieval RAG described in EC-RAG (Section 3.2 & 3.3, Appendix A/B),
adapted to the VideoRAG text pipeline (per-segment caption + transcript).

Pipeline:
  1. extract_events_from_segments()        – Entity-First SES triplet extraction (LLM, JSON)
  2. link_events_by_state_continuity()      – build [:TEMPORAL_NEXT] edges via PostState↔PreState
                                              embedding similarity (> gamma), NOT pairwise LLM judging
  3. build_event_causal_graph()             – insert Event nodes (with pre/post state) + causal edges
  4. embed_events_for_vdb()                 – event embeddings for the vector store
  5. causal_chain_retrieval()               – 3-step bidirectional retrieval:
                                              entry anchoring -> N-hop bidirectional walk
                                              -> timeline flattening + semantic dedup
"""

import asyncio
import json
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np

from ._storage import NanoVectorDBStorage, NetworkXStorage
from ._utils import (
    compute_mdhash_id,
    logger,
    clean_str,
)
from .prompt import PROMPTS

# ---------------------------------------------------------------------------
# Constants (EC-RAG paper defaults)
# ---------------------------------------------------------------------------

# Entity-merge / state-continuity threshold (paper: gamma_ent = gamma_evt = 0.85)
GAMMA_STATE_CONTINUITY = 0.85

# Semantic-deduplication threshold during retrieval (paper: tau_dup = 0.85)
TAU_DEDUP = 0.85

# Bidirectional walk hops (paper: N = 2)
DEFAULT_CAUSAL_HOPS = 2

# Look-ahead window (in temporal order) when weaving state-continuity edges.
# The paper links consecutive chunks (Sprev -> SESc); we allow a small window so
# that parallel action chains can be woven into a denser mesh.
STATE_CONTINUITY_WINDOW = 3

# Edge label used for state-continuity causal links.
TEMPORAL_NEXT_EDGE = "TEMPORAL_NEXT"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_start_seconds(timestamp: str) -> float:
    """Parse a 'start-end' (seconds) timestamp string into the start second.

    Returns a large sentinel on failure so unparseable events sort last but stay
    deterministic.
    """
    if not timestamp:
        return float("inf")
    try:
        start = timestamp.split("-")[0].strip()
        return float(start)
    except (ValueError, IndexError):
        return float("inf")


def _event_sort_key(evt: dict) -> tuple:
    """Chronological sort key: (start_seconds, segment_index, temporal_order)."""
    try:
        seg = int(evt.get("segment_index", 0))
    except (ValueError, TypeError):
        seg = 0
    try:
        order = int(evt.get("temporal_order", 0))
    except (ValueError, TypeError):
        order = 0
    return (_parse_start_seconds(evt.get("timestamp", "")), seg, order)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two 1-D vectors."""
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


async def _embed_texts_batched(
    texts: List[str],
    embedding_func: callable,
    batch_size: int = 32,
) -> np.ndarray:
    """Embed a list of texts in fixed-size batches to respect endpoint limits.

    The project's embedding functions (Ollama/OpenAI) do not batch internally, so
    we chunk here to avoid oversized requests on long videos.
    """
    if not texts:
        return np.empty((0, 0))
    batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]
    parts = await asyncio.gather(*[embedding_func(b) for b in batches])
    return np.concatenate([np.asarray(p) for p in parts], axis=0)


def _extract_json_block(text: str) -> Optional[dict]:
    """Extract the first JSON object from an LLM response (tolerant to fences/prose)."""
    if not text:
        return None
    # Strip common markdown code fences.
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    # Fast path.
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Fallback: grab the outermost {...} span.
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    snippet = cleaned[start : end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Step 1: SES (State-Event-State) Extraction  单片段 SES 抽取（异步）
# ---------------------------------------------------------------------------

async def extract_events_from_segments(
    video_name: str,
    segments_info: dict,           # segment_index → {content, time, transcript, ...}
    global_config: dict,
) -> List[dict]:
    """Extract State-Event-State (SES) triplets from each video segment via LLM.

    Faithful to EC-RAG's Entity-First two-step CoT (Appendix B.1): the LLM first
    inventories entities (with visual attributes) and then emits structured events,
    each carrying its pre-state and post-state. Output is strict JSON.

    Returns
    -------
    list[dict]
        Each dict::
            {
                "event_id": "evt-<hash>",
                "event_description": "...",
                "event_actors": "entity, entity, ...",   # comma-joined for VDB content
                "entities": [ ... ],
                "location": "...",
                "pre_state": "...",
                "post_state": "...",
                "temporal_order": int,
                "scene_inventory": [ ... ],               # segment-level, repeated per event
                "video_name": str,
                "segment_index": str,
                "timestamp": str,                          # "start-end" (seconds)
            }
    """
    use_llm_func: callable = global_config["llm"]["best_model_func"]
    ses_prompt = PROMPTS["ses_extraction"]

    all_events: List[dict] = []
    segment_indices = sorted(segments_info.keys(), key=lambda x: int(x))

    async def _extract_one_segment(seg_idx: str) -> List[dict]:
        seg_data = segments_info[seg_idx]
        segment_content = seg_data.get("content", "")
        timestamp = seg_data.get("time", "")

        if not segment_content or not segment_content.strip():
            return []

        prompt = ses_prompt.format(segment_content=segment_content)
        result = await use_llm_func(prompt)

        parsed = _extract_json_block(result)
        if parsed is None:
            logger.warning(
                f"[SES Extraction] {video_name}:{seg_idx} – failed to parse JSON, skipping"
            )
            return []

        scene_inventory = parsed.get("scene_inventory", []) or []
        raw_events = parsed.get("events", []) or []
        if not isinstance(raw_events, list):
            return []

        events: List[dict] = []
        for i, ev in enumerate(raw_events):
            if not isinstance(ev, dict):
                continue
            event_desc = clean_str(str(ev.get("description", "")).strip())
            if not event_desc:
                continue

            entities = ev.get("entities", []) or []
            if isinstance(entities, str):
                entities = [e.strip() for e in entities.split(",") if e.strip()]
            entities = [clean_str(str(e).strip()) for e in entities if str(e).strip()]

            try:
                temporal_order = int(ev.get("temporal_order", i + 1))
            except (ValueError, TypeError):
                temporal_order = i + 1

            location = clean_str(str(ev.get("location", "")).strip())
            pre_state = clean_str(str(ev.get("pre_state", "")).strip())
            post_state = clean_str(str(ev.get("post_state", "")).strip())

            event_id = compute_mdhash_id(
                f"{video_name}_{seg_idx}_{temporal_order}_{event_desc}", prefix="evt-"
            )
            events.append({
                "event_id": event_id,
                "event_description": event_desc,
                "event_actors": ", ".join(entities),
                "entities": entities,
                "location": location,
                "pre_state": pre_state,
                "post_state": post_state,
                "temporal_order": temporal_order,
                "scene_inventory": scene_inventory,
                "video_name": video_name,
                "segment_index": seg_idx,
                "timestamp": timestamp,
            })

        return events

    results = await asyncio.gather(
        *[_extract_one_segment(idx) for idx in segment_indices]
    )
    for events in results:
        all_events.extend(events)

    logger.info(
        f"[SES Extraction] {video_name}: extracted {len(all_events)} events "
        f"from {len(segments_info)} segments"
    )
    return all_events


# ---------------------------------------------------------------------------
# Step 2: State-Continuity Linking  状态连续性建边（EC-RAG core）
# ---------------------------------------------------------------------------

async def link_events_by_state_continuity(
    events: List[dict],
    embedding_func: callable,
    gamma: float = GAMMA_STATE_CONTINUITY,
    window: int = STATE_CONTINUITY_WINDOW,
    max_events_for_pairing: int = 4000,
) -> List[dict]:
    """Build [:TEMPORAL_NEXT] causal edges via State Continuity (EC-RAG, Alg.1 Phase 2).

    For each pair of chronologically ordered events (Event_i, Event_j) with i<j
    within a small look-ahead window, we compute the cosine similarity between
    ``Event_i.post_state`` and ``Event_j.pre_state``. If it exceeds ``gamma``, the
    two are fused with a directed ``TEMPORAL_NEXT`` edge (cause -> effect).

    This replaces the previous pairwise-LLM causal judgement: no extra LLM calls,
    faithful to the paper's embedding-based state fusion.

    Parameters
    ----------
    events : list[dict]
        SES event dicts (must carry pre_state / post_state / video / order).
    embedding_func : callable
        Async batch embedding function (e.g. ``event_vdb.embedding_func``); takes a
        list[str] and returns an array of shape (N, dim).
    gamma : float
        State-continuity similarity threshold.
    window : int
        Look-ahead window over the chronological order (per video).
    max_events_for_pairing : int
        Safety cap on events per video to bound compute.

    Returns
    -------
    list[dict]
        Each dict::
            {
                "source_event_id": str,   # Event_i (cause)
                "target_event_id": str,   # Event_j (effect)
                "relation_type": "TEMPORAL_NEXT",
                "relation_description": str,
                "weight": float,          # the state-continuity similarity
            }
    """
    if len(events) < 2:
        logger.info("[State Continuity] Fewer than 2 events, skipping edge construction")
        return []

    # Group by video – causal chains are intra-video here.
    video_events: Dict[str, List[dict]] = defaultdict(list)
    for evt in events:
        video_events[evt["video_name"]].append(evt)

    all_relations: List[dict] = []

    for video_name, v_events in video_events.items():
        if len(v_events) < 2:
            continue
        v_events = sorted(v_events, key=_event_sort_key)[:max_events_for_pairing]

        # Embed all pre-states and post-states in one batched pass per video.
        # Empty states fall back to the event description so similarity is still meaningful.
        pre_texts = [e.get("pre_state") or e["event_description"] for e in v_events]
        post_texts = [e.get("post_state") or e["event_description"] for e in v_events]

        pre_emb = await _embed_texts_batched(pre_texts, embedding_func)
        post_emb = await _embed_texts_batched(post_texts, embedding_func)

        n = len(v_events)
        for i in range(n):
            for j in range(i + 1, min(i + 1 + window, n)):
                sim = _cosine(post_emb[i], pre_emb[j])
                if sim >= gamma:
                    all_relations.append({
                        "source_event_id": v_events[i]["event_id"],
                        "target_event_id": v_events[j]["event_id"],
                        "relation_type": TEMPORAL_NEXT_EDGE,
                        "relation_description": (
                            f"State continuity: \"{v_events[i].get('post_state', '')}\" "
                            f"→ \"{v_events[j].get('pre_state', '')}\" (sim={sim:.3f})"
                        ),
                        "weight": sim,
                    })

        logger.info(
            f"[State Continuity] {video_name}: {n} events → "
            f"{sum(1 for r in all_relations if True)} candidate edges so far"
        )

    logger.info(
        f"[State Continuity] Total: {len(all_relations)} TEMPORAL_NEXT edges "
        f"(gamma={gamma}, window={window})"
    )
    return all_relations


# Backward-compatible alias: the pipeline previously called extract_causal_relations().
# It now performs embedding-based state-continuity linking (EC-RAG faithful).
async def extract_causal_relations(
    events: List[dict],
    global_config: dict,
    embedding_func: callable = None,
    **kwargs,
) -> List[dict]:
    """Compatibility wrapper → :func:`link_events_by_state_continuity`.

    ``embedding_func`` may be passed explicitly; otherwise the caller must supply
    one via ``global_config['event_embedding_func']``.
    """
    if embedding_func is None:
        embedding_func = global_config.get("event_embedding_func")
    if embedding_func is None:
        raise ValueError(
            "extract_causal_relations now requires an embedding_func for "
            "state-continuity linking (EC-RAG). Pass it explicitly or set "
            "global_config['event_embedding_func']."
        )
    return await link_events_by_state_continuity(events, embedding_func)


# ---------------------------------------------------------------------------
# Step 3: Build Event-Causal (SES) Graph
# ---------------------------------------------------------------------------

def build_event_causal_graph(
    events: List[dict],
    causal_relations: List[dict],
    graph_storage: NetworkXStorage,
) -> NetworkXStorage:
    """Insert SES event nodes and TEMPORAL_NEXT causal edges into the graph storage.

    Each Event node stores the natural-language description together with its
    pre-state, post-state, location and involved entities (EC-RAG SES schema).
    """
    for evt in events:
        graph_storage._graph.add_node(
            evt["event_id"],
            entity_type="EVENT",
            description=evt["event_description"],
            event_actors=evt.get("event_actors", ""),
            entities="; ".join(evt.get("entities", []) or []),
            location=evt.get("location", ""),
            pre_state=evt.get("pre_state", ""),
            post_state=evt.get("post_state", ""),
            temporal_order=evt.get("temporal_order", 0),
            video_name=evt["video_name"],
            segment_index=evt["segment_index"],
            timestamp=evt.get("timestamp", ""),
            source_id=evt["segment_index"],
        )

    for rel in causal_relations:
        for endpoint in ("source_event_id", "target_event_id"):
            node_id = rel[endpoint]
            if not graph_storage._graph.has_node(node_id):
                graph_storage._graph.add_node(
                    node_id,
                    entity_type="EVENT",
                    description=rel.get("relation_description", ""),
                    source_id="",
                )

        graph_storage._graph.add_edge(
            rel["source_event_id"],
            rel["target_event_id"],
            weight=float(rel.get("weight", 1.0)),
            description=rel.get("relation_description", ""),
            relation_type=rel.get("relation_type", TEMPORAL_NEXT_EDGE),
            source_id="state_continuity",
            order=1,
        )

    logger.info(
        f"[Event-Causal Graph] Built: {len(events)} event nodes, "
        f"{len(causal_relations)} TEMPORAL_NEXT edges"
    )
    return graph_storage


# ---------------------------------------------------------------------------
# Step 4: Event embeddings for the vector store
# ---------------------------------------------------------------------------

async def embed_events_for_vdb(
    events: List[dict],
    event_vdb: NanoVectorDBStorage,
) -> None:
    """Embed each SES event and upsert into the event vector DB (entry anchoring index).

    Embedding content = description + entities + pre/post state, so that both
    semantic ("what happened") and state ("what changed") facets are searchable.
    """
    if not events:
        return

    data_for_vdb = {}
    for evt in events:
        eid = evt["event_id"]
        content = (
            f"{evt['event_description']}. "
            f"Entities: {evt.get('event_actors', '')}. "
            f"Before: {evt.get('pre_state', '')}. "
            f"After: {evt.get('post_state', '')}."
        )
        data_for_vdb[eid] = {
            "content": content,
            "event_id": eid,
        }

    await event_vdb.upsert(data_for_vdb)
    logger.info(f"[Event VDB] Upserted {len(data_for_vdb)} event embeddings")


# ---------------------------------------------------------------------------
# Step 5: Bidirectional Retrieval RAG  三步双向检索（EC-RAG Section 3.3）
# ---------------------------------------------------------------------------

async def _refine_causal_query(query: str, global_config: dict) -> str:
    """Rewrite the query to emphasise causal/event structure before anchoring."""
    use_llm_func: callable = global_config["llm"]["cheap_model_func"]
    rewrite_prompt = PROMPTS["causal_chain_retrieval_query"]
    prompt = rewrite_prompt.format(input_text=query)
    return await use_llm_func(prompt)


def _node_text(node_data: dict) -> str:
    """Build a compact textual representation of an event node for dedup/serialisation."""
    parts = [node_data.get("description", "")]
    if node_data.get("pre_state"):
        parts.append(f"Before: {node_data['pre_state']}")
    if node_data.get("post_state"):
        parts.append(f"After: {node_data['post_state']}")
    return ". ".join(p for p in parts if p)


def _serialize_causal_chain(kept_nodes: List[tuple], graph) -> str:
    """Serialise the retrieved SES events + causal links into a text block for the LLM.

    Faithful to EC-RAG 3.3: the retrieved event graph is serialised and provided to
    the backbone model so it can reason over the event-causal structure — not just
    the raw segment captions. Events are already timeline-flattened by the caller.

    Output format::

        [Event Timeline]
        T1 (12-18s) @location The user opens the AutoDL webpage
             before: no server options visible | after: server options are shown
        T2 (18-24s) The user selects an RTX 3090 GPU configuration
             ...
        [Causal Links]
        - "opens the AutoDL webpage" --TEMPORAL_NEXT--> "selects an RTX 3090 ..."
    """
    if not kept_nodes:
        return ""

    kept_ids = {eid for eid, _ in kept_nodes}

    lines = ["[Event Timeline]"]
    for i, (eid, nd) in enumerate(kept_nodes, start=1):
        ts = nd.get("timestamp", "")
        loc = nd.get("location", "")
        desc = nd.get("description", "")
        head = f"T{i}"
        if ts:
            head += f" ({ts}s)"
        if loc:
            head += f" @{loc}"
        lines.append(f"{head} {desc}")
        pre = nd.get("pre_state", "")
        post = nd.get("post_state", "")
        if pre or post:
            lines.append(f"     before: {pre or 'n/a'} | after: {post or 'n/a'}")

    edge_lines = []
    for u, v in graph.edges():
        if u in kept_ids and v in kept_ids:
            du = graph.nodes[u].get("description", u)[:60]
            dv = graph.nodes[v].get("description", v)[:60]
            rel = graph.edges[u, v].get("relation_type", "TEMPORAL_NEXT")
            edge_lines.append(f'- "{du}" --{rel}--> "{dv}"')
    if edge_lines:
        lines.append("")
        lines.append("[Causal Links]")
        lines.extend(edge_lines)

    return "\n".join(lines)


async def causal_chain_retrieval(
    query: str,
    event_vdb: NanoVectorDBStorage,
    event_causal_graph: NetworkXStorage,
    text_chunks_db,
    global_config: dict,
    top_k_events: int = 10,
    n_hops: int = DEFAULT_CAUSAL_HOPS,
    tau_dup: float = TAU_DEDUP,
    return_chain_text: bool = False,
):
    """Retrieve video segments via EC-RAG's 3-step bidirectional retrieval.

    Step 1 (Entry Anchoring): rewrite the query and match it against the event
        vector DB to get the most semantically relevant seed events.
    Step 2 (Bidirectional Walk Selection): collect all distinct nodes within
        ``n_hops`` of each anchor along causal edges (both causes and effects),
        without directed path enumeration.
    Step 3 (Semantic Refinement): flatten the collected nodes chronologically by
        timestamp and prune redundant nodes whose text is > ``tau_dup`` cosine
        similar to an already-kept node (semantic state collapse).

    Returns
    -------
    set
        The set of segment IDs, if ``return_chain_text`` is False (default).
    tuple[set, str]
        ``(segments, chain_text)`` if ``return_chain_text`` is True, where
        ``chain_text`` is the serialised event-causal chain for the LLM prompt.
    """
    # ---- Step 1: Entry Anchoring ----
    causal_query = await _refine_causal_query(query, global_config)
    logger.info(f"[Causal Retrieval] Rewritten query: {causal_query}")

    event_results = await event_vdb.query(causal_query, top_k=top_k_events)
    if not len(event_results):
        logger.info("[Causal Retrieval] No seed events found")
        return (set(), "") if return_chain_text else set()

    seed_event_ids = [r["id"] for r in event_results]
    logger.info(f"[Causal Retrieval] Seed events: {len(seed_event_ids)}")

    # ---- Step 2: Bidirectional Walk Selection (N-hop, undirected reachability) ----
    # The backing store is an undirected nx.Graph, so a neighbour walk already
    # collects both causes and effects within N hops — exactly the paper's
    # "collect all distinct nodes within N hops without path enumeration".
    all_event_ids = set(seed_event_ids)
    frontier = set(seed_event_ids)
    graph = event_causal_graph._graph
    directed = graph.is_directed()

    for _ in range(n_hops):
        next_frontier = set()
        for event_id in frontier:
            if not graph.has_node(event_id):
                continue
            if directed:
                neighbors = list(graph.successors(event_id)) + list(graph.predecessors(event_id))
            else:
                neighbors = list(graph.neighbors(event_id))
            for nb in neighbors:
                if nb not in all_event_ids:
                    next_frontier.add(nb)
                    all_event_ids.add(nb)
        frontier = next_frontier
        if not frontier:
            break

    logger.info(
        f"[Causal Retrieval] {len(all_event_ids)} events after {n_hops}-hop "
        f"bidirectional walk (from {len(seed_event_ids)} seeds)"
    )

    # ---- Step 3: Semantic Refinement (timeline flatten + semantic dedup) ----
    candidate_nodes = []
    for event_id in all_event_ids:
        if not graph.has_node(event_id):
            continue
        node_data = graph.nodes[event_id]
        candidate_nodes.append((event_id, node_data))

    # Timeline flattening: sort by physical timestamp, then segment/order.
    candidate_nodes.sort(
        key=lambda x: _event_sort_key({
            "timestamp": x[1].get("timestamp", ""),
            "segment_index": x[1].get("segment_index", 0),
            "temporal_order": x[1].get("temporal_order", 0),
        })
    )

    embedding_func = getattr(event_vdb, "embedding_func", None)
    seen_embeddings: List[np.ndarray] = []
    kept_nodes = []

    if embedding_func is not None and candidate_nodes:
        texts = [_node_text(nd) or nd.get("description", "") for _, nd in candidate_nodes]
        node_embeddings = await _embed_texts_batched(texts, embedding_func)
        for idx, (event_id, node_data) in enumerate(candidate_nodes):
            vec = node_embeddings[idx]
            if seen_embeddings:
                smax = max(_cosine(vec, v) for v in seen_embeddings)
            else:
                smax = 0.0
            if smax > tau_dup:
                continue  # redundant → prune (semantic state collapse)
            seen_embeddings.append(vec)
            kept_nodes.append((event_id, node_data))
    else:
        kept_nodes = candidate_nodes

    logger.info(
        f"[Causal Retrieval] Semantic dedup: {len(candidate_nodes)} → "
        f"{len(kept_nodes)} nodes (tau_dup={tau_dup})"
    )

    # ---- Map kept events back to segments ----
    causal_segments = set()
    for _, node_data in kept_nodes:
        video_name = node_data.get("video_name", "")
        segment_index = node_data.get("segment_index", "")
        if video_name and segment_index != "":
            causal_segments.add(f"{video_name}_{segment_index}")

    logger.info(
        f"[Causal Retrieval] Retrieved {len(causal_segments)} segments "
        f"from {len(kept_nodes)} deduplicated events"
    )

    if return_chain_text:
        chain_text = _serialize_causal_chain(kept_nodes, graph)
        logger.info(
            f"[Causal Retrieval] Serialised causal chain: "
            f"{len(kept_nodes)} events, {len(chain_text)} chars"
        )
        return causal_segments, chain_text
    return causal_segments

