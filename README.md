# Docstats: Readability Metrics API and MCP Server

Docstats is a versatile Python application that calculates a comprehensive set of readability metrics for textual content. It can be run as a standard HTTP API (using FastAPI) or as an MCP (Model Context Protocol) server in two modes: STDIO or Streamable HTTP.

The application can process text from three types of sources:
1.  Direct text input.
2.  A publicly accessible web URL (HTML content will be parsed to extract main text).
3.  A Google Cloud Storage (GCS) URI pointing to a PDF file.

## Features

- Calculates numerous readability scores (Flesch Reading Ease, Flesch-Kincaid Grade, Gunning Fog, etc.).
- Provides basic text statistics: syllable count, word count, sentence count.
- Accepts input as direct text, web URL, or GCS PDF URI.
- HTML parsing for web URLs to extract relevant content using BeautifulSoup.
- PDF text extraction from GCS using PyPDF2 (Note: PyPDF2 is deprecated, consider migrating to `pypdf`).
- Multi-mode operation: FastAPI HTTP server, MCP STDIO server, or MCP Streamable HTTP server.

## Setup

1.  **Clone the repository (if applicable).**
2.  **Create and activate a virtual environment using `uv` (recommended):**
    ```bash
    python -m venv .venv # Or your preferred venv creation method
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
3.  **Install dependencies:**
    If you have `requirements.txt`:
    ```bash
    uv pip install -r requirements.txt
    ```
    If you only have `pyproject.toml` or want to ensure all dependencies from it are installed (recommended):
    ```bash
    uv pip install -e . # Installs the project in editable mode with its dependencies
    # or for just dependencies if not installing the project itself:
    # uv pip install . 
    ```
    Ensure your `pyproject.toml` lists all necessary dependencies like `fastapi`, `uvicorn[standard]`, `textstat`, `py-readability-metrics`, `google-cloud-storage`, `pypdf2`, `beautifulsoup4`, `mcp>=1.9.3`, `starlette`, `anyio`.

4.  **Google Cloud Authentication (for GCS PDF processing):**
    Ensure you have Application Default Credentials (ADC) configured in your environment. This typically involves running:
    ```bash
    gcloud auth application-default login
    ```
    Refer to [Google Cloud ADC documentation](https://cloud.google.com/docs/authentication/provide-credentials-adc) for more details.

## Running the Application

The `main.py` script uses command-line flags to determine how it starts.

### 1. As a FastAPI HTTP Server

This mode provides a traditional RESTful API. For development with auto-reload, it's best to run Uvicorn directly.

**Recommended Development Startup (with auto-reload):**
```bash
uv run uvicorn main:fastapi_app --host 127.0.0.1 --port 8000 --reload
```
- Adjust `--host` and `--port` as needed.
- API documentation (Swagger UI) will be available at `http://127.0.0.1:8000/docs`.

**Alternative Startup (using `python main.py`):**
```bash
uv run python main.py --server-type fastapi --host 127.0.0.1 --port 8000
```
- Note: Uvicorn's `--reload` feature works best when Uvicorn imports the app string (`main:fastapi_app`) directly.

**Example API Call (using cURL for a web URL):**
```bash
curl -X POST "http://127.0.0.1:8000/scores/" -H "Content-Type: application/json" -d '{ "web_url": "https://www.example.com" }'
```
**Example API Call (using cURL for direct text):**
```bash
curl -X POST "http://127.0.0.1:8000/scores/" -H "Content-Type: application/json" -d '{ "text": "This is a sample text for readability analysis." }'
```

### 2. As an MCP STDIO Server

This mode runs the MCP server communicating over standard input/output. This is useful for direct integration with other processes or MCP clients that use STDIO (e.g., an AI Agent CLI).

**Command using `python main.py`:**
```bash
uv run python main.py --server-type mcp
```
- This will start the `mcp_generic_app` instance defined in `main.py` using the STDIO transport.

**Using with an MCP Client (e.g., Gemini CLI / AI Agent):**
If you have an MCP client configured (like the Gemini CLI), you can define this server in its settings. For example, in a `.gemini/settings.json` (or similar client configuration file for your agent):
```json
{
    "mcpServers": {
        "readability_docstats": {
            "command": "uv",
            "args": ["run", "python", "main.py", "--server-type", "mcp"],
            "workingDirectory": "/Users/ghchinoy/dev/docstats"
        }
    }
}
```
Replace `/Users/ghchinoy/dev/docstats` with the correct absolute path to this project directory if your MCP client runs from a different context.
Once configured, you could invoke the tool via the client, e.g.:
`@readability_docstats get_readability_scores text="Some sample text."`

### 3. As an MCP Streamable HTTP Server

This mode runs the MCP server over HTTP.

**Command using `python main.py`:**
```bash
uv run python main.py --server-type mcp-http --host 127.0.0.1 --port 8001
```
- Adjust `--host` and `--port` as needed. A different port (e.g., 8001) is recommended to avoid conflict with the FastAPI server.
- The MCP endpoint will typically be available at `http://127.0.0.1:8001/mcp`.
- To get plain JSON responses instead of SSE streams (useful for some clients or debugging):
  ```bash
  uv run python main.py --server-type mcp-http --mcp-http-json-response --port 8001
  ```

## Development and Testing

- **Dependencies:** Manage Python dependencies using `uv` and `pyproject.toml`.
  To add a new dependency: `uv pip install <new_package>` (this should update `uv.lock`; you may need to manually add it to `pyproject.toml`'s dependencies section).
  To generate `requirements.txt` from `pyproject.toml` (if needed for other purposes):
  ```bash
  uv pip compile pyproject.toml -o requirements.txt
  ```
- **Testing:** The project includes a test suite using `pytest`.
  Run tests with:
  ```bash
  uv run pytest
  ```
  To run tests without those marked as `slow` (network-dependent):
  ```bash
  uv run pytest -m "not slow"
  ```

## Available Readability Scores

The API returns the following scores (where applicable):
- Flesch Reading Ease
- Flesch-Kincaid Grade Level
- Gunning Fog Index
- SMOG Index
- Automated Readability Index (ARI)
- Coleman-Liau Index
- Linsear Write Formula
- Dale-Chall Readability Score
- Spache Readability Score (Note: May return `null` if text doesn't meet specific criteria, e.g., word count)
- Text Standard (Consensus grade level)
- Syllable Count
- Word Count
- Sentence Count