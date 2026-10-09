"""Fetch real FDA label text from openFDA to back each rule with a citation.

Fails soft: on any error we return None and the UI says "FDA label text not retrieved" (never a fake citation).
Labels are cached in memory only (process lifetime), consistent with "nothing is stored".
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Dict, Optional, Tuple

import httpx

log = logging.getLogger("clearcare.openfda")
URL = "https://api.fda.gov/drug/label.json"
SECTIONS = [("drug_interactions", "Drug Interactions"), ("warnings_and_cautions", "Warnings and Precautions"),
            ("warnings", "Warnings"), ("precautions", "Precautions"), ("contraindications", "Contraindications"),
            ("boxed_warning", "Boxed Warning")]
_cache: Dict[str, Optional[Dict[str, str]]] = {}
_SAFE = re.compile(r"[a-z][a-z \-]{1,40}")


async def _get_label(http: httpx.AsyncClient, generic: str) -> Optional[Dict[str, str]]:
    generic = generic.lower().strip()
    if not _SAFE.fullmatch(generic):                       # names come from an untrusted document
        return None
    if generic in _cache:
        return _cache[generic]
    params = {"search": f'openfda.generic_name:"{generic}" AND openfda.product_type:"HUMAN PRESCRIPTION DRUG"',
              "limit": 5}
    if os.getenv("OPENFDA_API_KEY"):
        params["api_key"] = os.environ["OPENFDA_API_KEY"]
    try:
        r = await http.get(URL, params=params)
        if r.status_code != 200:
            _cache[generic] = None
            return None
        merged: Dict[str, str] = {}
        for res in r.json().get("results", []):
            for key, _ in SECTIONS:
                if key not in merged and res.get(key):
                    merged[key] = " ".join(res[key]).lower()
        _cache[generic] = merged or None
    except Exception as e:
        log.warning("openFDA lookup failed: %s", type(e).__name__)
        return None                                         # do not cache transient failures
    return _cache[generic]


async def find_evidence(evidence) -> Optional[Tuple[str, str]]:
    """evidence = [(generic_name, (terms...)), ...] -> (generic, section label) of the first label that mentions a term."""
    if not evidence:
        return None
    async with httpx.AsyncClient(timeout=4.0) as http:
        labels = await asyncio.gather(*[_get_label(http, g) for g, _ in evidence])
    for (generic, terms), label in zip(evidence, labels):
        if not label:
            continue
        for key, title in SECTIONS:
            if key in label and any(t in label[key] for t in terms):
                return generic.title(), title
    return None
