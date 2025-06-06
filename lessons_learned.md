# Lessons Learned: MCP Tool Handler `ctx` Argument

**Issue:** Clients reported a `TypeError: call_tool_generic() missing 1 required positional argument: 'ctx'` when interacting with the MCP server defined in `main.py`.

**Root Cause:**
The `call_tool_generic` and `call_tool_http` functions (decorated with `@mcp_generic_app.call_tool()` and `@mcp_http_app.call_tool()` respectively) in `main.py` were defined to accept `ctx` as a direct parameter in their function signatures:
```python
async def call_tool_generic(name: str, args_dict: dict, ctx: Any) -> ...:
    # ...
```
However, the `MCPLowLevelServer` framework (from the `mcp` library) does not pass the context object (`ctx`) as a direct argument to these handlers. Instead, it makes the context available via an attribute on the server instance itself (e.g., `app.request_context`).

This mismatch led to the `TypeError` because the framework called the handlers without the `ctx` argument they were expecting in their signatures.

**Solution:**
The handlers were modified to remove `ctx` from their function signatures. Inside the handlers, `ctx` is now accessed from the respective `MCPLowLevelServer` instance:

```python
@mcp_generic_app.call_tool()
async def call_tool_generic(name: str, args_dict: dict) -> list[mcp_sdk_types.TextContent]: 
    ctx = mcp_generic_app.request_context # Correct way to access context
    if name == "get_readability_scores": 
        return await execute_readability_tool(args_dict, ctx)
    # ...

@mcp_http_app.call_tool()
async def call_tool_http(name: str, args_dict: dict) -> list[mcp_sdk_types.TextContent]: 
    ctx = mcp_http_app.request_context # Correct way to access context
    if name == "get_readability_scores": 
        return await execute_readability_tool(args_dict, ctx)
    # ...
```
The `execute_readability_tool` function, which is called internally by these handlers, continues to receive `ctx` as an argument as it's passed explicitly by the modified handlers.

**Reference:** This solution aligns with the pattern observed in example MCP server implementations (e.g., `streamable_http/server.py`) where context is accessed via `app.request_context` within the tool call handler.
