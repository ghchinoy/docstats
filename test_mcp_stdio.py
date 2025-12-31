import json
import subprocess
import select
import time
import sys

def test_mcp_stdio():
    print("Starting MCP server process...")
    process = subprocess.Popen(
        ["uv", "run", "python", "main.py", "--server-type", "mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    def read_line_with_timeout(stream, timeout=5):
        """Reads a line from the stream with a timeout."""
        rlist, _, _ = select.select([stream], [], [], timeout)
        if rlist:
            return stream.readline()
        else:
            return None

    try:
        # 1. Initialization
        print("Sending 'initialize' request...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"}
            }
        }
        process.stdin.write(json.dumps(init_request) + "\n")
        
        line = read_line_with_timeout(process.stdout)
        if line:
            print(f"Init Response: {line.strip()}")
        else:
            print("Timeout waiting for Init Response")
            return

        # MCP Protocol: Must send 'notifications/initialized' after receiving 'initialize' response
        print("Sending 'notifications/initialized' notification...")
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        process.stdin.write(json.dumps(initialized_notification) + "\n")

        # 2. List Tools
        print("Sending 'tools/list' request...")
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        process.stdin.write(json.dumps(list_tools_request) + "\n")
        
        line = read_line_with_timeout(process.stdout)
        if line:
            print(f"List Tools Response: {line.strip()}")
            assert "get_readability_scores" in line
        else:
            print("Timeout waiting for List Tools Response")
            return

        # 3. Call Tool
        print("Sending 'tools/call' request...")
        call_tool_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_readability_scores",
                "arguments": {"text": "This is a simple test sentence for readability."}
            }
        }
        process.stdin.write(json.dumps(call_tool_request) + "\n")
        
        line = read_line_with_timeout(process.stdout)
        if line:
            print(f"Call Tool Response: {line.strip()}")
            assert "flesch_reading_ease" in line
        else:
            print("Timeout waiting for Call Tool Response")
            return

        print("\nAll tests passed successfully!")

    except Exception as e:
        print(f"Test failed with error: {e}")
    finally:
        print("Terminating server process...")
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=2)
            if stderr:
                print(f"\nServer Stderr logs:\n{stderr}")
        except subprocess.TimeoutExpired:
            process.kill()
            print("Process killed after timeout.")

if __name__ == "__main__":
    test_mcp_stdio()