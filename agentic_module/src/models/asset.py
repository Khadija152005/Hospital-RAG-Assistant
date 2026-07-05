from sqlalchemy import Column, Text, Integer, Float, Date
from db import Base


class Asset(Base):
    __tablename__ = "asset"

    asset_id = Column(Text, primary_key=True)
    asset_name = Column(Text)
    asset_type = Column(Text)
    model = Column(Text)
    manufacturer = Column(Text)
    serial_number = Column(Text)
    department = Column(Text)

    purchase_date = Column(Date)
    purchase_cost = Column(Float)

    expected_lifetime_years = Column(Integer)
    calibration_interval_hours = Column(Integer)
    operating_hours = Column(Integer)