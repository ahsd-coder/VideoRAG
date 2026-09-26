Collection: 10
QID: 5
Mode: causal_only
Question: Which specific feature of Trade Nation provides a significant advantage?

[ERROR] RetryError[<Future at 0x7812737b8fd0 state=finished raised APIConnectionError>]
Traceback (most recent call last):
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/httpx/_transports/default.py", line 101, in map_httpcore_exceptions
    yield
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/httpx/_transports/default.py", line 394, in handle_async_request
    resp = await self._pool.handle_async_request(req)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/httpcore/_async/connection_pool.py", line 256, in handle_async_request
    raise exc from None
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/httpcore/_async/connection_pool.py", line 236, in handle_async_request
    response = await connection.handle_async_request(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/httpcore/_async/connection.py", line 101, in handle_async_request
    raise exc
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/httpcore/_async/connection.py", line 78, in handle_async_request
    stream = await self._connect(request)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/httpcore/_async/connection.py", line 124, in _connect
    stream = await self._network_backend.connect_tcp(**kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/httpcore/_backends/auto.py", line 31, in connect_tcp
    return await self._backend.connect_tcp(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/httpcore/_backends/anyio.py", line 113, in connect_tcp
    with map_exceptions(exc_map):
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/contextlib.py", line 158, in __exit__
    self.gen.throw(typ, value, traceback)
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/httpcore/_exceptions.py", line 14, in map_exceptions
    raise to_exc(exc) from exc
httpcore.ConnectError: All connection attempts failed

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/openai/_base_client.py", line 1648, in request
    response = await self._send_request(
               ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/openai/_client.py", line 946, in _send_request
    return await self._send_with_auth_retry(request, stream=stream, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/openai/_client.py", line 924, in _send_with_auth_retry
    response = await super()._send_request(request, stream=stream, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/openai/_base_client.py", line 1571, in _send_request
    return await self._client.send(request, stream=stream, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/httpx/_client.py", line 1629, in send
    response = await self._send_handling_auth(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/httpx/_client.py", line 1657, in _send_handling_auth
    response = await self._send_handling_redirects(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/httpx/_client.py", line 1694, in _send_handling_redirects
    response = await self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/httpx/_client.py", line 1730, in _send_single_request
    response = await transport.handle_async_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/httpx/_transports/default.py", line 393, in handle_async_request
    with map_httpcore_exceptions():
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/contextlib.py", line 158, in __exit__
    self.gen.throw(typ, value, traceback)
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/httpx/_transports/default.py", line 118, in map_httpcore_exceptions
    raise mapped_exc(message) from exc
httpx.ConnectError: All connection attempts failed

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/tenacity/asyncio/__init__.py", line 116, in __call__
    result = await fn(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/VideoRAG-main/VideoRAG-algorithm/videorag/_llm.py", line 493, in vllm_embedding
    response = await client.embeddings.create(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/openai/resources/embeddings.py", line 260, in create
    return await self._post(
           ^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/openai/_base_client.py", line 1931, in post
    return await self.request(cast_to, opts, stream=stream, stream_cls=stream_cls)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/openai/_base_client.py", line 1683, in request
    raise APIConnectionError(request=request) from err
openai.APIConnectionError: Connection error.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/gjw/VideoRAG-main/VideoRAG-algorithm/run_benchmark.py", line 101, in query_collection
    ans = videorag.query(query=question, param=param)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/VideoRAG-main/VideoRAG-algorithm/videorag/videorag.py", line 336, in query
    return loop.run_until_complete(self.aquery(query, param))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/asyncio/base_events.py", line 654, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/home/gjw/VideoRAG-main/VideoRAG-algorithm/videorag/videorag.py", line 340, in aquery
    response = await videorag_query(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/VideoRAG-main/VideoRAG-algorithm/videorag/_op.py", line 603, in videorag_query
    results = await chunks_vdb.query(query, top_k=query_param.top_k)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/VideoRAG-main/VideoRAG-algorithm/videorag/_storage/vdb_nanovectordb.py", line 61, in query
    embedding = await self.embedding_func([query])
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/VideoRAG-main/VideoRAG-algorithm/videorag/_utils.py", line 193, in wait_func
    result = await func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/VideoRAG-main/VideoRAG-algorithm/videorag/_utils.py", line 176, in __call__
    return await self.func(**kwargs)
    ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/VideoRAG-main/VideoRAG-algorithm/videorag/_utils.py", line 176, in __call__
    return await self.func(**kwargs)
    ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/tenacity/asyncio/__init__.py", line 193, in async_wrapped
    return await copy(fn, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/tenacity/asyncio/__init__.py", line 112, in __call__
    do = await self.iter(retry_state=retry_state)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/tenacity/asyncio/__init__.py", line 157, in iter
    result = await action(retry_state)
             ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/tenacity/_utils.py", line 111, in inner
    return call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/gjw/anaconda3/envs/videorag/lib/python3.11/site-packages/tenacity/__init__.py", line 414, in exc_check
    raise retry_exc from fut.exception()
tenacity.RetryError: RetryError[<Future at 0x7812737b8fd0 state=finished raised APIConnectionError>]

