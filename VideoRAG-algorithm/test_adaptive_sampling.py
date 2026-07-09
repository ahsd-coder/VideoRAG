"""
Test script for adaptive frame selection vs uniform sampling.

Two test modes:
  1. Visual check:  Save side-by-side frame grids for manual inspection.
  2. Full pipeline:  Process the same video with both methods, compare KG stats.

Usage:
  python test_adaptive_sampling.py --video_path YOUR_VIDEO.mp4 --mode visual
  python test_adaptive_sampling.py --video_path YOUR_VIDEO.mp4 --mode full
"""

import os
import sys
import json
import argparse
import shutil
import numpy as np
from PIL import Image
from moviepy.video.io.VideoFileClip import VideoFileClip

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from videorag._videoutil.caption import (
    adaptive_frame_selection,
    _compute_histogram_features,
    _kmeans_plus_plus,
)


def test_visual(video_path, segment_length=30, num_frames=5, output_dir="./test_frames", max_duration=None):
    """Visual comparison: save uniform vs adaptive frames as images."""
    os.makedirs(output_dir, exist_ok=True)

    with VideoFileClip(video_path) as video:
        total_duration = int(video.duration)
        if max_duration is not None:
            total_duration = min(total_duration, max_duration)
            print(f"Limiting to first {total_duration}s ({total_duration//60}min)")
        # Generate ALL segments (same logic as split_video)
        start_times = list(range(0, total_duration, segment_length))
        if len(start_times) > 1 and (total_duration - start_times[-1]) < 5:
            start_times = start_times[:-1]
        segments = []
        for start in start_times:
            end = min(start + segment_length, total_duration) if start != start_times[-1] else total_duration
            segments.append((start, end))

        for seg_idx, (start, end) in enumerate(segments):
            print(f"\n{'='*60}")
            print(f"Segment {seg_idx}: [{start}s – {end}s]  (duration: {end-start}s)")
            print(f"{'='*60}")

            # --- Uniform sampling ---
            uniform_times = np.linspace(start, end, num_frames, endpoint=False)
            uniform_frames = []
            for t in uniform_times:
                frame = video.get_frame(t)
                uniform_frames.append(
                    Image.fromarray(frame.astype("uint8")).resize((320, 180))
                )

            # --- Adaptive sampling ---
            adaptive_times = adaptive_frame_selection(video, start, end, k=num_frames)
            adaptive_frames = []
            for t in adaptive_times:
                frame = video.get_frame(t)
                adaptive_frames.append(
                    Image.fromarray(frame.astype("uint8")).resize((320, 180))
                )

            # --- Print comparison ---
            print(f"\nUniform times:  {[f'{t-start:.1f}s' for t in uniform_times]}")
            print(f"Adaptive times: {[f'{t-start:.1f}s' for t in adaptive_times]}")

            # --- Save side-by-side grid ---
            grid_top = np.hstack([np.array(f) for f in uniform_frames])
            grid_bottom = np.hstack([np.array(f) for f in adaptive_frames])

            # Add labels
            from PIL import ImageDraw, ImageFont
            label_h = 30
            grid_h, grid_w = grid_top.shape[0], grid_top.shape[1]

            canvas = np.ones((label_h * 2 + grid_h * 2 + 10, grid_w, 3), dtype=np.uint8) * 255
            canvas_pil = Image.fromarray(canvas)
            draw = ImageDraw.Draw(canvas_pil)
            draw.text((5, 5), "Uniform (np.linspace)", fill=(0, 0, 0))
            draw.text((5, label_h + grid_h + 5), "Adaptive (K-Means++)", fill=(0, 0, 0))

            canvas = np.array(canvas_pil)
            canvas[label_h : label_h + grid_h, :] = grid_top
            canvas[label_h * 2 + grid_h + 10 : label_h * 2 + grid_h * 2 + 10, :] = grid_bottom

            out_path = os.path.join(output_dir, f"comparison_seg{seg_idx}_{start}_{end}.png")
            Image.fromarray(canvas).save(out_path)
            print(f"\nSaved: {out_path}")
            print(f"→ Open this image to visually compare frame diversity.")


def test_full_pipeline(video_path, working_dir_old, working_dir_new):
    """
    Full pipeline comparison.
    Requires: MiniCPM-V-2_6 model at ./MiniCPM-V-2_6-int4
              faster-whisper model at ./faster-distil-whisper-large-v3
              ImageBind model (auto-downloaded)
              OpenAI-compatible API for LLM

    NOTE: This test patches caption.py at runtime to switch between
    uniform and adaptive sampling. It does NOT modify the source file.
    """
    import multiprocessing
    multiprocessing.set_start_method("spawn", force=True)

    # ============================================================
    # Test OLD method: uniform sampling
    # ============================================================
    print("\n" + "=" * 70)
    print("PHASE 1: Processing with UNIFORM sampling (np.linspace)")
    print("=" * 70)

    # Monkey-patch to use uniform sampling
    import videorag._videoutil.caption as caption_module
    original_segment_caption = caption_module.segment_caption

    def uniform_segment_caption(*args, **kwargs):
        """Temporarily replace adaptive with uniform inside segment_caption."""
        # We monkey-patch adaptive_frame_selection to return uniform times
        original_adaptive = caption_module.adaptive_frame_selection

        def uniform_selection(video, start, end, k=5):
            return np.linspace(start, end, k, endpoint=False)

        caption_module.adaptive_frame_selection = uniform_selection
        try:
            return original_segment_caption(*args, **kwargs)
        finally:
            caption_module.adaptive_frame_selection = original_adaptive

    caption_module.segment_caption = uniform_segment_caption

    try:
        from videorag import VideoRAG, QueryParam
        from videorag._llm import openai_config

        # Clean old dir
        if os.path.exists(working_dir_old):
            shutil.rmtree(working_dir_old)

        videorag_old = VideoRAG(llm=openai_config, working_dir=working_dir_old)
        videorag_old.insert_video(video_path_list=[video_path])

        # Collect stats
        stats_old = _collect_kg_stats(videorag_old, working_dir_old)
    finally:
        caption_module.segment_caption = original_segment_caption

    # ============================================================
    # Test NEW method: adaptive sampling
    # ============================================================
    print("\n" + "=" * 70)
    print("PHASE 2: Processing with ADAPTIVE sampling (K-Means++)")
    print("=" * 70)

    if os.path.exists(working_dir_new):
        shutil.rmtree(working_dir_new)

    videorag_new = VideoRAG(llm=openai_config, working_dir=working_dir_new)
    videorag_new.insert_video(video_path_list=[video_path])

    stats_new = _collect_kg_stats(videorag_new, working_dir_new)

    # ============================================================
    # Comparison Report
    # ============================================================
    print("\n" + "=" * 70)
    print("COMPARISON REPORT")
    print("=" * 70)

    _print_comparison(stats_old, stats_new)


def _collect_kg_stats(videorag_instance, working_dir):
    """Collect KG and caption statistics from a processed VideoRAG instance."""
    stats = {
        "num_videos": len(videorag_instance.video_segments._data),
        "num_segments": 0,
        "num_chunks": len(videorag_instance.text_chunks._data),
        "num_entities": 0,
        "num_relations": 0,
        "entity_types": {},
        "avg_caption_length": 0,
        "avg_transcript_length": 0,
        "segment_details": [],
    }

    # Count segments
    for video_name, segments in videorag_instance.video_segments._data.items():
        stats["num_segments"] += len(segments)
        for seg_idx, seg_data in segments.items():
            content = seg_data.get("content", "")
            transcript = seg_data.get("transcript", "")
            caption = content.split("Transcript:")[0].replace("Caption:\n", "").strip()
            stats["avg_caption_length"] += len(caption.split())
            stats["avg_transcript_length"] += len(transcript.split())
            stats["segment_details"].append({
                "video": video_name,
                "index": seg_idx,
                "caption_words": len(caption.split()),
                "transcript_words": len(transcript.split()),
            })

    if stats["num_segments"] > 0:
        stats["avg_caption_length"] /= stats["num_segments"]
        stats["avg_transcript_length"] /= stats["num_segments"]

    # Count entities and relations from KG
    graph = videorag_instance.chunk_entity_relation_graph._graph
    for node_id, node_data in graph.nodes(data=True):
        stats["num_entities"] += 1
        etype = node_data.get("entity_type", "UNKNOWN")
        stats["entity_types"][etype] = stats["entity_types"].get(etype, 0) + 1

    stats["num_relations"] = graph.number_of_edges()

    # Save detailed dump
    dump_path = os.path.join(working_dir, "kg_stats.json")
    with open(dump_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False, default=str)
    print(f"Stats saved to: {dump_path}")

    return stats


def _print_comparison(stats_old, stats_new):
    """Print side-by-side comparison."""
    def delta_str(old, new):
        if old == 0:
            return "N/A"
        delta = (new - old) / old * 100
        sign = "+" if delta >= 0 else ""
        return f"{sign}{delta:.1f}%"

    rows = [
        ("Metric", "Uniform", "Adaptive", "Change"),
        ("─" * 40, "─" * 12, "─" * 12, "─" * 10),
        ("Videos", stats_old["num_videos"], stats_new["num_videos"], ""),
        ("Segments", stats_old["num_segments"], stats_new["num_segments"], ""),
        ("Chunks", stats_old["num_chunks"], stats_new["num_chunks"],
         delta_str(stats_old["num_chunks"], stats_new["num_chunks"])),
        ("Entities", stats_old["num_entities"], stats_new["num_entities"],
         delta_str(stats_old["num_entities"], stats_new["num_entities"])),
        ("Relations", stats_old["num_relations"], stats_new["num_relations"],
         delta_str(stats_old["num_relations"], stats_new["num_relations"])),
        ("Avg Caption Words", f'{stats_old["avg_caption_length"]:.1f}',
         f'{stats_new["avg_caption_length"]:.1f}',
         delta_str(stats_old["avg_caption_length"], stats_new["avg_caption_length"])),
        ("Avg Transcript Words", f'{stats_old["avg_transcript_length"]:.1f}',
         f'{stats_new["avg_transcript_length"]:.1f}', ""),
        ("", "", "", ""),
        ("Entity Type Distribution:", "", "", ""),
    ]

    for row in rows:
        if len(row) == 4:
            print(f"  {row[0]:<40} {row[1]:<12} {row[2]:<12} {row[3]:<10}")
        else:
            print(row)

    # Entity type comparison
    all_types = set(stats_old["entity_types"].keys()) | set(stats_new["entity_types"].keys())
    for etype in sorted(all_types):
        old_count = stats_old["entity_types"].get(etype, 0)
        new_count = stats_new["entity_types"].get(etype, 0)
        print(f"  {etype:<40} {old_count:<12} {new_count:<12} {delta_str(old_count, new_count):<10}")

    # Key verdict
    print(f"\n{'='*60}")
    print("KEY VERDICT:")
    checks = []
    checks.append(("More entities?", stats_new["num_entities"] > stats_old["num_entities"]))
    checks.append(("More relations?", stats_new["num_relations"] > stats_old["num_relations"]))
    checks.append(("Richer captions?", stats_new["avg_caption_length"] > stats_old["avg_caption_length"]))
    for question, passed in checks:
        status = "✅ YES" if passed else "❌ NO"
        print(f"  {question:<25} {status}")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test adaptive frame selection")
    parser.add_argument("--video_path", type=str, required=True,
                        help="Path to a test video file (.mp4)")
    parser.add_argument("--mode", type=str, default="visual",
                        choices=["visual", "full"],
                        help="visual: save frame grids; full: run complete pipeline comparison")
    parser.add_argument("--segment_length", type=int, default=60,
                        help="Segment length in seconds (default: 60)")
    parser.add_argument("--num_frames", type=int, default=10,
                        help="Number of frames per segment (default: 10)")
    parser.add_argument("--output_dir", type=str, default="./test_frames",
                        help="Output directory for frame grids (visual mode)")
    parser.add_argument("--max_duration", type=int, default=None,
                        help="Only process first N seconds of video (e.g. 1800 for 30min)")
    parser.add_argument("--workdir_old", type=str, default="./test_workdir_uniform",
                        help="Working directory for uniform method (full mode)")
    parser.add_argument("--workdir_new", type=str, default="./test_workdir_adaptive",
                        help="Working directory for adaptive method (full mode)")
    args = parser.parse_args()

    if not os.path.exists(args.video_path):
        print(f"ERROR: Video not found: {args.video_path}")
        sys.exit(1)

    if args.mode == "visual":
        print("Running VISUAL comparison...")
        print(f"Video: {args.video_path}")
        print(f"Output: {args.output_dir}")
        test_visual(args.video_path, args.segment_length, args.num_frames, args.output_dir, args.max_duration)

    elif args.mode == "full":
        print("Running FULL pipeline comparison...")
        print(f"Video: {args.video_path}")
        print(f"Old (uniform) workdir: {args.workdir_old}")
        print(f"New (adaptive) workdir: {args.workdir_new}")
        print("\n⚠️  This requires: MiniCPM-V-2_6, Whisper, ImageBind, and LLM API.")
        print("   Make sure models are available before running.\n")
        test_full_pipeline(args.video_path, args.workdir_old, args.workdir_new)
