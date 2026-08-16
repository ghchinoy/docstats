# Dependencies in FastAPI

FastAPI includes a built-in Dependency Injection system designed to integrate external components cleanly into path operation functions.

### What is Dependency Injection?

In software engineering, dependency injection allows your code to declare external components it requires to operate. The framework then resolves and delivers those dependencies at runtime.

This pattern helps you:
- Share business logic across multiple route handlers.
- Manage database sessions and connections.
- Enforce authentication, authorization, and role requirements.
- Minimize repetitive boilerplate code across endpoints.

### First Steps

Consider a minimal example where route handlers share common query parameters:

```python
from typing import Annotated

from fastapi import Depends, FastAPI

app = FastAPI()


async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}


@app.get("/items/")
async def read_items(commons: Annotated[dict, Depends(common_parameters)]):
    return commons
```