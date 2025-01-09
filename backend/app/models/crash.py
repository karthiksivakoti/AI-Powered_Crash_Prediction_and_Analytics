# app/models/crash.py
from sqlalchemy import Column, Integer, Float, String, DateTime, func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from .base import Base

class Crash(Base):
    __tablename__ = "crashes"

    id = Column(Integer, primary_key=True, index=True)
    crn = Column(String, unique=True, index=True)
    crash_datetime = Column(DateTime, index=True)
    location = Column(Geometry('POINT'))
    county = Column(String)
    municipality = Column(String)
    hour_of_day = Column(Integer)
    weather = Column(String)
    road_condition = Column(String)
    severity = Column(String)
    fatal_count = Column(Integer, default=0)
    injury_count = Column(Integer, default=0)
    
    vehicles = relationship("Vehicle", back_populates="crash")
    persons = relationship("Person", back_populates="crash")