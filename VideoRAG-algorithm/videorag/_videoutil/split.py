import os
import time
import shutil
import subprocess
import numpy as np
from tqdm import tqdm
from moviepy.video.io.VideoFileClip import VideoFileClip
from .._utils import logger


def _find_ffmpeg_tool(tool_name):
    """Find ffmpeg/ffprobe binary path."""
    # 1. Try imageio-ffmpeg (bundled with moviepy)
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        tool_path = os.path.join(ffmpeg_dir, tool_name)
        if os.path.isfile(tool_path):
            return tool_path
        # imageio-ffmpeg may only have ffmpeg, check if tool_name matches
        if tool_name == 'ffmpeg' and os.path.isfile(ffmpeg_exe):
            return ffmpeg_exe
    except Exception:
        pass

    # 2. Try system PATH
    path = shutil.which(tool_name)
    if path:
        return path

    # 3. Try common locations
    common_dirs = [
        os.path.expanduser('~/anaconda3/envs/videorag/bin'),
        os.path.expanduser('~/anaconda3/bin'),
        '/usr/bin', '/usr/local/bin',
    ]
    for d in common_dirs:
        tool_path = os.path.join(d, tool_name)
        if os.path.isfile(tool_path):
            return tool_path

    return None


def _get_video_duration(video_path):
    """Get video duration, trying ffprobe first, falling back to moviepy."""
    ffprobe = _find_ffmpeg_tool('ffprobe')
    if ffprobe:
        try:
            result = subprocess.run(
                [ffprobe, '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(float(result.stdout.strip()))
        except Exception:
            pass

    # Fallback to moviepy
    with VideoFileClip(video_path) as video:
        return int(video.duration)


def _extract_audio_segment(ffmpeg_path, video_path, output_path, start, duration, timeout=30):
    """Extract a single audio segment using ffmpeg."""
    subprocess.run([
        ffmpeg_path, '-y', '-loglevel', 'error',
        '-ss', str(start), '-i', video_path,
        '-t', str(duration), '-vn',
        '-acodec', 'libmp3lame', '-q:a', '5',
        output_path
    ], check=True, timeout=timeout)

def split_video(
    video_path,
    working_dir,
    segment_length,
    num_frames_per_segment,
    audio_output_format='mp3',
):
    unique_timestamp = str(int(time.time() * 1000))
    video_name = os.path.basename(video_path).split('.')[0]
    video_segment_cache_path = os.path.join(working_dir, '_cache', video_name)
    if os.path.exists(video_segment_cache_path):
        shutil.rmtree(video_segment_cache_path)
    os.makedirs(video_segment_cache_path, exist_ok=False)

    # Get video duration (ffprobe if available, moviepy fallback)
    total_video_length = _get_video_duration(video_path)

    start_times = list(range(0, total_video_length, segment_length))
    if len(start_times) > 1 and (total_video_length - start_times[-1]) < 5:
        start_times = start_times[:-1]

    segment_index2name, segment_times_info = {}, {}
    for seg_idx, start in enumerate(tqdm(start_times, desc=f"Spliting Video {video_name}")):
        end = total_video_length if start == start_times[-1] else start + segment_length
        subvideo_length = end - start
        frame_times = np.linspace(0, subvideo_length, num_frames_per_segment, endpoint=False)
        frame_times += start

        segment_index2name[f"{seg_idx}"] = f"{unique_timestamp}-{seg_idx}-{start}-{end}"
        segment_times_info[f"{seg_idx}"] = {"frame_times": frame_times, "timestamp": (start, end)}

    # Extract ALL audio segments in one ffmpeg pass (much faster than per-segment extraction)
    _extract_all_audio_segments(
        video_path, video_segment_cache_path, start_times,
        segment_index2name, audio_output_format, total_video_length,
        segment_length, video_name
    )

    return segment_index2name, segment_times_info


def _extract_all_audio_segments(
    video_path, cache_path, start_times, segment_index2name,
    audio_format, total_duration, segment_length, video_name
):
    """Extract audio for all segments. Uses ffmpeg if available, falls back to moviepy."""
    ffmpeg = _find_ffmpeg_tool('ffmpeg')
    ffprobe = _find_ffmpeg_tool('ffprobe')

    # Check audio track
    has_audio = True
    if ffprobe:
        try:
            probe = subprocess.run(
                [ffprobe, '-v', 'error', '-select_streams', 'a:0',
                 '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', video_path],
                capture_output=True, text=True, timeout=10
            )
            if not probe.stdout.strip():
                has_audio = False
        except Exception:
            pass

    if not has_audio:
        logger.warning(f"No audio track found in {video_name}, skipping audio extraction.")
        return

    if ffmpeg:
        # Fast path: ffmpeg per-segment extraction
        seg_count = len(start_times)
        for seg_idx in tqdm(range(seg_count), desc=f"Extracting Audio {video_name}"):
            start = start_times[seg_idx]
            seg_name = segment_index2name[f"{seg_idx}"]
            audio_file = os.path.join(cache_path, f"{seg_name}.{audio_format}")
            try:
                _extract_audio_segment(ffmpeg, video_path, audio_file, start, segment_length)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                logger.warning(f"Failed to extract audio segment {seg_idx} [{start}s]: {e}")
    else:
        # Fallback: moviepy (slow but reliable)
        logger.warning(f"ffmpeg not found, falling back to slow moviepy audio extraction.")
        with VideoFileClip(video_path) as video:
            for seg_idx in tqdm(range(len(start_times)), desc=f"Extracting Audio {video_name}"):
                start = start_times[seg_idx]
                end = total_duration if start == start_times[-1] else start + segment_length
                seg_name = segment_index2name[f"{seg_idx}"]
                audio_file = os.path.join(cache_path, f"{seg_name}.{audio_format}")
                try:
                    subclip = video.subclip(start, end)
                    if subclip.audio is not None:
                        subclip.audio.write_audiofile(audio_file, codec='mp3', verbose=False, logger=None)
                except Exception as e:
                    logger.warning(f"Failed to extract audio segment {seg_idx} [{start}s]: {e}")

def saving_video_segments(
    video_name,
    video_path,
    working_dir,
    segment_index2name,
    segment_times_info,
    error_queue,
    video_output_format='mp4',
):
    try:
        ffmpeg = _find_ffmpeg_tool('ffmpeg')
        video_segment_cache_path = os.path.join(working_dir, '_cache', video_name)

        if ffmpeg:
            # Fast path: ffmpeg stream copy (no re-encoding, near-instant)
            for index in tqdm(segment_index2name, desc=f"Cutting Video Segments {video_name}"):
                start, end = segment_times_info[index]["timestamp"][0], segment_times_info[index]["timestamp"][1]
                video_file = f'{segment_index2name[index]}.{video_output_format}'
                output_path = os.path.join(video_segment_cache_path, video_file)
                # -c copy copies streams without re-encoding; -ss after -i for accurate cuts
                subprocess.run([
                    ffmpeg, '-y', '-loglevel', 'error',
                    '-ss', str(start), '-i', video_path,
                    '-t', str(end - start), '-c', 'copy',
                    '-avoid_negative_ts', 'make_zero',
                    output_path
                ], check=True, timeout=60)
        else:
            # Slow fallback: moviepy re-encode
            with VideoFileClip(video_path) as video:
                video_fps = video.fps or 30.0
                for index in tqdm(segment_index2name, desc=f"Saving Video Segments {video_name}"):
                    start, end = segment_times_info[index]["timestamp"][0], segment_times_info[index]["timestamp"][1]
                    video_file = f'{segment_index2name[index]}.{video_output_format}'
                    subvideo = video.subclip(start, end)
                    if subvideo.fps is None:
                        subvideo.fps = video_fps
                    subvideo.write_videofile(
                        os.path.join(video_segment_cache_path, video_file),
                        codec='libx264', verbose=False, logger=None
                    )
    except Exception as e:
        error_queue.put(f"Error in saving_video_segments:\n {str(e)}")
        raise RuntimeError