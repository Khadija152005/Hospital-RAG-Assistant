from db import SessionLocal
from services import AssetService
from core import settings

def get_due_assets_tool():
    """
    Tool used by Device Agent to fetch assets due for maintenance.
    """

    db = SessionLocal()

    try:
        service = AssetService(db)

        assets = service.get_due_assets(
            reminder_days=settings.REMINDER_DAYS
        )

     
        return [
            asset.model_dump() for asset in assets
        ]

    finally:
        db.close()