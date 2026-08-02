import os
import torch
import pickle
from tqdm import tqdm
from imagebind import data
from imagebind.models import imagebind_model
from imagebind.models.imagebind_model import ImageBindModel, ModalityType


def encode_video_segments(video_paths, embedder: ImageBindModel):
    device = next(embedder.parameters()).device
    inputs = {
        ModalityType.VISION: data.load_and_transform_video_data(video_paths, device),
    }
    with torch.no_grad():
        embeddings = embedder(inputs)[ModalityType.VISION]
    embeddings = embeddings.cpu()
    return embeddings


def _encode_worker(gpu_id, id_path_pairs, batch_size, return_dict):
    """Encode a shard of (id, video_path) on one pinned GPU. Fault-tolerant.

    Runs as a spawned child. Sets CUDA_VISIBLE_DEVICES before any CUDA use so it
    only sees its GPU. Writes {seg_id: numpy_vector} into return_dict; corrupt
    segments are skipped (no vector) so one bad file never crashes the shard.
    """
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    import torch as _torch
    from imagebind.models import imagebind_model as _ibm
    embedder = _ibm.imagebind_huge(pretrained=True).cuda()
    embedder.eval()
    ids = [x[0] for x in id_path_pairs]
    paths = [x[1] for x in id_path_pairs]
    for start in tqdm(range(0, len(paths), batch_size),
                      desc=f"[GPU{gpu_id}] Encoding Segments"):
        b_ids = ids[start: start + batch_size]
        b_paths = paths[start: start + batch_size]
        try:
            emb = encode_video_segments(b_paths, embedder)
            for sid, e in zip(b_ids, emb):
                return_dict[sid] = e.numpy()
        except Exception:
            for sid, p in zip(b_ids, b_paths):
                try:
                    e = encode_video_segments([p], embedder)
                    return_dict[sid] = e[0].numpy()
                except Exception:
                    pass  # corrupt segment → skip (no visual vector)

def encode_string_query(query:str, embedder: ImageBindModel):
    device = next(embedder.parameters()).device
    inputs = {
        ModalityType.TEXT: data.load_and_transform_text([query], device),
    }
    with torch.no_grad():
        embeddings = embedder(inputs)[ModalityType.TEXT]
    embeddings = embeddings.cpu()
    return embeddings