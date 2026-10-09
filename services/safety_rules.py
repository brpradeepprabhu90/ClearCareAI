"""Deterministic medication-safety rules.

Pure Python: no network, no LLM. Same input -> same output, and unit-testable offline.
Hackathon prototype: have a clinician/pharmacist review severities and wording before real use.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, List, Tuple

# ---------------------------------------------------------------- drug vocab
BRAND_TO_GENERIC = {
    "advil": "ibuprofen", "motrin": "ibuprofen", "aleve": "naproxen", "naprosyn": "naproxen",
    "voltaren": "diclofenac", "celebrex": "celecoxib", "mobic": "meloxicam",
    "coumadin": "warfarin", "jantoven": "warfarin", "eliquis": "apixaban", "xarelto": "rivaroxaban",
    "lasix": "furosemide", "zestril": "lisinopril", "prinivil": "lisinopril", "coreg": "carvedilol",
    "klor-con": "potassium chloride", "k-dur": "potassium chloride", "kcl": "potassium chloride",
    "glucophage": "metformin", "lipitor": "atorvastatin",
}
NSAIDS = {"ibuprofen", "naproxen", "diclofenac", "ketorolac", "meloxicam", "celecoxib",
          "indomethacin", "etodolac", "nabumetone", "nsaid"}
ANTICOAGULANTS = {"warfarin", "apixaban", "rivaroxaban", "dabigatran", "edoxaban"}
LOOP_DIURETICS = {"furosemide", "bumetanide", "torsemide"}

ES_NAMES = {
    "warfarin": "warfarina", "ibuprofen": "ibuprofeno", "naproxen": "naproxeno",
    "diclofenac": "diclofenaco", "furosemide": "furosemida", "metformin": "metformina",
    "atorvastatin": "atorvastatina", "potassium chloride": "cloruro de potasio",
    "apixaban": "apixabán", "rivaroxaban": "rivaroxabán", "nsaid": "AINE",
}


def is_raas(c: str) -> bool:           # ACE inhibitors / ARBs
    return c.endswith("pril") or c.endswith("sartan")


def is_beta_blocker(c: str) -> bool:
    return c.endswith("olol") or c == "carvedilol"


def _known(t: str) -> bool:
    return (t in NSAIDS or t in ANTICOAGULANTS or t in LOOP_DIURETICS or is_raas(t)
            or is_beta_blocker(t) or t == "metformin" or t in BRAND_TO_GENERIC)


def canonical(med: str) -> str:
    """'Potassium chloride ER 20 mEq' -> 'potassium chloride'; 'Coumadin 5 mg' -> 'warfarin'."""
    raw = (med or "").lower().strip()
    s = re.split(r"\d", raw, maxsplit=1)[0]
    if not s.strip():
        s = re.sub(r"\d+(?:[.,]\d+)?", " ", raw)
    s = re.sub(r"[^a-z\- ]", " ", s)
    s = re.sub(r"\b(tab|tabs|tablet|tablets|cap|caps|capsule|capsules|er|xl|xr|sr|cr|dr|oral|po|mg|mcg|meq)\b", " ", s)
    s = " ".join(s.split()).strip(" -")
    if s in BRAND_TO_GENERIC:
        return BRAND_TO_GENERIC[s]
    tokens = s.split()
    if len(tokens) > 1:                 # 'warfarin sodium', 'nsaid ibuprofen', 'metformin hcl'
        for t in [t for t in tokens if t != "nsaid"] or tokens:
            if _known(t):
                return BRAND_TO_GENERIC.get(t, t)
    return s


def display(c: str) -> str:
    return "NSAID" if c == "nsaid" else c.title()


def es(c: str, cap: bool = False) -> str:
    base = ES_NAMES.get(c, c)
    return base[:1].upper() + base[1:] if cap else base


def _join(names: List[str], word: str) -> str:
    names = [n for n in names if n]
    if len(names) <= 1:
        return "".join(names)
    last = names[-1]
    w = "e" if word == "y" and last.lower().startswith(("i", "hi")) else word
    return ", ".join(names[:-1]) + f" {w} " + last


def join_en(names): return _join(names, "and")
def join_es(names): return _join(names, "y")


def detect_conditions(diagnosis: str) -> set:
    d = (diagnosis or "").lower()
    conds = set()
    if re.search(r"heart failure|hfref|hfpef|\bchf\b|cardiomyopathy", d):
        conds.add("hf")
    if re.search(r"\bckd\b|chronic kidney|kidney (disease|injury|insufficiency)|renal (insufficiency|failure|impairment)|\baki\b", d):
        conds.add("ckd")
    return conds


# ---------------------------------------------------------------- findings
Evidence = List[Tuple[str, Tuple[str, ...]]]   # (generic drug to look up, terms to find in its FDA label)


@dataclass
class RuleFinding:
    rule_id: str
    severity: str                      # "high" | "medium"
    meds: List[str]                    # canonical names; meds[0] is the "primary" med (tagged in the schedule)
    headline_en: str
    headline_es: str
    action_en: str
    action_es: str
    detail_en: str
    detail_es: str
    group: str = ""                    # findings in group "nsaid" are merged into one hero card
    reason_en: str = ""
    reason_es: str = ""
    evidence: Evidence = field(default_factory=list)


ASK_EN = "Ask your doctor or pharmacist before taking this combination."
ASK_ES = "Consulte a su médico o farmacéutico antes de tomar esta combinación."
KEEP_EN = "Do not change your medicines on your own. Ask your doctor or pharmacist."
KEEP_ES = "No cambie sus medicinas por su cuenta. Consulte a su médico o farmacéutico."


def _uniq(items: Iterable[str]) -> List[str]:
    return list(dict.fromkeys(i for i in items if i))


def evaluate_rules(medications: Iterable[str], diagnosis: str) -> List[RuleFinding]:
    all_names = [canonical(m) for m in medications if m and str(m).strip()]
    meds = _uniq(all_names)
    conds = detect_conditions(diagnosis)
    nsaids = [m for m in meds if m in NSAIDS]
    anticoags = [m for m in meds if m in ANTICOAGULANTS]
    raas = [m for m in meds if is_raas(m)]
    loops = [m for m in meds if m in LOOP_DIURETICS]
    bbs = [m for m in meds if is_beta_blocker(m)]
    potassium = [m for m in meds if m.startswith("potassium")]
    out: List[RuleFinding] = []

    for n in nsaids:
        N, Nes = display(n), es(n, True)
        for a in anticoags:
            A, Aes = display(a), es(a)
            out.append(RuleFinding(
                "warf_nsaid", "high", [n, a],
                f"{A} + {N}: major bleeding risk", f"{Aes.capitalize()} + {Nes}: riesgo grave de sangrado",
                ASK_EN, ASK_ES,
                "Anti-inflammatory pain medicines like ibuprofen can irritate the stomach and affect blood clotting. "
                "Together with a blood thinner, the risk of serious bleeding is much higher.",
                "Los antiinflamatorios como el ibuprofeno pueden irritar el estómago y afectar la coagulación. "
                "Junto con un anticoagulante, el riesgo de sangrado grave es mucho mayor.",
                group="nsaid",
                reason_en=f"With {A}: much higher risk of serious bleeding.",
                reason_es=f"Con {Aes}: mucho mayor riesgo de sangrado grave.",
                evidence=[(a, ("nsaid", "nonsteroidal", "non-steroidal", "ibuprofen")), (n, ("warfarin", "anticoagulant"))]))
        if raas and loops:
            R, L = join_en([display(x) for x in raas]), join_en([display(x) for x in loops])
            Res, Les = join_es([es(x) for x in raas]), join_es([es(x) for x in loops])
            out.append(RuleFinding(
                "triple_whammy", "high", [n] + raas + loops,
                f"{N} + {R} + {L}: kidney injury risk", f"{Nes} + {Res} + {Les}: riesgo de daño renal",
                ASK_EN, ASK_ES,
                "An anti-inflammatory pain medicine taken with an ACE inhibitor (or ARB) and a water pill can reduce "
                "blood flow to the kidneys and may cause sudden kidney injury.",
                "Un antiinflamatorio junto con un inhibidor de la ECA (o ARA) y una pastilla para orinar puede reducir "
                "el flujo de sangre a los riñones y causar daño renal repentino.",
                group="nsaid",
                reason_en=f"With {R} and {L} together: can harm the kidneys.",
                reason_es=f"Junto con {Res} y {Les}: puede dañar los riñones.",
                evidence=[(n, ("renal", "kidney")), (raas[0], ("nsaid", "non-steroidal", "nonsteroidal"))]))
        if "hf" in conds:
            out.append(RuleFinding(
                "nsaid_hf", "high", [n], f"{N} with heart failure", f"{Nes} con insuficiencia cardíaca",
                "Ask your doctor or pharmacist before taking this medicine.",
                "Consulte a su médico o farmacéutico antes de tomar este medicamento.",
                "Anti-inflammatory pain medicines can make the body hold on to salt and water, which can make heart failure worse.",
                "Los antiinflamatorios pueden hacer que el cuerpo retenga sal y agua, lo que puede empeorar la insuficiencia cardíaca.",
                group="nsaid",
                reason_en="With heart failure: can cause fluid buildup and make heart failure worse.",
                reason_es="Con insuficiencia cardíaca: puede causar acumulación de líquidos y empeorarla.",
                evidence=[(n, ("heart failure", "fluid retention", "edema"))]))
        if "ckd" in conds:
            out.append(RuleFinding(
                "nsaid_ckd", "medium", [n], f"{N} with kidney disease", f"{Nes} con enfermedad renal",
                "Ask your doctor or pharmacist before taking this medicine.",
                "Consulte a su médico o farmacéutico antes de tomar este medicamento.",
                "Anti-inflammatory pain medicines can lower kidney function, especially when the kidneys are already weak.",
                "Los antiinflamatorios pueden disminuir la función de los riñones, sobre todo si ya están débiles.",
                group="nsaid",
                reason_en="With chronic kidney disease: can lower kidney function further.",
                reason_es="Con enfermedad renal crónica: puede disminuir aún más la función de los riñones.",
                evidence=[(n, ("renal", "kidney"))]))
        partners = raas + loops + bbs
        if partners:
            out.append(RuleFinding(
                "nsaid_bp_effect", "medium", [n] + partners, f"{N} can weaken heart medicines",
                f"{Nes} puede debilitar las medicinas del corazón",
                "Ask your doctor or pharmacist before taking this medicine.",
                "Consulte a su médico o farmacéutico antes de tomar este medicamento.",
                "Anti-inflammatory pain medicines can make blood pressure and water pills work less well.",
                "Los antiinflamatorios pueden hacer que las medicinas para la presión y las pastillas para orinar funcionen peor.",
                group="nsaid",
                reason_en="Can weaken your blood pressure and water pills.",
                reason_es="Puede debilitar sus medicinas para la presión y las pastillas para orinar.",
                evidence=[(n, ("antihypertensive", "diuretic", "blood pressure"))]))

    if raas and potassium:
        r, k = raas[0], potassium[0]
        ckd = "ckd" in conds
        extra_en = " Kidney disease makes this more likely." if ckd else ""
        extra_es = " La enfermedad renal lo hace más probable." if ckd else ""
        out.append(RuleFinding(
            "acei_kcl", "high" if ckd else "medium", [k, r],
            f"{display(r)} + {display(k)}: high potassium risk",
            f"{es(r, True)} + {es(k, True)}: riesgo de potasio alto",
            KEEP_EN + " Keep your blood test (potassium and kidney) appointment.",
            KEEP_ES + " No falte a su análisis de sangre (potasio y riñones).",
            "ACE inhibitors and ARBs make the body keep potassium. Taking extra potassium as well can raise it to a "
            "level that affects the heartbeat." + extra_en,
            "Los inhibidores de la ECA y los ARA hacen que el cuerpo retenga potasio. Tomar potasio adicional puede "
            "elevarlo a un nivel que afecta el latido del corazón." + extra_es,
            evidence=[(r, ("potassium", "hyperkalemia")), (k, ("ace inhibitor", "angiotensin", "hyperkalemia"))]))

    if "metformin" in meds and "ckd" in conds:
        out.append(RuleFinding(
            "metformin_renal", "medium", ["metformin"], "Metformin with reduced kidney function",
            "Metformina con función renal reducida",
            "Keep your kidney blood tests. Ask your doctor if your dose is still right.",
            "No falte a sus análisis de riñón. Pregunte a su médico si su dosis sigue siendo adecuada.",
            "Metformin is cleared by the kidneys. When kidney function is reduced, the dose may need to be checked.",
            "Los riñones eliminan la metformina. Si la función renal está reducida, puede ser necesario revisar la dosis.",
            evidence=[("metformin", ("renal", "kidney"))]))

    for c in _uniq(all_names):
        if all_names.count(c) > 1:
            out.append(RuleFinding(
                "dup_ingredient", "medium", [c], f"{display(c)} is listed more than once",
                f"{es(c, True)} aparece más de una vez",
                "Confirm the correct dose with your doctor or pharmacist.",
                "Confirme la dosis correcta con su médico o farmacéutico.",
                "The same medicine appears more than once in the list. Taking it twice by mistake can be harmful.",
                "El mismo medicamento aparece más de una vez en la lista. Tomarlo dos veces por error puede ser dañino."))
    return out


def merge_nsaid_group(findings: List[RuleFinding]) -> List[RuleFinding]:
    """Merge every NSAID-related finding into ONE hero card (fewer, clearer cards)."""
    members = [f for f in findings if f.group == "nsaid"]
    others = [f for f in findings if f.group != "nsaid"]
    if len(members) < 2:
        return sort_findings(findings)
    members.sort(key=lambda f: severity_rank(f.severity))
    nsaid_names = [m for m in _uniq(x for f in members for x in f.meds) if m in NSAIDS]
    all_meds = nsaid_names + [m for m in _uniq(x for f in members for x in f.meds) if m not in nsaid_names]
    reasons_en = _uniq(f.reason_en for f in members)
    reasons_es = _uniq(f.reason_es for f in members)
    n = len(reasons_en)
    N, Nes = join_en([display(x) for x in nsaid_names]), join_es([es(x, True) for x in nsaid_names])
    hero = RuleFinding(
        "nsaid_multi", "high" if any(f.severity == "high" for f in members) else "medium", all_meds,
        f"{N}: {n} safety risks with your medicines and conditions",
        f"{Nes}: {n} riesgos de seguridad con sus medicinas y condiciones",
        "Do not take this unless your doctor or pharmacist says it is safe for you. Ask about other ways to treat pain.",
        "No lo tome a menos que su médico o farmacéutico le diga que es seguro para usted. Pregunte por otras formas de tratar el dolor.",
        "Why this matters:\n• " + "\n• ".join(reasons_en),
        "Por qué es importante:\n• " + "\n• ".join(reasons_es),
        evidence=[e for f in members for e in f.evidence])
    return sort_findings(others + [hero])


def severity_rank(s: str) -> int:
    return 0 if s == "high" else 1


def sort_findings(findings: List[RuleFinding]) -> List[RuleFinding]:
    # high before medium; within a severity the ibuprofen/NSAID hero card comes first (clearest story for the patient)
    return sorted(findings, key=lambda f: (severity_rank(f.severity), 0 if f.rule_id == "nsaid_multi" else 1))
