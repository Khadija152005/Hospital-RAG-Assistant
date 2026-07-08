from fastapi import FastAPI
from api import maintenance as maintenance_router
from core import config

app = FastAPI(
    title=config.settings.APP_TITLE,
    version=config.settings.APP_VERSION,
)

app.include_router(maintenance_router.router)

