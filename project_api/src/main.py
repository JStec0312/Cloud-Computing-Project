import fastapi
from src.api.routers.auth import limiter, router as auth_controller
from src.api.routers.files import router as files_controller
from src.config.logging import configure_logging
from fastapi import FastAPI
configure_logging("DEBUG")
STANDARD_PREFIX = "/api/v1"
app = FastAPI(title = "Cloud drive")
app.include_router(auth_controller, prefix=STANDARD_PREFIX)
app.state.limiter = limiter
app.include_router(files_controller, prefix=STANDARD_PREFIX)
# @TODO SPRAWDZIC JAK DZIALA AUTO AUTH I DODAC DO PLIKOW KTOREGO TO DOTYCZY
@app.get("/ping")
async def ping():
    return {"message": "pong"}