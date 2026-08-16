import json
import select
import subprocess

import pytest


def test_mcp_stdio():
    """Verifies that the MCP server runs correctly over STDIO transport."""
    process = subprocess.Popen(
        ["uv", "run", "python", "main.py", "--server-type", "mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    def read_line_with_timeout(stream, timeout=5):
        """Reads a line from the stream with a timeout."""
        rlist, _, _ = select.select([stream], [], [], timeout)
        if rlist:
            return stream.readline()
        return None

    try:
        # 1. Initialization
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"},
            },
        }
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()

        line = read_line_with_timeout(process.stdout)
        if not line:
            pytest.fail("Timeout waiting for MCP initialize response")
        init_response = json.loads(line)
        assert "result" in init_response

        # MCP Protocol: Must send 'notifications/initialized'
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }
        process.stdin.write(json.dumps(initialized_notification) + "\n")
        process.stdin.flush()

        # 2. List Tools
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }
        process.stdin.write(json.dumps(list_tools_request) + "\n")
        process.stdin.flush()

        line = read_line_with_timeout(process.stdout)
        if not line:
            pytest.fail("Timeout waiting for tools/list response")
        assert "get_readability_scores" in line

        # 3. Call Tool
        call_tool_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_readability_scores",
                "arguments": {
                    "text": "This is a simple test sentence for readability."
                },
            },
        }
        process.stdin.write(json.dumps(call_tool_request) + "\n")
        process.stdin.flush()

        line = read_line_with_timeout(process.stdout)
        if not line:
            pytest.fail("Timeout waiting for tools/call response")
        assert "flesch_reading_ease" in line

    finally:
        process.terminate()
        try:
            process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    test_mcp_stdio()
