from fastapi import FastAPI
from src.api.auth import controller as auth_controller
app = FastAPI(title = "Cloud drive")

app.include_router(auth_controller.router)
