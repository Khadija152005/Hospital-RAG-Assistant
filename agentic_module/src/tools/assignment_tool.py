from db import SessionLocal
from services import AssignmentService


def get_assignment_tool(asset_id: str):

    db = SessionLocal()

    try:
        service = AssignmentService(db)
        return service.get_assignment_with_staff(asset_id)

    finally:
        db.close()