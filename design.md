# ClearCare AI: Design Document

**Hackathon:** ForgeHacks Online 2026 | **Track:** AI + Healthcare | **Deadline:** Oct 10, 2026, 12:00pm EDT
**Formerly:** DischargeIQ
**One-liner:** Turn confusing hospital discharge papers into a safe, plain-language, multilingual care plan, with a medication-safety check on top.

> **Status legend used in this doc:** ✅ Built (seen working) | 🟡 Partial / needs fix | 🔲 Planned

---

## 1. Problem

| Fact | Impact |
|---|---|
| Discharge papers run 10+ pages of clinical shorthand (PRN, BID, q6h, HFrEF, GDMT) | Patients and caregivers can't act on them |
| New meds, changed doses, and old meds are mixed together | Duplicate or conflicting medications |
| Instructions are often given in English only, verbally and in writing | Non-English speakers are left behind |
| Dangerous combinations aren't flagged at the point of discharge (e.g., a blood thinner + an NSAID) | Preventable bleeding, kidney injury, readmission |

**Who is hit hardest:** elderly patients, non-native English speakers, people with low health literacy, and the family members who manage medications for them.

## 2. Product Vision

Upload a discharge summary, get back in seconds:
1. **What happened to me** (plain language, in my language)
2. **What to take and when** (a daily schedule)
3. **What could hurt me** (a severity-ranked safety check)
4. **What I can and can't do** (diet and activity limits)
5. **When to call for help** (warning signs)
6. **A printable plan** I can hand to family

## 3. Users

| Persona | Need | Key feature |
|---|---|---|
| **Patient** (e.g., 75-year-old, Spanish-speaking) | "What do I take, when, and what's dangerous?" | Spanish plan, schedule, safety cards |
| **Family caregiver** | One shareable page that's easy to follow | Print Plan, plain language |
| **Care coordinator / nurse** (extension) | Fewer follow-up calls, catch errors early | Safety flags with reasoning |

## 4. Goals and Non-Goals

| Goals | Non-Goals |
|---|---|
| Accurate extraction of meds, doses, appointments, restrictions | Diagnosing or giving medical advice |
| Surface medication risks clearly and conservatively | Replacing the care team or pharmacist |
| Plain-language output at about a 6th-grade reading level | EHR integration |
| English and Spanish output for every patient-facing string | Storing patient data or user accounts |
| Fast, demo-ready, end-to-end flow | Native mobile app |

## 5. Feature Catalog

| # | Feature | Description | Status |
|---|---|---|---|
| F1 | **Document upload** | Upload a discharge summary PDF (photo support planned) | ✅ |
| F2 | **Structured extraction** | Meds, doses, frequency, status (new/changed/continued), appointments, restrictions, warning signs | ✅ |
| F3 | **Safety Check** | Severity-ranked cards (High Risk / Warning) for interactions and contraindications, each with an explanation | ✅ |
| F4 | **Inline med warning** | Red tag on risky meds inside the schedule (e.g., ibuprofen: "Interacts with Warfarin/HF meds. Ask your doctor first.") | ✅ |
| F5 | **Plain-Language Summary** | Short bullets: why you were hospitalized, why it happened, key instructions, appointments (with warfarin's purpose explained) | ✅ |
| F6 | **Diet & Activity Limits** | Sodium and fluid limits, daily weights, lifting limit, walking, vitamin K consistency | ✅ |
| F7 | **Daily Schedule** | Meds grouped by time of day (Morning/Breakfast, Evening 6:00 PM/Dinner, Bedtime, As Needed) with dose and instructions | ✅ |
| F8 | **English / Español toggle** | Summary, diet, and schedule switch language | 🟡 Safety cards, inline tag, and doctor card are not yet translated |
| F9 | **When to Call the Doctor** | Red-flag symptoms from the document plus standard HF and anticoagulant warnings | 🟡 Card renders empty in the latest build |
| F10 | **Privacy badge** | "Processed in memory. Nothing is stored." | ✅ (must stay true; see §12) |
| F11 | **Disclaimer bar** | "Not medical advice. Confirm this plan with your care team." | ✅ |
| F12 | **Print Plan / Start Over** | Print-friendly output; reset to upload another document | 🟡 Print stylesheet needs a light theme |
| F13 | **Confirm-meds step** | User reviews extracted meds before the plan is generated | 🔲 |
| F14 | **Source citations** | Each med/flag links to the page and line in the source document | 🔲 |
| F15 | **Database-grounded interaction check** | openFDA label "Drug Interactions" text cited per flag; RxNorm for name normalization | 🔲 |
| F16 | **Deterministic rule table** | Known high-risk pairs always flagged, so results don't vary between runs | 🔲 |
| F17 | **Calendar export (.ics)** | Appointments and INR check as calendar events | 🔲 |
| F18 | **Evaluation harness** | Field-level F1 on extraction, interaction recall, readability score | 🔲 |
| F19 | **Auto language detection** | Defaults the toggle to the patient language found in the document | 🔲 |

## 6. Screen Design

**Style:** dark theme, glass cards, blue/purple accents. Header: logo, privacy badge, nav (Dashboard / Patients / Settings). Page title "Patient Care Plan" with the EN/ES toggle at the right.

| Section | Layout | Content | Design notes |
|---|---|---|---|
| **Safety Check** (hero) | Full-width card, 3-4 columns of flag cards | Severity pill (red High Risk, amber Warning), title, explanation, source label | Hero because it's the differentiator. Target: headline, one "What to do" line, expandable clinical detail |
| **Plain-Language Summary** | Left card | 4-5 bullets | One idea per bullet; dates written out in words |
| **Diet & Activity Limits** | Middle card | Bulleted limits with red markers | Hide the card if there's no data |
| **Daily Schedule** | Right card | Time-of-day rows, purple left rail | Risky meds carry a red inline tag |
| **When to Call the Doctor** | Full-width card | Warning-sign list | Split: "From your discharge papers" vs. "General safety info" |
| **Footer** | Disclaimer bar, then Start Over and Print Plan buttons | | Print uses a light, ink-friendly theme |

## 7. User Flow

```
Upload PDF → Extract → (Confirm meds) → Safety check + Explain + Schedule
          → Assemble plan → View (EN/ES) → Print or Start Over
```

| Step | System behavior | Failure handling |
|---|---|---|
| Upload | Accept PDF; read in memory | Reject non-PDF or oversized files with a clear message |
| Extract | Vision/text LLM fills the schema; validate with Pydantic | Retry once; show "couldn't read this section" for low-confidence fields |
| Confirm (planned) | Table of extracted meds the user can edit | Block plan generation until confirmed |
| Analyze | Safety, Explainer, and Scheduler run in parallel | Show partial results with a banner if one step fails |
| View | Render cards; language toggle re-renders every string | Fall back to English with a note if translation fails |

## 8. Architecture

```
                 ┌────────────┐
   PDF upload ─▶ │ Extractor  │──▶ structured JSON (validated)
                 └────────────┘
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
 ┌────────────┐  ┌─────────────┐  ┌────────────┐
 │ Safety     │  │ Explainer   │  │ Scheduler  │
 │ rules +    │  │ summary,    │  │ timeline,  │
 │ label data │  │ diet, flags │  │ .ics       │
 │ + LLM text │  │ (EN / ES)   │  │            │
 └─────┬──────┘  └──────┬──────┘  └─────┬──────┘
       └────────────────┼───────────────┘
                        ▼
                ┌───────────────┐
                │  Assembler    │ → plan JSON → Web UI (EN/ES, Print)
                └───────────────┘
```

**Runtime:** Python backend (FastAPI) serving a single-page web UI (runs locally at `0.0.0.0:8000`). LLM provider is configurable via environment variable.

## 9. Components

### 9.1 Extractor
- **Input:** PDF text and/or page images.
- **Output:** JSON per §10, validated with Pydantic.
- **Reconciliation rule:** same drug name with a different dose across home vs. discharge lists is `status: "changed"`, never a duplicate. (Fixes an early false positive where lisinopril 10 mg → 20 mg showed as "duplicate therapy".)
- **Extra fields:** `source_ref` (page:line) and `confidence` per item.

### 9.2 Safety Agent
**Design principle: rules decide, data supports, the LLM explains.**

| Layer | Role |
|---|---|
| 1. Normalization | Map names to RxNorm ingredient IDs (brand/generic safe) |
| 2. Deterministic rule table | Always-flag pairs and class rules (see §11) |
| 3. Label grounding | Pull the openFDA drug-label "Drug Interactions" and "Warnings" text for each med and cite the section |
| 4. LLM explanation | Convert flagged findings into a plain-language headline, "What to do", and optional clinical detail, in the selected language |
| 5. Source label | Truthful label per flag: "Rule + FDA label" or "AI-assisted check" |

The LLM never removes or downgrades a rule-triggered flag. It may add "additional considerations", labeled as AI-generated.

### 9.3 Explainer
- 4-5 bullets, about a 6th-grade reading level.
- Must include: why hospitalized, the likely cause as stated in the document, the key action, what any anticoagulant is for, and each appointment (provider, date written out, purpose).
- Dates are written out ("9 October 2026" / "9 de octubre de 2026") to avoid DD/MM vs. MM/DD confusion.
- No invented provider gender in translation (neutral "Dr./Dra." or name only).
- Thresholds (e.g., weight gain) are copied from the source document, never paraphrased numerically.

### 9.4 Scheduler
- Maps frequency to clock slots: daily AM, BID (breakfast + dinner), 6 PM (as written), bedtime, PRN.
- Warfarin keeps its stated time (6:00 PM) and is not merged into generic "dinner".
- Rows are sorted by clock time; PRN is last with the max-frequency note.
- Each risky med inherits the inline warning from the Safety Agent.
- Optional: export appointments and INR check to `.ics`.

### 9.5 Assembler
- Merges outputs into one plan JSON, attaches citations, enforces **"every visible string exists in both languages"** (a missing string fails the build in tests).
- Splits patient-document content from general safety info.

### 9.6 Web UI
- Single-page app; toggling language re-renders from the plan JSON (no new LLM call when both languages were pre-generated).
- Print stylesheet (`@media print`): light background, no fixed nav, safety first.

## 10. Data Schema (plan JSON)

```json
{
  "patient": {"name": "Maria L. Gonzalez", "language": "es", "age": 75},
  "diagnosis": {"principal": "Acute decompensated heart failure", "secondary": ["AFib", "T2DM", "CKD 3a"]},
  "medications": [
    {"name": "lisinopril", "rxcui": "29046", "dose": "20 mg", "frequency": "daily",
     "status": "changed", "previous_dose": "10 mg", "source_ref": "p2:l8", "confidence": 0.97},
    {"name": "ibuprofen", "dose": "400 mg", "frequency": "q6h PRN", "indication": "knee pain",
     "status": "new", "warning_ids": ["warf_nsaid", "nsaid_hf", "triple_whammy"]}
  ],
  "appointments": [
    {"with": "Anticoagulation Clinic", "when": "2026-10-09T14:00", "purpose": "INR check"},
    {"with": "Cardiology - Dr. R. Chen", "when": "2026-10-13T09:30", "purpose": "Heart and fluid check"},
    {"with": "PCP - Dr. L. Moreno", "when": "2026-10-20T11:00", "purpose": "Blood tests, med review"}
  ],
  "restrictions": {"sodium_g": 2, "fluid_l": 1.5, "lifting_lbs": 10, "lifting_weeks": 2, "daily_weight": true},
  "warning_signs": [
    {"text": "Weight gain >3 lbs in 24 h or >5 lbs in 1 week", "origin": "document"},
    {"text": "Black or tarry stools, unusual bleeding", "origin": "document"},
    {"text": "Signs of an allergic reaction", "origin": "general"}
  ],
  "safety_flags": [
    {"id": "warf_nsaid", "severity": "high", "drugs": ["warfarin", "ibuprofen"],
     "headline": {"en": "...", "es": "..."}, "action": {"en": "...", "es": "..."},
     "detail": {"en": "...", "es": "..."},
     "basis": "rule+label", "citation": "openFDA label, Drug Interactions"}
  ]
}
```

## 11. Safety Logic

### Severity definitions
| Level | Meaning | UI |
|---|---|---|
| **High Risk** | Known serious harm; "ask your doctor before taking" | Red card, shown first |
| **Warning** | Needs monitoring or clarification | Amber card |
| **Info** | Good-to-know | Collapsed list |

### Deterministic rules (v1)
| Rule ID | Trigger | Severity | Rationale |
|---|---|---|---|
| `warf_nsaid` | Warfarin + any NSAID | High | Major bleeding risk |
| `acei_kcl` | ACE inhibitor + potassium supplement | High (CKD present) / Warning (otherwise) | Hyperkalemia |
| `triple_whammy` | ACE inhibitor/ARB + diuretic + NSAID | High | Acute kidney injury |
| `nsaid_hf` | NSAID + heart failure diagnosis | High | Fluid retention, HF worsening |
| `nsaid_ckd` | NSAID + CKD | Warning | Kidney function |
| `dup_ingredient` | Same ingredient listed twice with the same dose | Warning | Duplicate therapy (not for dose changes) |
| `metformin_renal` | Metformin + reduced kidney function | Warning (not High while stable) | Lactic acidosis; review at labs |

⚠️ **Clinical review needed:** severities and rules should be reviewed by a licensed clinician or pharmacist before any real-world use. This is a hackathon prototype.

### Output requirements for every flag
Headline (1 line), "What to do" (1 line), expandable detail, basis label, and a citation when available.

## 12. Privacy and Security

| Topic | Approach |
|---|---|
| Data used | Synthetic documents only; no real patient data in repo, demo, or tests |
| Storage | Uploads processed in memory; no DB; no logging of document content |
| Third-party LLM | The document text is sent to the configured LLM provider. The privacy badge must be worded accurately: "Not stored by ClearCare" (or document that provider terms apply) |
| Compliance claims | No "HIPAA compliant" claim. Prototype only |
| Secrets | API keys in environment variables, excluded from git |

## 13. Evaluation Plan

| Metric | Method | Target |
|---|---|---|
| Extraction accuracy | Field-level F1 on 20-30 synthetic documents vs. ground truth JSON | ≥ 0.90 |
| Interaction recall | Seeded high-risk pairs (warfarin+NSAID, ACEi+KCl, triple whammy, NSAID in HF) | 100% on seeded set |
| False-positive rate | Documents with benign lists, plus dose-change cases | Near zero on the dose-change case |
| Determinism | Run the same document 5× | Identical flag set |
| Readability | Flesch-Kincaid grade: source vs. plan | Source ≥ grade 12 → plan ≤ grade 7 |
| Translation sanity | Back-translate a sample; check numbers, dates, doses unchanged | 100% numeric match |
| i18n completeness | Toggle language; assert every visible string changes | 0 untranslated strings |

### Reference test document
`sample_discharge_summary.pdf` (synthetic, 2 pages): 75-year-old Spanish-speaking patient with heart failure, AFib, T2DM, CKD 3a.

| Seeded case | Expected result |
|---|---|
| Warfarin (home) + ibuprofen PRN (new) | High: bleeding |
| Lisinopril 20 + KCl 20 mEq, Cr 1.3 | High: hyperkalemia |
| Lisinopril + furosemide + ibuprofen | High: triple whammy / AKI |
| Ibuprofen in HFrEF | High: HF worsening |
| Lisinopril 10 → 20 mg | "Changed", no duplicate flag |
| Warfarin 6:00 PM | Scheduled at 6:00 PM |
| 3 appointments | All extracted with provider, date, time |
| Spanish patient, English-only papers | Language auto-detected as ES |

## 14. Known Issues and Fix Order

| Priority | Issue | Fix |
|---|---|---|
| 🔴 1 | "When to call the doctor" card is empty | Populate from `warning_signs`; add a fallback; check in both languages |
| 🔴 2 | Safety cards and inline tag stay in English in Español mode | Pass language through the Safety Agent; add the i18n test |
| 🔴 3 | Flags vary between runs (triple whammy appeared, then vanished) | Deterministic rule table; temperature 0; cache the demo result |
| 🔴 4 | Metformin-in-HF flagged High though patient is stable and plan says continue | Downgrade to Warning; clinician review |
| 🟠 5 | Safety text is textbook-dense | Headline + action + expandable detail |
| 🟠 6 | Ibuprofen appears in 3-4 separate cards | Add a single hero: "Ibuprofen is unsafe with 3 of your medicines" |
| 🟠 7 | Source label is "AI-assisted" only | Add openFDA label citations; RxNorm for name normalization |
| 🟡 8 | Ambiguous numeric dates (09/10/2026) | Write dates out in words |
| 🟡 9 | Invented gender in the Spanish provider title | Use a neutral form |
| 🟡 10 | Print layout (overlapping nav, dark theme) | Print stylesheet |
| 🟡 11 | Privacy badge wording vs. LLM provider reality | Reword per §12 |

## 15. Limitations (state these in the README and video)
- Prototype tested on synthetic documents only; not clinically validated.
- Interaction coverage is limited to the rule table plus label text, not a full interaction database.
- Not a substitute for a pharmacist or physician.
- Translation quality needs human review before real use.

## 16. Judging Criteria Mapping

| Criterion | Where ClearCare AI delivers |
|---|---|
| **Real-world impact** | Real discharge-error problem; patient, caregiver, and coordinator personas; Spanish support for underserved patients |
| **Technical implementation and AI use** | Multi-stage pipeline: structured extraction, deterministic safety rules, label grounding, LLM explanation, i18n, eval harness. Not just a wrapper |
| **Innovation** | A verification layer that flags dangerous combinations before the patient leaves, in the patient's language |
| **Execution and completeness** | End-to-end demo: upload → plan → toggle → print |
| **Presentation** | Story-driven video, README with architecture diagram and eval table, honest limitations |

## 17. Demo Script (3 min)

| Time | Beat |
|---|---|
| 0:00 | **Hook:** show the jargon-heavy discharge page. "Maria, 75, Spanish-speaking, leaves with 7 medications and papers in English" |
| 0:30 | Upload; show extraction (meds, doses, appointments) |
| 1:15 | **Safety Check:** highlight the ibuprofen hero (blood thinner + heart + kidney risk). "The rules caught this, the AI explained it" |
| 1:50 | Toggle to **Español**: summary, schedule with the warfarin 6 PM dose, diet limits, warning signs |
| 2:20 | Print Plan; show eval numbers (recall, F1, readability) |
| 2:45 | Impact and limitations; call to action |

## 18. Submission Checklist (Devpost)

| Item | Done |
|---|---|
| Project title and short description | ☐ |
| Track selected: **AI + Healthcare** | ☐ |
| Public demo video (2-4 min, YouTube) | ☐ |
| GitHub repo with clear README (setup, architecture diagram, eval table, limitations) | ☐ |
| Written description: problem and users, technical approach, real-world impact | ☐ |
| Screenshots / architecture diagram / deployment link | ☐ |
| Submit before **Oct 10, 12:00pm EDT** (leave buffer) | ☐ |

## 19. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Time (under 2 days) | Priority: §14 items 1-3, then README and video; cut `.ics` and the confirm step if needed |
| LLM variance in demo | Rule table, temperature 0, cached demo output |
| Medical hallucination | Schema validation, rules, label citations, "AI-assisted" labeling |
| Over-claiming | Truthful badges; limitations section; no HIPAA claim |
| API quota or billing issues | Cache responses; keep a recorded fallback run |
| Translation errors | Back-translation check; numbers and dates verified programmatically |

## 20. Repo Structure

```text
forge_hacks/
├── README.md
├── design.md
├── api/
│   └── routes.py                 # FastAPI endpoints (upload, orchestration)
├── models/
│   └── domain.py                 # Pydantic schemas enforcing strict JSON contracts
├── services/
│   ├── explainer_scheduler_service.py  # Summary and Schedule generation agents
│   ├── extractor_service.py            # PDF text extraction agent
│   ├── safety_service.py               # Deterministic and LLM safety checks
│   ├── safety_rules.py                 # Deterministic interaction rules
│   └── openfda_client.py               # FDA label fetching
├── frontend/                     # Modern React SPA
│   ├── package.json              # NPM dependencies
│   ├── vite.config.js            # Vite build and proxy config
│   ├── src/                      
│   │   ├── App.jsx               # Main React Application
│   │   ├── main.jsx              # Vite Entrypoint
│   │   ├── index.css             # Tailwind CSS entrypoint
│   │   ├── components/           # React Components (UploadView, DashboardView, etc)
│   │   └── store/useAppStore.js  # Zustand state management
├── main.py                       # FastAPI application entrypoint
├── requirements.txt              # Python dependencies
└── .env                          # Environment variables (API keys)
```

## 21. API Contract (target)

| Endpoint | Method | Request | Response |
|---|---|---|---|
| `/api/extract` | POST | multipart PDF | extracted JSON (for the confirm step) |
| `/api/generate_plan` | POST | confirmed JSON, `lang` | plan JSON (§10) with EN and ES strings |
| `/api/health` | GET | none | `{"status":"ok"}` |