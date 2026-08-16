# Handling Infinite Pagination in Developer SDKs

SDKs that consume paginated API endpoints often burden client developers with manual cursor management. Tracking tokens, handling offsets, and writing loop boilerplate clutters application code and introduces subtle bugs.

To simplify integration, an SDK can expose asynchronous generators that abstract page boundaries. Instead of forcing consumers to manage page tokens directly, an `auto_paginate` iterator yields individual records across page boundaries on demand.

Under this pattern, an async iterator requests the next page only when the consumer exhausts the current batch. This lazy evaluation model keeps memory usage low while handling cursor state, batch sizes, and network retries behind the scenes.

```python
async for item in client.items.auto_paginate(query="active"):
    process(item)
```

Encapsulating cursor state inside the iterator provides a standard iteration interface and isolates client applications from API pagination details.