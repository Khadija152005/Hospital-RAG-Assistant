from sqlalchemy import Column, Text
from db import Base


class Staff(Base):
    __tablename__ = "staff"

    staff_id = Column(Text, primary_key=True)
    full_name = Column(Text)
    email = Column(Text)
    role = Column(Text)
    department = Column(Text)