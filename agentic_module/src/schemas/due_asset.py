from pydantic import BaseModel
from datetime import date


class DueAsset(BaseModel):

    asset_id: str

    asset_name: str

    asset_type: str

    department: str

    next_maintenance_date: date