import os
import torch
import numpy as np
from PIL import Image
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer
from moviepy.video.io.VideoFileClip import VideoFileClip

def encode_video(video, frame_times):
    frames = []
    for t in frame_times:
        frames.append(video.get_frame(t))
    frames = np.stack(frames, axis=0)
    frames = [Image.fromarray(v.astype('uint8')).resize((1280, 720)) for v in frames]
    return frames


def _compute_histogram_features(small_frames):
    """Compute RGB color histogram features for a list of small frames.

    Args:
        small_frames: list of numpy arrays (H, W, 3), uint8, already resized to small size.

    Returns:
        features: (N, 96) float32 array, 32 bins per RGB channel, L1-normalized.
    """
    features = []
    for frame in small_frames:
        hist_r = np.histogram(frame[:, :, 0].ravel(), bins=32, range=(0, 256))[0]
        hist_g = np.histogram(frame[:, :, 1].ravel(), bins=32, range=(0, 256))[0]
        hist_b = np.histogram(frame[:, :, 2].ravel(), bins=32, range=(0, 256))[0]
        hist = np.concatenate([hist_r, hist_g, hist_b]).astype(np.float32)
        hist = hist / (hist.sum() + 1e-8)
        features.append(hist)
    return np.stack(features, axis=0)


def _kmeans_plus_plus(features, k, max_iter=10, random_state=42):
    """K-Means++ clustering using pure numpy.

    Args:
        features: (N, D) float32 array.
        k: number of clusters.
        max_iter: maximum Lloyd iterations.
        random_state: seed for reproducibility.

    Returns:
        selected_indices: list of k indices, one per cluster (closest to centroid).
    """
    rng = np.random.RandomState(random_state)
    n_samples = features.shape[0]

    if n_samples <= k:
        return list(range(n_samples))

    # K-Means++ initialization
    centroids = [features[rng.randint(n_samples)]]
    for _ in range(1, k):
        dists = np.array([min(np.sum((f - c) ** 2) for c in centroids) for f in features])
        dists = np.maximum(dists, 0.0)  # ensure non-negative
        if dists.sum() == 0:
            # All points identical — pick randomly
            next_idx = rng.randint(n_samples)
        else:
            probs = dists / dists.sum()
            probs = probs / probs.sum()  # re-normalize to fix fp precision
            next_idx = rng.choice(n_samples, p=probs)
        centroids.append(features[next_idx])
    centroids = np.stack(centroids, axis=0)

    # Lloyd's algorithm
    labels = np.zeros(n_samples, dtype=np.int32)
    for _ in range(max_iter):
        distances = np.zeros((n_samples, k))
        for i in range(k):
            distances[:, i] = np.sum((features - centroids[i]) ** 2, axis=1)
        new_labels = np.argmin(distances, axis=1)
        if np.array_equal(labels, new_labels):
            break
        labels = new_labels
        for i in range(k):
            mask = (labels == i)
            if mask.sum() > 0:
                centroids[i] = features[mask].mean(axis=0)

    # For each cluster, select the frame closest to its centroid
    selected_indices = []
    for i in range(k):
        mask = (labels == i)
        if mask.sum() > 0:
            cluster_dists = np.sum((features[mask] - centroids[i]) ** 2, axis=1)
            cluster_indices = np.where(mask)[0]
            best_idx = cluster_indices[np.argmin(cluster_dists)]
        else:
            best_idx = rng.randint(n_samples)
        selected_indices.append(int(best_idx))

    return sorted(selected_indices)


def adaptive_frame_selection(video, start, end, k=5):
    """Select k visually diverse frames using K-Means++ on color histograms.

    Densely samples frames at 1fps within [start, end], computes RGB histogram
    features, clusters them into k groups, and returns the frame times closest
    to each cluster centroid.

    Args:
        video: MoviePy VideoFileClip object.
        start, end: global timestamps in seconds (int).
        k: number of frames to select.

    Returns:
        selected_times: numpy array of k global frame timestamps.
    """
    duration = end - start
    n_dense = max(k, int(duration))

    # Fallback: if segment is very short, use uniform sampling
    if n_dense <= k:
        return np.linspace(start, end, k, endpoint=False)

    dense_times = np.linspace(start, end, n_dense, endpoint=False)

    # Extract frames at low resolution (112x112) for fast feature computation
    small_frames = []
    for t in dense_times:
        frame = video.get_frame(t)
        small = np.array(Image.fromarray(frame.astype('uint8')).resize((112, 112)))
        small_frames.append(small)

    # Compute features and cluster
    features = _compute_histogram_features(small_frames)
    selected_indices = _kmeans_plus_plus(features, k)

    return dense_times[selected_indices]


def segment_caption(video_name, video_path, segment_index2name, transcripts, segment_times_info, caption_result, error_queue):
    try:
        model = AutoModel.from_pretrained('./MiniCPM-V-2_6-int4', trust_remote_code=True)
        tokenizer = AutoTokenizer.from_pretrained('./MiniCPM-V-2_6-int4', trust_remote_code=True)
        model.eval()

        with VideoFileClip(video_path) as video:
            for index in tqdm(segment_index2name, desc=f"Captioning Video {video_name}"):
                # Adaptive frame selection: K-Means++ on color histograms
                # instead of uniform np.linspace
                start, end = segment_times_info[index]["timestamp"]
                frame_times = adaptive_frame_selection(video, int(start), int(end), k=5)
                video_frames = encode_video(video, frame_times)
                segment_transcript = transcripts[index]
                query = f"The transcript of the current video:\n{segment_transcript}.\nNow provide a description (caption) of the video in English."
                msgs = [{'role': 'user', 'content': video_frames + [query]}]
                params = {}
                params["use_image_id"] = False
                params["max_slice_nums"] = 2
                segment_caption = model.chat(
                    image=None,
                    msgs=msgs,
                    tokenizer=tokenizer,
                    **params
                )
                caption_result[index] = segment_caption.replace("\n", "").replace("<|endoftext|>", "")
                torch.cuda.empty_cache()
    except Exception as e:
        error_queue.put(f"Error in segment_caption:\n {str(e)}")
        raise RuntimeError

def merge_segment_information(segment_index2name, segment_times_info, transcripts, captions):
    inserting_segments = {}
    for index in segment_index2name:
        inserting_segments[index] = {"content": None, "time": None}
        segment_name = segment_index2name[index]
        inserting_segments[index]["time"] = '-'.join(segment_name.split('-')[-2:])
        inserting_segments[index]["content"] = f"Caption:\n{captions[index]}\nTranscript:\n{transcripts[index]}\n\n"
        inserting_segments[index]["transcript"] = transcripts[index]
        inserting_segments[index]["frame_times"] = segment_times_info[index]["frame_times"].tolist()
    return inserting_segments
        
def retrieved_segment_caption(caption_model, caption_tokenizer, refine_knowledge, retrieved_segments, video_path_db, video_segments, num_sampled_frames):
    # model = AutoModel.from_pretrained('./MiniCPM-V-2_6-int4', trust_remote_code=True)
    # tokenizer = AutoTokenizer.from_pretrained('./MiniCPM-V-2_6-int4', trust_remote_code=True)
    # model.eval()
    
    caption_result = {}
    for this_segment in tqdm(retrieved_segments, desc='Captioning Segments for Given Query'):
        video_name = '_'.join(this_segment.split('_')[:-1])
        index = this_segment.split('_')[-1]
        video_path = video_path_db._data[video_name]
        timestamp = video_segments._data[video_name][index]["time"].split('-')
        start, end = eval(timestamp[0]), eval(timestamp[1])
        with VideoFileClip(video_path) as video:
            # Adaptive frame selection: K-Means++ on color histograms
            # instead of uniform np.linspace (consistent with indexing phase)
            frame_times = adaptive_frame_selection(video, int(start), int(end), k=num_sampled_frames)
            video_frames = encode_video(video, frame_times)
        segment_transcript = video_segments._data[video_name][index]["transcript"]
        # query = f"The transcript of the current video:\n{segment_transcript}.\nGiven a question: {query}, you have to extract relevant information from the video and transcript for answering the question."
        query = f"The transcript of the current video:\n{segment_transcript}.\nNow provide a very detailed description (caption) of the video in English and extract relevant information about: {refine_knowledge}'"
        msgs = [{'role': 'user', 'content': video_frames + [query]}]
        params = {}
        params["use_image_id"] = False
        params["max_slice_nums"] = 2
        segment_caption = caption_model.chat(
            image=None,
            msgs=msgs,
            tokenizer=caption_tokenizer,
            **params
        )
        this_caption = segment_caption.replace("\n", "").replace("<|endoftext|>", "")
        caption_result[this_segment] = f"Caption:\n{this_caption}\nTranscript:\n{segment_transcript}\n\n"
        torch.cuda.empty_cache()
    
    return caption_result