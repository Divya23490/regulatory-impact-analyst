"""Central configuration: load .env once, expose model factories for each framework.

Why a single module for this?
- All three frameworks need a model client, but each wants it in a different shape:
    * LangGraph / Deep Agents want a LangChain `BaseChatModel`.
    * AutoGen wants its own `ChatCompletionClient`.
  Keeping both constructions here means there is exactly one place that reads the
  API key and the model id.

Provider: Google Gemini, via its own SDK for LangChain and via its
OpenAI-compatible endpoint for AutoGen (AutoGen has no native Gemini client, but
Gemini exposes an OpenAI-shaped API, so `OpenAIChatCompletionClient` pointed at
Google's base URL works unmodified).
"""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()  # read .env into os.environ on import

MODEL_ID = os.getenv("REGIMPACT_MODEL", "gemini-3.5-flash-lite")
_GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def _require_key() -> str:
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Copy .env.example to .env and fill it in "
            "(get a key at https://aistudio.google.com/apikey)."
        )
    return key


@lru_cache(maxsize=1)
def langchain_model():
    """A LangChain chat model — consumed by LangGraph nodes and by the Deep Agent.

    NOTE: we deliberately do NOT wrap this in LangChain's generic `.with_retry()`
    — that returns a `RunnableRetry`, which drops `.bind_tools()`, and
    `create_deep_agent` needs `.bind_tools()` to give the model its tools.
    `max_retries` is Gemini's own retry knob (its SDK already retries transient
    5xx/429s internally); we just raise it a bit above the library default of 6,
    since the free tier's "high demand" 503s can need a few extra attempts.
    """
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=MODEL_ID,
        google_api_key=_require_key(),
        max_output_tokens=8000,
        max_retries=10,
    )


@lru_cache(maxsize=1)
def autogen_model_client():
    """An AutoGen model client — consumed by the review-committee agents.

    We pass `model_info` explicitly so AutoGen does not need a built-in entry for
    whatever model id we happen to use, and point the OpenAI-compatible client at
    Google's Gemini endpoint instead of OpenAI's.
    """
    from autogen_core.models import ModelFamily
    from autogen_ext.models.openai import OpenAIChatCompletionClient

    return OpenAIChatCompletionClient(
        model=MODEL_ID,
        api_key=_require_key(),
        base_url=_GEMINI_OPENAI_BASE_URL,
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            # No enum entry for 3.6 yet; GEMINI_2_5_FLASH is the closest known
            # family and gets AutoGen's Gemini-specific tool-call handling.
            "family": ModelFamily.GEMINI_2_5_FLASH,
            "structured_output": True,
        },
    )
