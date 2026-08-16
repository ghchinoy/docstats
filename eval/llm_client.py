# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Provider-agnostic LLM client with first-class Gemini support.

Supports automatic fallback between Gemini Developer API (API key) and
Google Cloud Vertex AI (Application Default Credentials).
"""

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("EVAL_MODEL", "gemini-3.7-flash")


@dataclass
class UsageStats:
    """Token usage and execution telemetry."""

    prompt_tokens: int = 0
    candidate_tokens: int = 0
    total_tokens: int = 0
    latency_seconds: float = 0.0


@dataclass
class ToolCallRecord:
    """Record of a tool invocation during a multi-turn conversation."""

    tool_name: str
    arguments: Dict[str, Any]
    result: Any


@dataclass
class LLMResponse:
    """Standardized response from an LLM invocation."""

    text: str
    model: str
    usage: UsageStats
    tool_calls: List[ToolCallRecord] = field(default_factory=list)
    raw_response: Any = None


class GeminiLLMClient:
    """Gemini client using the official google-genai SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        project: Optional[str] = None,
        location: str = "global",
        model: str = DEFAULT_MODEL,
    ):
        """Initializes the Gemini client with automatic auth resolution."""
        from google import genai

        self.model = model
        self.auth_mode: str = "unknown"

        # 1. Prefer GEMINI_API_KEY if provided or in env
        resolved_api_key = api_key or os.environ.get("GEMINI_API_KEY")
        vertex_requested = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in (
            "true",
            "1",
            "yes",
        )
        resolved_project = project or os.environ.get("GOOGLE_CLOUD_PROJECT")

        if resolved_api_key and not vertex_requested:
            self.client = genai.Client(api_key=resolved_api_key)
            self.auth_mode = "developer_api"
            logger.info("Initialized Gemini client via Gemini Developer API key.")
        elif resolved_project:
            self.client = genai.Client(
                vertexai=True, project=resolved_project, location=location
            )
            self.auth_mode = "vertex_ai"
            logger.info(
                f"Initialized Gemini client via Vertex AI "
                f"(project={resolved_project}, location={location})."
            )
        elif resolved_api_key:
            self.client = genai.Client(api_key=resolved_api_key)
            self.auth_mode = "developer_api"
            logger.info("Initialized Gemini client via Developer API key.")
        else:
            # Attempt default client initialization (may pick up ambient credentials)
            self.client = genai.Client()
            self.auth_mode = "ambient_default"
            logger.info("Initialized Gemini client using ambient environment.")

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        seed: Optional[int] = 42,
        tools: Optional[List[Callable]] = None,
        model_override: Optional[str] = None,
    ) -> LLMResponse:
        """Executes a text generation or multi-turn tool-calling loop."""
        from google.genai import types

        active_model = model_override or self.model
        config_kwargs: Dict[str, Any] = {
            "temperature": temperature,
        }
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
        if seed is not None:
            config_kwargs["seed"] = seed
        if tools:
            config_kwargs["tools"] = tools

        config = types.GenerateContentConfig(**config_kwargs)

        start_time = time.perf_counter()
        response = self.client.models.generate_content(
            model=active_model,
            contents=prompt,
            config=config,
        )
        latency = time.perf_counter() - start_time

        prompt_tokens = 0
        candidate_tokens = 0
        total_tokens = 0

        if hasattr(response, "usage_metadata") and response.usage_metadata:
            meta = response.usage_metadata
            prompt_tokens = getattr(meta, "prompt_token_count", 0) or 0
            candidate_tokens = getattr(meta, "candidates_token_count", 0) or 0
            total_tokens = getattr(meta, "total_token_count", 0) or 0

        usage = UsageStats(
            prompt_tokens=prompt_tokens,
            candidate_tokens=candidate_tokens,
            total_tokens=total_tokens,
            latency_seconds=round(latency, 3),
        )

        response_text = response.text or ""

        return LLMResponse(
            text=response_text,
            model=active_model,
            usage=usage,
            raw_response=response,
        )


class ClaudeVertexLLMClient:
    """Anthropic Claude client using the AnthropicVertex SDK (Model Garden).

    Requires Claude models enabled in the target GCP project's Vertex AI
    Model Garden. Falls back gracefully with a clear error if unavailable.
    """

    def __init__(
        self,
        project: Optional[str] = None,
        region: str = "us-east5",
        model: str = "claude-3-7-sonnet@20250219",
    ):
        """Initializes the Claude-on-Vertex client."""
        from anthropic import AnthropicVertex

        self.model = model
        self.region = region
        self.auth_mode = "vertex_anthropic"
        resolved_project = project or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.client = AnthropicVertex(project_id=resolved_project, region=region)
        logger.info(
            f"Initialized Claude client via Vertex AI "
            f"(project={resolved_project}, region={region}, model={model})."
        )

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        seed: Optional[int] = 42,
        tools: Optional[List[Callable]] = None,
        model_override: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Executes a Claude text generation call."""
        active_model = model_override or self.model

        kwargs: Dict[str, Any] = {
            "model": active_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_instruction:
            kwargs["system"] = system_instruction

        start_time = time.perf_counter()
        response = self.client.messages.create(**kwargs)
        latency = time.perf_counter() - start_time

        text_parts = [
            block.text for block in response.content if hasattr(block, "text")
        ]
        response_text = "".join(text_parts)

        input_toks = getattr(response.usage, "input_tokens", 0) or 0
        output_toks = getattr(response.usage, "output_tokens", 0) or 0

        usage = UsageStats(
            prompt_tokens=input_toks,
            candidate_tokens=output_toks,
            total_tokens=input_toks + output_toks,
            latency_seconds=round(latency, 3),
        )

        return LLMResponse(
            text=response_text,
            model=active_model,
            usage=usage,
            raw_response=response,
        )


def get_llm_client(model: Optional[str] = None):
    """Provider-agnostic factory selecting a client by model id prefix.

    - `claude-*` -> ClaudeVertexLLMClient (Vertex AI Model Garden)
    - anything else (default) -> GeminiLLMClient
    """
    resolved = model or DEFAULT_MODEL
    if resolved.lower().startswith("claude"):
        return ClaudeVertexLLMClient(model=resolved)
    return GeminiLLMClient(model=resolved)


def get_default_llm_client(model: Optional[str] = None) -> GeminiLLMClient:
    """Convenience factory to get the configured default LLM client."""
    return GeminiLLMClient(model=model or DEFAULT_MODEL)
