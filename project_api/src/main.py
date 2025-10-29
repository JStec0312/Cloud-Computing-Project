from fastapi import FastAPI
from src.api.routers.auth import router as auth_controller
from src.config.logging import configure_logging
configure_logging("DEBUG")
app = FastAPI(title = "Cloud drive")

app.include_router(auth_controller)
