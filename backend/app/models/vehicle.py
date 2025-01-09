# app/models/vehicle.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    crash_id = Column(Integer, ForeignKey('crashes.id'))
    vehicle_type = Column(String)
    initial_impact = Column(String)
    damage_extent = Column(String)
    
    crash = relationship("Crash", back_populates="vehicles")
    persons = relationship("Person", back_populates="vehicle")