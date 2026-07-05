from fastapi import FastAPI
from db import Base, SessionLocal
from sqlalchemy import text
from models import Asset
from services import AssetService
from tools import get_due_assets_tool
from agents import DeviceAgent, AssignmentAgent, EmailAgent

def run_pipeline():

    db = SessionLocal()

    device_agent = DeviceAgent()
    assignment_agent = AssignmentAgent()
    email_agent = EmailAgent()

    # 1. devices
    device_result = device_agent.run()
    tasks = device_result["tasks"]

    # 2. assignment
    enriched_tasks = assignment_agent.enrich_tasks(tasks)

    # 3. email
    emails = email_agent.build_emails(enriched_tasks)

    print("\n📧 Generated Emails:")
    for e in emails[:1]:
        print(e)


if __name__ == "__main__":
    run_pipeline()
# app = FastAPI()
# app.include_router(base.base_router)