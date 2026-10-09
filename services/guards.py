"""Output guardrails: catch invented doses and dropped medications before they reach a patient."""
from __future__ import annotations

import json
import re
from typing import Dict, List, Set

from services.safety_rules import canonical

_DOSE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(mg|mcg|µg|meq|units?)\b", re.I)


def med_name(m: Dict) -> str:
    for k in ("name", "medication", "drug", "drug_name"):
        if k in m and m[k]:
            return str(m[k])
    return next((str(v) for v in m.values() if isinstance(v, str) and v), "")


def doses_in(text: str) -> Set[str]:
    out = set()
    for val, unit in _DOSE.findall(text or ""):
        out.add(f"{float(val.replace(',', '.')):g} {unit.lower()}")
    return out


def unexpected_doses(output_text: str, meds: List[Dict]) -> Set[str]:
    """Doses that appear in the generated text but not in the extracted medication data."""
    allowed = doses_in(json.dumps(meds, ensure_ascii=False, default=str))
    return doses_in(output_text) - allowed


def missing_meds(output_text: str, meds: List[Dict]) -> List[str]:
    low = (output_text or "").lower()
    missing = []
    for m in meds:
        name = canonical(med_name(m))
        if name and name not in low:
            missing.append(name)
    return missing


_NUM = re.compile(r"\d+(?:[.,]\d+)?")
ALLOWED_EXTRA_NUMBERS = {"1.4", "2.3", "4.5", "911"}      # metric conversions we ask for + emergency number


def numbers_in(text: str) -> Set[str]:
    return {f"{float(n.replace(',', '.')):g}" for n in _NUM.findall(text or "")}
