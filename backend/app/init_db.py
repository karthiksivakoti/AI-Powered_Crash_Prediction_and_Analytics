# app/init_db.py
from app.db.database import engine
from app.models.base import Base
from app.models.crash import Crash
from app.models.vehicle import Vehicle
from app.models.person import Person
from sqlalchemy import text

def init_db():
    print("Creating database tables...")
    
    # Create PostGIS extension if it doesn't exist
    with engine.connect() as connection:
        connection.execute(text('CREATE EXTENSION IF NOT EXISTS postgis;'))
        connection.commit()
    
    print("Created PostGIS extension")
    
    # Create all tables
    Base.metadata.drop_all(bind=engine)  # Drop existing tables
    Base.metadata.create_all(bind=engine)  # Create tables fresh
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()