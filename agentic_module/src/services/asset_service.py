from datetime import date, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy import func

from models import Asset, AssetMaintenance

from schemas import DueAsset



class AssetService:

    def __init__(self, db: Session):
        self.db = db
    
    def get_due_assets(self, reminder_days: int):

        # target_date = date.today() + timedelta(days=reminder_days)

        # temporary solution for testing purposes
        today = date.today()
        target_date = today + timedelta(days=reminder_days)
        overdue_limit = today - timedelta(days=0)
        # overdue_limit = today - timedelta(days=10)

        latest_maintenance = (
            self.db.query(
                AssetMaintenance.asset_id,
                func.max(AssetMaintenance.maintenance_date).label("latest_date"),
            )
            .group_by(AssetMaintenance.asset_id)
            .subquery()
        )

        assets = (
            self.db.query(
                Asset.asset_id,
                Asset.asset_name,
                Asset.asset_type,
                Asset.department,
                AssetMaintenance.next_maintenance_date,
            )
            .join(
                AssetMaintenance,
                Asset.asset_id == AssetMaintenance.asset_id,
            )
            .join(
                latest_maintenance,
                (AssetMaintenance.asset_id == latest_maintenance.c.asset_id)
                & (
                    AssetMaintenance.maintenance_date
                    == latest_maintenance.c.latest_date
                ),
            )
            .filter(
                # AssetMaintenance.next_maintenance_date <= target_date
                # temporary solution for testing purposes
                and_(
                    AssetMaintenance.next_maintenance_date <= target_date,
                    AssetMaintenance.next_maintenance_date >= overdue_limit,
                )
            )
            .all()
        )

        return [
            DueAsset(
                asset_id=row.asset_id,
                asset_name=row.asset_name,
                asset_type=row.asset_type,
                department=row.department,
                next_maintenance_date=row.next_maintenance_date,
            )
            for row in assets
        ]   
