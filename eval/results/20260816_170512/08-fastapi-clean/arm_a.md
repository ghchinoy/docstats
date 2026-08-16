# Dependencies in FastAPI

FastAPI features a powerful yet intuitive Dependency Injection system. It is designed to be simple to use and makes integrating external components with FastAPI seamless.

### What is "Dependency Injection"?

In programming, **Dependency Injection** is a design pattern where your code (such as your path operation functions) declares the external resources or logic it requires to function—its "dependencies."

The framework (in this case, FastAPI) automatically handles creating, resolving, and providing ("injecting") those dependencies into your functions at runtime.

This pattern is especially useful when you need to:
- Reuse shared business logic across multiple endpoints.
- Share database connections and sessions.
- Enforce security, authentication, and role-based permissions.
- Minimize code duplication across your application.

### First Steps

Here is a basic example illustrating how FastAPI's Dependency Injection system works:

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