from fastapi import FastAPI
from src.api.routers.auth import router as auth_controller
app = FastAPI(title = "Cloud drive")

app.include_router(auth_controller)
