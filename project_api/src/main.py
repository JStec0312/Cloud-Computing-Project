from src.api.routers.auth import limiter, router as auth_controller
from src.api.routers.files import router as files_controller
from src.config.logging import configure_logging
from fastapi import FastAPI
# IMPORT CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware 

configure_logging("DEBUG")

STANDARD_PREFIX = "/api/v1"

app = FastAPI(
    title="Cloud Drive API",
    description="A robust REST API for cloud storage service with file versioning, rate limiting, and S3 support.",
    version="1.0.0"
)

# --- ADD THIS SECTION ---
# This allows your React app to talk to the backend
origins = [
    "http://localhost:5173", # Vite (React) default port
    "http://localhost:3000", # Create React App default port
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ------------------------

app.include_router(auth_controller, prefix=STANDARD_PREFIX)
app.state.limiter = limiter
app.include_router(files_controller, prefix=STANDARD_PREFIX)

@app.get("/ping")
async def ping():
    return {"message": "pong"}