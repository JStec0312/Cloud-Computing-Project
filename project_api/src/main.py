from fastapi import FastAPI
from src.api.routers.auth import router as auth_controller
from src.api.routers.files import router as files_controller
from src.config.logging import configure_logging
configure_logging("DEBUG")
app = FastAPI(title = "Cloud drive")

app.include_router(auth_controller)
app.include_router(files_controller)
# @TODO SPRAWDZIC JAK DZIALA AUTO AUTH I DODAC DO PLIKOW KTOREGO TO DOTYCZY
@app.get("/ping")
async def ping():
    return {"message": "pong"}