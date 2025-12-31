# Docstats: Readability Metrics API and MCP Server

Docstats is a versatile Python application that calculates a comprehensive set of readability metrics for textual content. It can be run as a standard HTTP API (using FastAPI) or as an MCP (Model Context Protocol) server in two modes: STDIO or Streamable HTTP.

The application can process text from three types of sources:
1.  Direct text input.
2.  A publicly accessible web URL (supports both HTML content and PDF files).
3.  A Google Cloud Storage (GCS) URI pointing to a PDF file.

## Features

- Calculates numerous readability scores (Flesch Reading Ease, Flesch-Kincaid Grade, Gunning Fog, etc.).
- Provides basic text statistics: syllable count, word count, sentence count.
- Accepts input as direct text, web URL (HTML/PDF), or GCS PDF URI.
- HTML parsing for web URLs to extract relevant content using BeautifulSoup.
- PDF text extraction from web URLs and GCS using `pypdf`.
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

This mode provides a traditional RESTful API. For development with auto-reload, it's best to run Uvicorn directly pointing to the `fastapi_app` module.

**Recommended Development Startup (with auto-reload):**
```bash
uv run uvicorn fastapi_app:fastapi_app --host 127.0.0.1 --port 8000 --reload
```
- Adjust `--host` and `--port` as needed.
- API documentation (Swagger UI) will be available at `http://127.0.0.1:8000/docs`.

**Alternative Startup (using the `main.py` entry point):**
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

**Using with an MCP Client (e.g., AI Application / Gemini CLI / Claude):**
If you have an MCP client configured (like Gemini CLI or Claude Code), you can define this server in its settings. 

For example, in a `~/.claude/settings.json` or `~/.gemini/settings.json` (or similar client configuration file for your agent):
```json
{
  "mcpServers": {
    "readability_docstats": {
      "command": "uv",
      "args": ["run", "python", "/PATH/TO/DOCSTATS/main.py", "--server-type", "mcp"],
      "cwd": "/PATH/TO/DOCSTATS"
    }
  }
}
```

Replace `/PATH/TO/docstats` with the correct absolute path to this project directory if your MCP client runs from a different context.
Once configured, you could invoke the tool via the client, e.g.:
`@readability_docstats get_readability_scores text="Some sample text."`


[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/install-mcp?name=readability_docstats&config=eyJjb21tYW5kIjoidXYgcnVuIC9QQVRIL1RPL1JFUE8vZG9jc3RhdHMvLnZlbnYvYmluL3B5dGhvbiAvUEFUSC9UTy9SRVBPL2RvY3N0YXRzL21haW4ucHkgLS1zZXJ2ZXItdHlwZSBtY3AiLCJ3b3JraW5nRGlyZWN0b3J5IjoiL1BBVEgvVE8vUkVQTy9kZXYvZG9jc3RhdHMifQ%3D%3D)



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

### Testing
The project includes a comprehensive test suite using `pytest`. 

#### Test Types
1. **Unit Tests (`test_unit.py`):** Uses mocks for `httpx`, `google-cloud-storage`, and `pypdf`. These are fast and do not require internet or cloud credentials. They cover core extraction logic and MCP tool execution.
2. **Integration Tests (`test_main.py`):** Uses FastAPI's `TestClient` to verify end-to-end flow. Some tests are marked as `slow` because they require network access to fetch live web pages and GCS PDFs.

#### Test Coverage
- **Direct Text Input:** Verifies score calculation for both short and medium texts.
- **Web & PDF Extraction:** Tests HTML and PDF extraction from both live URLs and mocked responses.
- **GCS PDF Extraction:** Verifies GCS integration (mocked and live).
- **MCP Tools:** Verifies that the Model Context Protocol tools return correctly formatted JSON-RPC responses.
- **Validation & Errors:** Ensures 422 errors are returned for invalid inputs or source conflicts.

#### Running Tests
Run **all** tests:
```bash
uv run pytest
```

Run only **unit tests** (fast, no network):
```bash
uv run pytest test_unit.py
```

Run tests **excluding slow integration tests**:
```bash
uv run pytest -m "not slow"
```

### Benchmarking & Samples
The project includes a **Readability Golden Set** in the `samples/` directory, containing texts of varying complexity (Primary, Middle, Academic, Legal).

#### Baseline Analysis
You can run a baseline analysis to see how the engine scores these different levels:
```bash
uv run python baseline_analysis.py
```
This script:
1. Processes all files in `samples/`.
2. Prints a summary table of grade standards and word counts.
3. Saves the full metric breakdown to `samples/baseline_results.json`.

**Note:** The samples are used to verify that code or logic changes (e.g., extraction or normalization) don't unintentionally shift the readability scores of known content.

### Dependencies
Manage Python dependencies using `uv` and `pyproject.toml`.
- To add a new dependency: `uv add <package>`
- To sync environment: `uv sync`

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


# License
Apache 2.0

# Disclaimer
This is not an officially supported Google product.