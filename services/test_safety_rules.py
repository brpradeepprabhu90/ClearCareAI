import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.safety_rules import canonical, evaluate_rules, merge_nsaid_group, detect_conditions  # noqa: E402
from services.guards import unexpected_doses, missing_meds, numbers_in  # noqa: E402

SAMPLE_MEDS = [
    "Warfarin 5 mg tab", "Metformin 500 mg tab", "Furosemide 40 mg tab", "Carvedilol 6.25 mg tab",
    "Lisinopril 20 mg tab", "Potassium chloride ER 20 mEq", "Ibuprofen 400 mg tab", "Atorvastatin 40 mg tab",
]
SAMPLE_DX = ("Principal: Acute decompensated congestive heart failure (HFrEF, EF 35%). "
             "Secondary: persistent atrial fibrillation, T2DM, CKD stage 3a.")


def run(meds=SAMPLE_MEDS, dx=SAMPLE_DX):
    return merge_nsaid_group(evaluate_rules(meds, dx))


def test_canonical():
    assert canonical("Potassium chloride ER 20 mEq") == "potassium chloride"
    assert canonical("Coumadin 5 mg") == "warfarin"
    assert canonical("Warfarin sodium 5 mg") == "warfarin"
    assert canonical("NSAID (Ibuprofen)") == "ibuprofen"
    assert canonical("Advil") == "ibuprofen"


def test_conditions():
    assert detect_conditions(SAMPLE_DX) == {"hf", "ckd"}
    assert detect_conditions("Pneumonia") == set()


def test_sample_document_flags():
    f = {x.rule_id: x for x in run()}
    assert set(f) == {"nsaid_multi", "acei_kcl", "metformin_renal"}
    assert f["nsaid_multi"].severity == "high" and f["nsaid_multi"].meds[0] == "ibuprofen"
    assert f["acei_kcl"].severity == "high" and f["acei_kcl"].meds[0] == "potassium chloride"
    assert f["metformin_renal"].severity == "medium"
    assert [x.severity for x in run()] == sorted([x.severity for x in run()], key=lambda s: s != "high")


def test_hero_lists_reasons_in_both_languages():
    hero = {x.rule_id: x for x in run()}["nsaid_multi"]
    assert "bleeding" in hero.detail_en and "sangrado" in hero.detail_es
    assert "kidneys" in hero.detail_en and "riñones" in hero.detail_es
    assert "heart failure" in hero.detail_en and "insuficiencia cardíaca" in hero.detail_es


def test_dose_change_is_not_duplicate():           # extractor lists only the NEW lisinopril dose
    assert "dup_ingredient" not in {x.rule_id for x in run()}


def test_true_duplicate_is_flagged():
    ids = {x.rule_id for x in run(SAMPLE_MEDS + ["Lisinopril 10 mg tab"])}
    assert "dup_ingredient" in ids


def test_acei_kcl_without_ckd_is_still_flagged_medium():   # old code silently dropped this case
    f = {x.rule_id: x for x in run(dx="Heart failure")}
    assert f["acei_kcl"].severity == "medium"


def test_no_condition_info_still_catches_drug_drug_rules():
    ids = {x.rule_id for x in run(dx="")}
    assert "nsaid_multi" in ids and "acei_kcl" in ids   # warfarin+NSAID, triple whammy, ACEi+KCl


def test_empty_list_has_no_findings():
    assert run(meds=[]) == []


def test_single_nsaid_reason_stays_standalone():
    f = run(meds=["Ibuprofen 400 mg", "Atorvastatin 40 mg"], dx="")
    assert f == []


def test_deterministic():
    a = [(x.rule_id, x.severity, x.headline_en) for x in run()]
    assert all(a == [(x.rule_id, x.severity, x.headline_en) for x in run()] for _ in range(5))


def test_dose_guard():
    meds = [{"name": "Lisinopril", "dose": "20 mg"}, {"name": "Carvedilol", "dose": "6.25 mg"}]
    assert unexpected_doses("Take Lisinopril 20 mg and Carvedilol 6,25 mg", meds) == set()
    assert unexpected_doses("Take Lisinopril 10 mg", meds) == {"10 mg"}


def test_missing_meds_guard():
    meds = [{"name": "Lisinopril 20 mg"}, {"name": "Warfarin 5 mg"}]
    assert missing_meds("Take lisinopril in the morning", meds) == ["warfarin"]


def test_numbers_guard_catches_invented_threshold():
    raw = "Weight gain >3 lbs in 24 h or >5 lbs in 1 week"
    assert numbers_in("gain more than 2-3 pounds in a day or 5 pounds in a week") - numbers_in(raw) == {"2"}
    assert numbers_in("Aumento de peso de más de 3 lbs (1,4 kg) en 24 h") - numbers_in(raw) == {"1.4"}
