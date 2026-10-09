"""Shared OpenAI helper: one client, async calls, retry on transient errors, guardrail retry."""
from __future__ import annotations

import asyncio
import logging
import os
import random
import json
from typing import Callable, List, Type, TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

log = logging.getLogger("clearcare.llm")
MODEL = os.getenv("FEATHERLESS_MODEL", "Qwen/Qwen2.5-7B-Instruct")   # override via env
CALL_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "120"))
T = TypeVar("T", bound=BaseModel)
_client = None


class GuardrailError(RuntimeError):
    """The model's output failed validation twice; do not show it to the patient."""


def get_client():
    global _client
    if _client is None:
        if not os.getenv("FEATHERLESS_API_KEY"):
            log.warning("No FEATHERLESS_API_KEY set; requests may fail.")
        _client = AsyncOpenAI(
            api_key=os.getenv("FEATHERLESS_API_KEY", "sk-placeholder"),
            base_url="https://api.featherless.ai/v1"
        )
    return _client


def _retriable(e: Exception) -> bool:
    msg = str(e).upper()
    return (any(s in msg for s in ("429", "500", "502", "503", "504", "TIMEOUT", "RATE_LIMIT"))
            or isinstance(e, (ValueError, asyncio.TimeoutError)))


async def generate_structured(contents, schema: Type[T], *, temperature: float = 0.1, retries: int = 3) -> T:
    """Async call (does not block the event loop, so agents can really run in parallel)."""
    text_prompt = ""
    if isinstance(contents, list):
        for part in contents:
            if isinstance(part, str):
                text_prompt += part + "\n"
            elif hasattr(part, "text") and part.text:
                text_prompt += part.text + "\n"
    else:
        text_prompt = str(contents)

    sys_prompt = f"You are a helpful assistant. Output ONLY valid JSON. Return the fields at the root level. DO NOT wrap the output in a parent property (like '{schema.__name__}'). IMPORTANT: For all fields that require a string (like diagnosis, dose, frequency, source, etc.), you MUST provide a plain string. DO NOT use nested objects. For example, dose must be '5 mg', NOT {{'value': '5', 'unit': 'mg'}}.\n{json.dumps(schema.model_json_schema())}"

    last: Exception | None = None
    current_text = text_prompt
    for attempt in range(retries):
        try:
            resp = await asyncio.wait_for(
                get_client().chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": current_text}
                    ],
                    response_format={"type": "json_object"},
                    temperature=temperature,
                    max_tokens=1500,
                ),
                timeout=CALL_TIMEOUT_S
            )
            content = resp.choices[0].message.content
            if not content:
                raise ValueError("empty model response")
            try:
                data = json.loads(content)
                schema_name = schema.__name__.lower()
                # Robust unwrap: if the schema name exists as a key, use its value
                if isinstance(data, dict):
                    for k in list(data.keys()):
                        if k.lower() == schema_name or k.lower() == schema_name + "s" or k.lower() == "output":
                            if isinstance(data[k], dict):
                                data = data[k]
                                break
                return schema.model_validate(data)
            except json.JSONDecodeError:
                return schema.model_validate_json(content)
        except Exception as e:                                   # log the type only: messages may contain patient text
            last = e
            is_validation = "validation" in type(e).__name__.lower()
            log.warning("LLM call failed (attempt %d/%d): %s", attempt + 1, retries, type(e).__name__)
            if attempt == retries - 1 or not (_retriable(e) or is_validation):
                break
            if is_validation:
                # Inject the validation error into the next attempt so the LLM can learn from its mistake!
                current_text += f"\n\nYOUR PREVIOUS OUTPUT FAILED VALIDATION WITH THESE ERRORS:\n{str(e)}\n\nPLEASE FIX THESE EXACT ERRORS. Remember to strictly follow the JSON schema and DO NOT nest objects where strings are required."
            await asyncio.sleep(2 ** attempt + random.random())
    if last is not None:
        error_str = str(last) or "No details provided"
        raise RuntimeError(f"LLM call failed after {retries} attempts: {type(last).__name__}: {error_str}") from last
    raise RuntimeError("LLM call failed (no exception captured)")


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
