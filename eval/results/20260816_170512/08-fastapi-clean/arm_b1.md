# Dependencies in FastAPI

FastAPI includes a dependency injection system that lets you declare external requirements directly inside path operation functions. The framework resolves and supplies these dependencies before executing the endpoint.

### Understanding Dependency Injection

In software engineering, dependency injection separates the creation of a component from its usage. Your endpoint declares what it requires to run, and FastAPI instantiates and passes those objects at runtime.

Use dependency injection to:
- Share business logic across multiple routes
- Manage database sessions and connection pools
- Enforce authentication and role-based access control
- Reduce duplicate setup code across endpoints

### Basic Implementation

Declare dependencies as functions, then inject them into path operations using `Depends`:

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