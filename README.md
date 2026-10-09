# ClearCare AI

**Your Discharge, Decoded for a Better Recovery.**

ClearCare AI is an intelligent medical discharge dashboard designed to reduce readmissions by making complex clinical discharge summaries easy to understand. It extracts dense medical data from uploaded PDFs and uses a multi-agent system (powered by Featherless AI) to generate a plain-language summary, a structured daily schedule, and critical clinical safety checks.

## Features

- **Multi-Agent Orchestration**: Concurrently runs 3 specialized agents (Safety, Explainer, Scheduler) for high-speed processing.
- **Bilingual Support (EN/ES)**: Instantly toggle the entire care plan between English and Spanish.
- **Deterministic Safety Rules**: Uses a hardcoded clinical rule engine combined with AI-assisted checks to guarantee critical drug-drug and drug-disease warnings are always flagged (e.g., NSAIDs + Heart Failure).
- **HIPAA-Conscious Architecture**: Processes PDFs entirely in memory without writing sensitive files to disk.
- **Smart Timeline**: Intelligently groups medications by time of day and highlights dangerous interactions directly in the schedule.

## Project Structure

```text
forge_hacks/
├── api/
│   └── routes.py                 # FastAPI endpoints (upload, orchestration)
├── models/
│   └── domain.py                 # Pydantic schemas enforcing strict JSON contracts
├── services/
│   ├── explainer_scheduler_service.py  # Summary and Schedule generation agents
│   ├── extractor_service.py            # PDF text extraction agent
│   └── safety_service.py               # Deterministic and LLM safety checks
├── static/
│   ├── app.js                    # Vanilla JS frontend logic
│   ├── index.html                # Main UI dashboard
│   ├── styles.css                # Custom CSS (Glassmorphism, responsive grid)
│   └── logo.jpg                  # Project logo
├── main.py                       # FastAPI application entrypoint
├── design.md                     # Technical architecture and specs
├── requirements.txt              # Python dependencies
└── .env                          # Environment variables (API keys)
```

## Prerequisites

- **Python 3.10+**
- A **Featherless AI API Key** (from https://featherless.ai/)

## Installation

1. **Clone or download the repository:**
   ```bash
   cd forge_hacks
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate

   # On Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   *(Ensure you have a `requirements.txt` containing at least `fastapi`, `uvicorn`, `pydantic`, `google-genai`, `python-multipart`, and `httpx`)*
   ```bash
   pip install -r requirements.txt
   ```
   *If `requirements.txt` is not present, install manually:*
   ```bash
   pip install fastapi uvicorn pydantic google-genai python-multipart httpx PyPDF2
   ```

4. **Set up Environment Variables:**
   Create a `.env` file in the root directory and add your Featherless API key:
   ```env
   FEATHERLESS_API_KEY=your_actual_api_key_here
   ```

## Running the Application

1. **Start the FastAPI server:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Open the Application:**
   Open your web browser and navigate to:
   [http://localhost:8000](http://localhost:8000)

3. **Usage:**
   - Drag and drop a patient discharge PDF into the upload zone.
   - Wait for the multi-agent pipeline to process the file.
   - Review the generated Bilingual Dashboard, Safety Checks, and Daily Schedule.

## Important Note on Data Privacy

This application is a **prototype** designed for a hackathon. While it implements an in-memory extraction pipeline to avoid saving PDFs to disk, **do not upload real Protected Health Information (PHI)** unless your Featherless AI account is specifically configured with HIPAA BAAs (Business Associate Agreements) and enterprise data governance policies. Always use mock or anonymized patient data for development and testing.

## Built With

- **Backend**: FastAPI, Pydantic, Python `asyncio`
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (No heavy frameworks)
- **AI**: Featherless AI
