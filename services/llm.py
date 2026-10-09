"""Shared Gemini helper: one client, async calls, retry on transient errors, guardrail retry."""
from __future__ import annotations

import asyncio
import logging
import os
import random
from typing import Callable, List, Type, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

log = logging.getLogger("clearcare.llm")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")   # override via env if your key uses another model id
CALL_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "60"))
T = TypeVar("T", bound=BaseModel)
_client = None


class GuardrailError(RuntimeError):
    """The model's output failed validation twice; do not show it to the patient."""


def get_client():
    global _client
    if _client is None:
        if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
            log.warning("No GEMINI_API_KEY / GOOGLE_API_KEY set; relying on default credentials.")
        _client = genai.Client()
    return _client


def _retriable(e: Exception) -> bool:
    code = getattr(e, "code", None)
    msg = str(e).upper()
    return (code in (429, 500, 502, 503, 504)
            or any(s in msg for s in ("RESOURCE_EXHAUSTED", "UNAVAILABLE", "DEADLINE", "OVERLOADED"))
            or isinstance(e, (ValueError, asyncio.TimeoutError)))   # empty / malformed JSON, timeouts


async def generate_structured(contents, schema: Type[T], *, temperature: float = 0.1, retries: int = 3) -> T:
    """Async call (does not block the event loop, so agents can really run in parallel)."""
    config = types.GenerateContentConfig(
        response_mime_type="application/json", response_schema=schema, temperature=temperature)
    last: Exception | None = None
    for attempt in range(retries):
        try:
            resp = await asyncio.wait_for(
                get_client().aio.models.generate_content(model=MODEL, contents=contents, config=config),
                timeout=CALL_TIMEOUT_S)
            if not resp.text:
                raise ValueError("empty model response")
            return schema.model_validate_json(resp.text)
        except Exception as e:                                   # log the type only: messages may contain patient text
            last = e
            log.warning("LLM call failed (attempt %d/%d): %s", attempt + 1, retries, type(e).__name__)
            if attempt == retries - 1 or not (_retriable(e) or "validation" in type(e).__name__.lower()):
                break
            await asyncio.sleep(2 ** attempt + random.random())
    raise last  # type: ignore[misc]


async def generate_checked(prompt: str, schema: Type[T], check: Callable[[T], List[str]], *,
                           temperature: float = 0.1) -> T:
    """Generate, validate with `check` (returns a list of problems), retry once with the problems, else fail closed."""
    out = await generate_structured(prompt, schema, temperature=temperature)
    problems = check(out)
    if not problems:
        return out
    log.warning("Guardrail failed (%d problem(s)); retrying once", len(problems))
    fix = "\n\nVALIDATION FAILED. Fix these problems and answer again:\n" + "\n".join(f"- {p}" for p in problems)
    out = await generate_structured(prompt + fix, schema, temperature=temperature)
    problems = check(out)
    if problems:
        raise GuardrailError("; ".join(problems))
    return out
