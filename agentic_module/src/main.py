from fastapi import FastAPI
from db import Base, SessionLocal
from sqlalchemy import text
from models import Asset
from services import AssetService
from tools import get_due_assets_tool
from agents import DeviceAgent

def test():
    agent = DeviceAgent()

    result = agent.run()

    print(result)


if __name__ == "__main__":
    test()

# app = FastAPI()
# app.include_router(base.base_router)