# app/db_init.py
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean
from geoalchemy2 import Geometry
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment variable or use default
DATABASE_URL = os.getenv(
    'DATABASE_URL', 
    "postgresql://postgres:postgres123@localhost:5432/crash_analytics"
)

# Create engine and session
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
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
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()