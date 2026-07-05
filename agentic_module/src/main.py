from fastapi import FastAPI
from db import Base, SessionLocal
from sqlalchemy import text
from models import Asset
from services import AssetService
from tools import get_due_assets_tool
from agents import DeviceAgent, AssignmentAgent

def test_pipeline():

    db = SessionLocal()

    
    device_agent = DeviceAgent()
    device_result = device_agent.run()

    tasks = device_result["tasks"]

    # print("tasks", device_result)
    # print("\n📦 Device Agent Output (first 2):")
    # for t in tasks[:2]:
    #     print(t)

    # 2. Assignment Agent 
    assignment_agent = AssignmentAgent()

    enriched_tasks = assignment_agent.enrich_tasks(tasks)

    print("enriched_tasks", enriched_tasks)
    # for t in enriched_tasks[:2]:
    #     print(t)


if __name__ == "__main__":
    test_pipeline()
# app = FastAPI()
# app.include_router(base.base_router)