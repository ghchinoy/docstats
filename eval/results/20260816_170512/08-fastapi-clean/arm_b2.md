# Dependencies in FastAPI

FastAPI includes a dependency injection system. Developers use it to integrate components into their applications.

### Dependency Injection

Dependency injection allows path operation functions to declare required resources. FastAPI resolves and provides these dependencies at runtime.

Dependencies minimize code duplication. You can use them to share database connections, enforce authentication roles, and extract repeated logic.

### Basic Example

This example demonstrates the core dependency injection mechanism.

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