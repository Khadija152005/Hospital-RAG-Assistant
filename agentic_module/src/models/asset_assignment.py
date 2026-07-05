from sqlalchemy import Column, Text, Integer, Boolean, TIMESTAMP, ForeignKey, func
from db import Base


class AssetAssignment(Base):
    __tablename__ = "asset_assignment"

    assignment_id = Column(Integer, primary_key=True, autoincrement=True)

    asset_id = Column(Text, ForeignKey("asset.asset_id"), nullable=False)
    staff_id = Column(Text, ForeignKey("staff.staff_id"), nullable=False)
