"""
Event-Causal Knowledge Graph Module

Implements the Event-Causal RAG approach from Yan et al. (2026), integrated into the
VideoRAG pipeline.  Two-step extraction:

  1. extract_events_from_segments()   – per-segment event extraction (LLM)
  2. extract_causal_relations()       – pairwise causal judgement on extracted events (LLM)

Then build_event_causal_graph() constructs a NetworkX graph, and
causal_chain_retrieval() performs N-hop causal-chain traversal for retrieval.
"""

import asyncio
import logging
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np
from tiktoken import encoding_for_model

from ._storage import NanoVectorDBStorage, NetworkXStorage
from ._utils import (
    compute_mdhash_id,
    encode_string_by_tiktoken,
    logger,
    split_string_by_multi_markers,
    clean_str,
)
from .prompt import PROMPTS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Max events per LLM call for causal-relation extraction (batch mode)
MAX_EVENTS_PER_CAUSAL_BATCH = 20

# Default causal-chain traversal hops
DEFAULT_CAUSAL_HOPS = 2

# Temporal window: when batching events for causal extraction, group events
# whose segments are within this many segment-indices of each other.
CAUSAL_WINDOW_SEGMENTS = 10


# ---------------------------------------------------------------------------
# Step 1: Event Extraction
# ---------------------------------------------------------------------------

async def extract_events_from_segments(
    video_name: str,
    segments_info: dict,           # segment_index → {content, time, transcript, ...}
    global_config: dict,
) -> List[dict]:
    """Extract atomic events from each video segment via LLM.

    Parameters
    ----------
    video_name : str
        Name of the video (used for event node IDs).
    segments_info : dict
        Dict mapping segment_index (str) to segment data dict with at least
        ``content`` and ``time`` fields.
    global_config : dict
        Global VideoRAG config dict (carries LLM functions, tokenizer, etc.).

    Returns
    -------
    list[dict]
        Each dict::
            {
                "event_id": "event-<hash>",
                "event_description": "...",
                "event_actors": "...",
                "event_type": "action|state_change|...",
                "video_name": str,
                "segment_index": str,
                "timestamp": str,   # "start-end" (seconds)
            }
    """
    use_llm_func: callable = global_config["llm"]["best_model_func"]
    event_extract_prompt = PROMPTS["event_extraction"]

    tuple_delimiter = PROMPTS["DEFAULT_TUPLE_DELIMITER"]
    record_delimiter = PROMPTS["DEFAULT_RECORD_DELIMITER"]
    completion_delimiter = PROMPTS["DEFAULT_COMPLETION_DELIMITER"]

    all_events: List[dict] = []

    segment_indices = sorted(segments_info.keys(), key=lambda x: int(x))

    async def _extract_one_segment(seg_idx: str) -> List[dict]:
        seg_data = segments_info[seg_idx]
        segment_content = seg_data.get("content", "")
        timestamp = seg_data.get("time", "")

        prompt = event_extract_prompt.format(segment_content=segment_content)
        result = await use_llm_func(prompt)

        # Parse the result
        records = split_string_by_multi_markers(
            result, [record_delimiter, completion_delimiter]
        )

        events: List[dict] = []
        for record in records:
            record = record.strip()
            if not record or record == completion_delimiter:
                continue
            # Extract tuple: ("event"<|>description<|>actors<|>type)
            import re
            match = re.search(r"\((.*)\)", record)
            if match is None:
                continue
            attrs = split_string_by_multi_markers(
                match.group(1), [tuple_delimiter]
            )
            if len(attrs) < 4 or attrs[0].strip('"') != "event":
                continue
            event_desc = clean_str(attrs[1].strip('"'))
            event_actors = clean_str(attrs[2].strip('"'))
            event_type = clean_str(attrs[3].strip('"'))

            if not event_desc:
                continue

            event_id = compute_mdhash_id(
                f"{video_name}_{seg_idx}_{event_desc}", prefix="evt-"
            )
            events.append({
                "event_id": event_id,
                "event_description": event_desc,
                "event_actors": event_actors,
                "event_type": event_type,
                "video_name": video_name,
                "segment_index": seg_idx,
                "timestamp": timestamp,
            })

        return events

    # Process segments concurrently (respecting LLM rate limit)
    results = await asyncio.gather(
        *[_extract_one_segment(idx) for idx in segment_indices]
    )

    for events in results:
        all_events.extend(events)

    logger.info(
        f"[Event Extraction] {video_name}: extracted {len(all_events)} events "
        f"from {len(segments_info)} segments"
    )
    return all_events


# ---------------------------------------------------------------------------
# Step 2: Causal Relation Extraction
# ---------------------------------------------------------------------------

async def extract_causal_relations(
    events: List[dict],
    global_config: dict,
    max_events_per_batch: int = MAX_EVENTS_PER_CAUSAL_BATCH,
    window_segments: int = CAUSAL_WINDOW_SEGMENTS,
) -> List[dict]:
    """Extract causal relations between events via LLM (batched).

    Events are batched by temporal proximity (segment index window) to keep
    LLM calls focused on plausible causal pairs.

    Parameters
    ----------
    events : list[dict]
        Event dicts as returned by :func:`extract_events_from_segments`.
    global_config : dict
        Global VideoRAG config.
    max_events_per_batch : int
        Max events per LLM call for causal-judgement.
    window_segments : int
        Temporal window in segment indices.  Events whose segment indices
        differ by more than this are not batched together.

    Returns
    -------
    list[dict]
        Each dict::
            {
                "source_event_id": str,
                "target_event_id": str,
                "relation_type": "causes"|"enables"|"prevents"|"results_in"|"precedes",
                "relation_description": str,
            }
    """
    if len(events) < 2:
        logger.info("[Causal Extraction] Fewer than 2 events, skipping causal extraction")
        return []

    use_llm_func: callable = global_config["llm"]["best_model_func"]
    causal_prompt = PROMPTS["causal_relation_extraction"]

    tuple_delimiter = PROMPTS["DEFAULT_TUPLE_DELIMITER"]
    record_delimiter = PROMPTS["DEFAULT_RECORD_DELIMITER"]
    completion_delimiter = PROMPTS["DEFAULT_COMPLETION_DELIMITER"]

    # Group events by video, then by temporal window
    video_events: Dict[str, List[dict]] = defaultdict(list)
    for evt in events:
        video_events[evt["video_name"]].append(evt)

    all_relations: List[dict] = []

    for video_name, v_events in video_events.items():
        # Sort by segment index
        v_events.sort(key=lambda e: int(e["segment_index"]))

        # Batch events within temporal windows
        batches = _batch_events_by_window(v_events, max_events_per_batch, window_segments)

        logger.info(
            f"[Causal Extraction] {video_name}: {len(v_events)} events → "
            f"{len(batches)} batches"
        )

        for batch_idx, batch in enumerate(batches):
            relations = await _extract_causal_from_batch(
                batch,
                causal_prompt,
                tuple_delimiter,
                record_delimiter,
                completion_delimiter,
                use_llm_func,
            )
            all_relations.extend(relations)

    logger.info(
        f"[Causal Extraction] Total: {len(all_relations)} causal relations extracted"
    )
    return all_relations


def _batch_events_by_window(
    events: List[dict],
    max_events_per_batch: int,
    window_segments: int,
) -> List[List[dict]]:
    """Batch events by temporal window for causal extraction."""
    batches: List[List[dict]] = []
    current_batch: List[dict] = []
    current_min_seg = None
    current_max_seg = None

    for evt in events:
        seg_idx = int(evt["segment_index"])

        if current_batch:
            # Check if adding this event would exceed batch size or window
            would_exceed_size = len(current_batch) >= max_events_per_batch
            would_exceed_window = (
                seg_idx - current_min_seg > window_segments
                and seg_idx - current_max_seg > window_segments
            )
            if would_exceed_size or would_exceed_window:
                batches.append(current_batch)
                current_batch = []
                current_min_seg = None
                current_max_seg = None

        current_batch.append(evt)
        if current_min_seg is None:
            current_min_seg = seg_idx
            current_max_seg = seg_idx
        else:
            current_min_seg = min(current_min_seg, seg_idx)
            current_max_seg = max(current_max_seg, seg_idx)

    if current_batch:
        batches.append(current_batch)

    return batches


async def _extract_causal_from_batch(
    batch: List[dict],
    causal_prompt: str,
    tuple_delimiter: str,
    record_delimiter: str,
    completion_delimiter: str,
    use_llm_func: callable,
) -> List[dict]:
    """Extract causal relations from a single batch of events."""
    # Build event list string for the prompt
    event_list_str = "\n".join(
        f"[{i}] \"{evt['event_description']}\""
        for i, evt in enumerate(batch)
    )

    prompt = causal_prompt.format(event_list=event_list_str)
    result = await use_llm_func(prompt)

    records = split_string_by_multi_markers(
        result, [record_delimiter, completion_delimiter]
    )

    relations: List[dict] = []
    for record in records:
        record = record.strip()
        if not record or record == completion_delimiter:
            continue
        import re
        match = re.search(r"\((.*)\)", record)
        if match is None:
            continue
        attrs = split_string_by_multi_markers(
            match.group(1), [tuple_delimiter]
        )
        if len(attrs) < 5 or attrs[0].strip('"') != "causal_relation":
            continue

        try:
            src_idx = int(attrs[1].strip('"'))
            tgt_idx = int(attrs[2].strip('"'))
        except (ValueError, IndexError):
            continue

        rel_type = clean_str(attrs[3].strip('"'))
        rel_desc = clean_str(attrs[4].strip('"'))

        if src_idx >= len(batch) or tgt_idx >= len(batch):
            continue
        if src_idx == tgt_idx:
            continue

        relations.append({
            "source_event_id": batch[src_idx]["event_id"],
            "target_event_id": batch[tgt_idx]["event_id"],
            "relation_type": rel_type,
            "relation_description": rel_desc,
        })

    return relations


# ---------------------------------------------------------------------------
# Step 3: Build Event-Causal Graph
# ---------------------------------------------------------------------------

def build_event_causal_graph(
    events: List[dict],
    causal_relations: List[dict],
    graph_storage: NetworkXStorage,
) -> NetworkXStorage:
    """Insert event nodes and causal edges into the graph storage.

    Parameters
    ----------
    events : list[dict]
        Event dicts from :func:`extract_events_from_segments`.
    causal_relations : list[dict]
        Causal relation dicts from :func:`extract_causal_relations`.
    graph_storage : NetworkXStorage
        The graph storage instance to populate.

    Returns
    -------
    NetworkXStorage
        The same graph storage instance (with data inserted).
    """
    # Insert event nodes
    for evt in events:
        graph_storage._graph.add_node(
            evt["event_id"],
            entity_type="EVENT",
            description=evt["event_description"],
            event_actors=evt["event_actors"],
            event_type=evt["event_type"],
            video_name=evt["video_name"],
            segment_index=evt["segment_index"],
            timestamp=evt["timestamp"],
            source_id=evt["segment_index"],
        )

    # Insert causal edges
    for rel in causal_relations:
        # Ensure both nodes exist
        if not graph_storage._graph.has_node(rel["source_event_id"]):
            graph_storage._graph.add_node(
                rel["source_event_id"],
                entity_type="EVENT",
                description=rel.get("relation_description", ""),
                source_id="",
            )
        if not graph_storage._graph.has_node(rel["target_event_id"]):
            graph_storage._graph.add_node(
                rel["target_event_id"],
                entity_type="EVENT",
                description=rel.get("relation_description", ""),
                source_id="",
            )

        graph_storage._graph.add_edge(
            rel["source_event_id"],
            rel["target_event_id"],
            weight=1.0,
            description=rel["relation_description"],
            relation_type=rel["relation_type"],
            source_id="causal_extraction",
            order=1,
        )

    logger.info(
        f"[Event-Causal Graph] Built: {len(events)} event nodes, "
        f"{len(causal_relations)} causal edges"
    )
    return graph_storage


# ---------------------------------------------------------------------------
# Step 4: Causal Chain Retrieval
# ---------------------------------------------------------------------------

async def _refine_causal_query(
    query: str,
    global_config: dict,
) -> str:
    """Rewrite query for causal event retrieval."""
    use_llm_func: callable = global_config["llm"]["cheap_model_func"]
    rewrite_prompt = PROMPTS["causal_chain_retrieval_query"]
    prompt = rewrite_prompt.format(input_text=query)
    result = await use_llm_func(prompt)
    return result


async def causal_chain_retrieval(
    query: str,
    event_vdb: NanoVectorDBStorage,
    event_causal_graph: NetworkXStorage,
    text_chunks_db,
    global_config: dict,
    top_k_events: int = 10,
    n_hops: int = DEFAULT_CAUSAL_HOPS,
) -> set:
    """Retrieve video segments via causal chain traversal.

    Steps:
    1. Rewrite query for causal retrieval.
    2. Match query against event vector DB to get seed events.
    3. From seed events, traverse N hops along causal edges (bidirectional).
    4. Collect all segments from traversed events.
    5. Return the set of segment IDs.

    Parameters
    ----------
    query : str
        User query.
    event_vdb : NanoVectorDBStorage
        Vector DB storing event embeddings.
    event_causal_graph : NetworkXStorage
        The event-causal knowledge graph.
    text_chunks_db : BaseKVStorage
        Text chunks DB (for mapping events back to segments).
    global_config : dict
        Global VideoRAG config.
    top_k_events : int
        Number of seed events to retrieve.
    n_hops : int
        Number of hops to traverse along causal edges.

    Returns
    -------
    set
        Set of segment IDs (str) retrieved via causal chains.
    """
    # Step 1: Rewrite query
    causal_query = await _refine_causal_query(query, global_config)
    logger.info(f"[Causal Retrieval] Rewritten query: {causal_query}")

    # Step 2: Retrieve seed events
    event_results = await event_vdb.query(causal_query, top_k=top_k_events)
    if not len(event_results):
        logger.info("[Causal Retrieval] No seed events found")
        return set()

    seed_event_ids = [r["id"] for r in event_results]
    logger.info(f"[Causal Retrieval] Seed events: {len(seed_event_ids)}")

    # Step 3: N-hop causal chain traversal
    all_event_ids = set(seed_event_ids)
    frontier = set(seed_event_ids)

    for hop in range(n_hops):
        next_frontier = set()
        for event_id in frontier:
            if not event_causal_graph._graph.has_node(event_id):
                continue
            # Outgoing edges (event → effect)
            for _, tgt in event_causal_graph._graph.out_edges(event_id):
                if tgt not in all_event_ids:
                    next_frontier.add(tgt)
                    all_event_ids.add(tgt)
            # Incoming edges (cause → event)
            for src, _ in event_causal_graph._graph.in_edges(event_id):
                if src not in all_event_ids:
                    next_frontier.add(src)
                    all_event_ids.add(src)
        frontier = next_frontier
        if not frontier:
            break

    logger.info(
        f"[Causal Retrieval] {len(all_event_ids)} events after {n_hops}-hop "
        f"traversal (from {len(seed_event_ids)} seeds)"
    )

    # Step 4: Map events to segments
    causal_segments = set()
    for event_id in all_event_ids:
        if not event_causal_graph._graph.has_node(event_id):
            continue
        node_data = event_causal_graph._graph.nodes[event_id]
        video_name = node_data.get("video_name", "")
        segment_index = node_data.get("segment_index", "")
        if video_name and segment_index:
            causal_segments.add(f"{video_name}_{segment_index}")

    logger.info(
        f"[Causal Retrieval] Retrieved {len(causal_segments)} segments "
        f"from {len(all_event_ids)} events"
    )
    return causal_segments


# ---------------------------------------------------------------------------
# Utility: build event embeddings for vector DB
# ---------------------------------------------------------------------------

async def embed_events_for_vdb(
    events: List[dict],
    event_vdb: NanoVectorDBStorage,
) -> None:
    """Embed event descriptions and upsert into the event vector DB.

    Each event is embedded as: event_description + " " + event_actors
    """
    if not events:
        return

    data_for_vdb = {}
    for evt in events:
        eid = evt["event_id"]
        content = f"{evt['event_description']} {evt['event_actors']}"
        data_for_vdb[eid] = {
            "content": content,
            "event_id": eid,
        }

    await event_vdb.upsert(data_for_vdb)
    logger.info(f"[Event VDB] Upserted {len(data_for_vdb)} event embeddings")