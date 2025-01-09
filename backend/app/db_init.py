# app/db_init.py
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import Geometry
import os

# Database connection
DATABASE_URL = "postgresql://postgres:your_password@localhost:5432/crash_analytics"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

class Crash(Base):
    __tablename__ = "crashes"

    id = Column(Integer, primary_key=True, index=True)
    crn = Column(String, unique=True, index=True)
    crash_datetime = Column(DateTime, index=True)
    location = Column(Geometry('POINT', srid=4326))
    county = Column(String)
    municipality = Column(String)
    hour_of_day = Column(Integer)
    weather = Column(String)
    road_condition = Column(String)
    severity = Column(String)
    fatal_count = Column(Integer, default=0)
    injury_count = Column(Integer, default=0)
    estimated_location = Column(Boolean, default=False)

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database tables created!")