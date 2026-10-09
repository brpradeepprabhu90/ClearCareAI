from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from services.extractor_service import extract_data
from services.safety_service import check_safety
from services.explainer_scheduler_service import generate_explanation, generate_schedule
from models.domain import ExtractorOutput
import asyncio

router = APIRouter()

@router.post("/api/extract")
async def extract_document(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        mime_type = file.content_type
        extractor_result = await extract_data(file_bytes, mime_type)
        return {"status": "success", "extractor": extractor_result.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/generate_plan")
async def generate_plan(extractor_data: ExtractorOutput):
    try:
        med_names = [med.name for med in extractor_data.medications]
        med_dicts = [med.model_dump() for med in extractor_data.medications]
        appt_dicts = [appt.model_dump() for appt in extractor_data.appointments]
        
        # Run the 3 agents concurrently for speed
        safety_task = asyncio.create_task(check_safety(extractor_data.diagnosis, med_names))
        explainer_task = asyncio.create_task(generate_explanation(extractor_data.diagnosis, med_dicts, appt_dicts, extractor_data.diet_activity_instructions))
        scheduler_task = asyncio.create_task(generate_schedule(med_dicts, extractor_data.warning_signs_raw))
        
        safety_result, explainer_result, scheduler_result = await asyncio.gather(
            safety_task, explainer_task, scheduler_task
        )
        
        return {
            "status": "success",
            "safety_check": safety_result.model_dump(),
            "explainer": explainer_result.model_dump(),
            "scheduler": scheduler_result.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
