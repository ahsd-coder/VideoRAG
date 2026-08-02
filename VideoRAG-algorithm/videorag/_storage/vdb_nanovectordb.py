import asyncio
import os
import torch
import multiprocessing
from dataclasses import dataclass
import numpy as np
from nano_vectordb import NanoVectorDB
from tqdm import tqdm
from imagebind.models import imagebind_model

from .._utils import logger
from ..base import BaseVectorStorage
from .._videoutil import encode_video_segments, encode_string_query
from .._videoutil.feature import _encode_worker


@dataclass
class NanoVectorDBStorage(BaseVectorStorage):
    cosine_better_than_threshold: float = 0.2
    
    def __post_init__(self):

        self._client_file_name = os.path.join(
            self.global_config["working_dir"], f"vdb_{self.namespace}.json"
        )
        self._max_batch_size = self.global_config["llm"]["embedding_batch_num"]
        self._client = NanoVectorDB(
            self.embedding_func.embedding_dim, storage_file=self._client_file_name
        )
        self.cosine_better_than_threshold = self.global_config.get(
            "query_better_than_threshold", self.cosine_better_than_threshold
        )

    async def upsert(self, data: dict[str, dict]):
        logger.info(f"Inserting {len(data)} vectors to {self.namespace}")
        if not len(data):
            logger.warning("You insert an empty data to vector DB")
            return []
        list_data = [
            {
                "__id__": k,
                **{k1: v1 for k1, v1 in v.items() if k1 in self.meta_fields},
            }
            for k, v in data.items()
        ]
        contents = [v["content"] for v in data.values()]
        batches = [
            contents[i : i + self._max_batch_size]
            for i in range(0, len(contents), self._max_batch_size)
        ]
        embeddings_list = await asyncio.gather(
            *[self.embedding_func(batch) for batch in batches]
        )
        embeddings = np.concatenate(embeddings_list)
        for i, d in enumerate(list_data):
            d["__vector__"] = embeddings[i]
        results = self._client.upsert(datas=list_data)
        return results

    async def query(self, query: str, top_k=5):
        embedding = await self.embedding_func([query])
        embedding = embedding[0]
        results = self._client.query(
            query=embedding,
            top_k=top_k,
            better_than_threshold=self.cosine_better_than_threshold,
        )
        results = [
            {**dp, "id": dp["__id__"], "distance": dp["__metrics__"]} for dp in results
        ]
        return results

    async def index_done_callback(self):
        self._client.save()


@dataclass
class NanoVectorDBVideoSegmentStorage(BaseVectorStorage):
    embedding_func = None
    segment_retrieval_top_k: float = 2

    def __post_init__(self):

        self._client_file_name = os.path.join(
            self.global_config["working_dir"], f"vdb_{self.namespace}.json"
        )
        self._max_batch_size = self.global_config["video_embedding_batch_num"]
        self._client = NanoVectorDB(
            self.global_config["video_embedding_dim"], storage_file=self._client_file_name
        )
        self.top_k = self.global_config.get(
            "segment_retrieval_top_k", self.segment_retrieval_top_k
        )
        # Initialize ImageBind model once for all queries (singleton pattern)
        self._query_embedder = None
    
    async def upsert(self, video_name, segment_index2name, video_output_format):
        logger.info(f"Inserting {len(segment_index2name)} segments to {self.namespace}")
        if not len(segment_index2name):
            logger.warning("You insert an empty data to vector DB")
            return []
        list_data, video_paths = [], []
        cache_path = os.path.join(self.global_config["working_dir"], '_cache', video_name)
        index_list = list(segment_index2name.keys())
        for index in index_list:
            list_data.append({
                "__id__": f"{video_name}_{index}",
                "__video_name__": video_name,
                "__index__": index,
            })
            segment_name = segment_index2name[index]
            video_file = os.path.join(cache_path, f"{segment_name}.{video_output_format}")
            video_paths.append(video_file)

        # GPU set for parallel encoding (same convention as caption).
        gpus_env = os.environ.get("VIDEORAG_CAPTION_GPUS", "").strip()
        if gpus_env:
            gpu_ids = [int(x) for x in gpus_env.split(",") if x.strip() != ""]
        else:
            n = torch.cuda.device_count()
            gpu_ids = list(range(n)) if n > 0 else [0]

        id_path_pairs = [(d["__id__"], p) for d, p in zip(list_data, video_paths)]

        # Multi-GPU: shard (id, path) round-robin, one worker per GPU. Each worker
        # is fault-tolerant (corrupt segments skipped) and returns {id: vector}.
        ctx = multiprocessing.get_context("spawn")
        mgr = ctx.Manager()
        return_dict = mgr.dict()
        if len(gpu_ids) <= 1:
            _encode_worker(gpu_ids[0], id_path_pairs, self._max_batch_size, return_dict)
        else:
            shards = [id_path_pairs[i::len(gpu_ids)] for i in range(len(gpu_ids))]
            procs = []
            for gpu_id, shard in zip(gpu_ids, shards):
                if not shard:
                    continue
                p = ctx.Process(target=_encode_worker,
                                args=(gpu_id, shard, self._max_batch_size, return_dict))
                p.start()
                procs.append(p)
            for p in procs:
                p.join()

        # Reassemble in original order; segments with no vector were corrupt → dropped.
        kept_data, kept_embeddings = [], []
        for d in list_data:
            vec = return_dict.get(d["__id__"])
            if vec is not None:
                kept_data.append(d)
                kept_embeddings.append(vec)
        dropped = len(list_data) - len(kept_data)
        if dropped:
            logger.warning(
                f"[VideoFeature] {video_name}: dropped {dropped} corrupt segment(s), "
                f"kept {len(kept_data)}"
            )
        if not kept_data:
            logger.warning(f"[VideoFeature] {video_name}: no segment encoded, skipping upsert")
            return []
        embeddings = np.stack(kept_embeddings, axis=0)
        for i, d in enumerate(kept_data):
            d["__vector__"] = embeddings[i]
        results = self._client.upsert(datas=kept_data)
        return results
    
    async def query(self, query: str):
        # Lazy load ImageBind model once on first query (singleton pattern)
        if self._query_embedder is None:
            logger.info("[ImageBind] Loading model for query (first time only)")
            self._query_embedder = imagebind_model.imagebind_huge(pretrained=True).cuda()
            self._query_embedder.eval()

        embedding = encode_string_query(query, self._query_embedder)
        embedding = embedding[0]
        results = self._client.query(
            query=embedding,
            top_k=self.top_k,
            better_than_threshold=-1,
        )
        results = [
            {**dp, "id": dp["__id__"], "distance": dp["__metrics__"]} for dp in results
        ]
        return results
    
    async def index_done_callback(self):
        self._client.save()
