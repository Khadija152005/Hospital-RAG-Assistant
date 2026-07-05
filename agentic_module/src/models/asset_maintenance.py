from sqlalchemy import Column, Text, Integer, Boolean, TIMESTAMP, ForeignKey, func, Date
from db import Base


class AssetMaintenance(Base):
    __tablename__ = "asset_maintenance"

    maintenance_id = Column(Integer, primary_key=True, autoincrement=True)

    asset_id = Column(Text, ForeignKey("asset.asset_id"), nullable=False)

    maintenance_date = Column(Date, nullable=False)

    next_maintenance_date = Column(Date)

    maintenance_type = Column(Text)

    performed_by = Column(Text, ForeignKey("staff.staff_id"))
