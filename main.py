from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.routes import router as api_router
import uvicorn
import os
from dotenv import load_dotenv

# Load env variables (like FEATHERLESS_API_KEY)
load_dotenv()

app = FastAPI(title="ClearCare AI Backend - Actual Validation")

# Include modular API routes
app.include_router(api_router)

from fastapi.responses import RedirectResponse

# Mount React build if it exists (for production)
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
else:
    @app.get("/")
    def read_root():
        return RedirectResponse(url="http://localhost:5173")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
