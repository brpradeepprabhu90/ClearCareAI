from pydantic import BaseModel, Field
from typing import List, Optional

class Medication(BaseModel):
    name: str = Field(description="Name of the medication (e.g., Lisinopril)")
    dose: str = Field(description="Dosage (e.g., 20 mg)")
    frequency: str = Field(description="How often to take it (e.g., 1 tab PO daily)")
    source: str = Field(description="Where it was found in the document (e.g., Page 2, Line 4)")

class Appointment(BaseModel):
    provider: str
    date: str
    purpose: str

class ExtractorOutput(BaseModel):
    patient_language: str = Field(description="Primary language of the patient, e.g., 'en' or 'es'", default="en")
    diagnosis: str = Field(description="Principal diagnosis")
    diet_activity_instructions: str = Field(description="Verbatim extraction of diet and activity instructions", default="")
    warning_signs_raw: str = Field(description="Raw text of warning signs and return precautions from the document", default="")
    medications: List[Medication]
    appointments: List[Appointment]

class SafetyFlag(BaseModel):
    severity: str = Field(description="'high', 'medium', or 'low'")
    drugs: List[str] = Field(description="The drugs involved in this flag")
    headline_en: str = Field(description="Short, punchy title (e.g., Warfarin + Ibuprofen)")
    headline_es: str = Field(description="Spanish translation of headline")
    action_en: str = Field(description="One line 'What to do' (e.g., Ask your doctor before taking)")
    action_es: str = Field(description="Spanish translation of action")
    detail_en: str = Field(description="Detailed clinical explanation of the interaction and source")
    detail_es: str = Field(description="Spanish translation of detail")
    citation: str = Field(description="E.g., openFDA label, Drug Interactions")

class SafetyCheckResult(BaseModel):
    flags: List[SafetyFlag]
    error: Optional[str] = None

class TimelineItem(BaseModel):
    time: str = Field(description="E.g., Morning (AM), Breakfast, 6:00 PM")
    action: str = Field(description="Meds to take at this time")

class SchedulerOutput(BaseModel):
    timeline_en: List[TimelineItem]
    timeline_es: List[TimelineItem]
    doc_warnings_en: List[str]
    doc_warnings_es: List[str]
    general_warnings_en: List[str]
    general_warnings_es: List[str]

class ExplainerOutput(BaseModel):
    summary_en: List[str] = Field(description="4-5 short bullet points explaining why they were in the hospital and next steps")
    summary_es: List[str]
    diet_activity_en: List[str] = Field(description="Diet and activity restrictions, e.g., fluid limits, sodium limits, lifting limits")
    diet_activity_es: List[str]
