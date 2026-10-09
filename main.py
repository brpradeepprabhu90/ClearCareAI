from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.routes import router as api_router
import uvicorn
import os
from dotenv import load_dotenv

# Load env variables (like GEMINI_API_KEY)
load_dotenv()

app = FastAPI(title="ClearCare AI Backend - Actual Validation")

# Include modular API routes
app.include_router(api_router)

# Mount static files
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
