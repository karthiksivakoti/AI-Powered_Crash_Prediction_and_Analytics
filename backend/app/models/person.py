# app/models/person.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    crash_id = Column(Integer, ForeignKey('crashes.id'))
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'))
    person_type = Column(String)
    injury_severity = Column(String)
    age = Column(Integer)
    gender = Column(String)
    safety_equipment = Column(String)
    
    crash = relationship("Crash", back_populates="persons")
    vehicle = relationship("Vehicle", back_populates="persons")