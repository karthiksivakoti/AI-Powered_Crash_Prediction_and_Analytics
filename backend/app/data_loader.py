# app/data_loader.py
import pandas as pd
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from datetime import datetime
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from pathlib import Path
from app.models.crash import Crash
from app.models.vehicle import Vehicle
from app.models.person import Person
from app.models.base import Base
from app.db.database import engine, SessionLocal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the project root directory and data directory
ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / 'frontend' / 'public' / 'data'

def safe_int(value, default=0):
    try:
        if pd.isna(value):
            return default
        val = int(float(value))
        return val
    except (ValueError, TypeError):
        return default

def validate_hour(hour):
    """Validate and fix hour value"""
    if pd.isna(hour):
        return 0
    
    try:
        hour = int(float(hour))
        if 0 <= hour <= 23:
            return hour
        elif hour == 24:  # Special case for midnight
            return 0
        elif hour > 24:  # Invalid hours
            return hour % 24  # Convert to 24-hour format
        else:
            return 0  # Default to midnight for negative values
    except (ValueError, TypeError):
        return 0

def get_coordinates(row):
    """Get coordinates with fallback to county center"""
    try:
        lat = pd.to_numeric(row['DEC_LAT'], errors='coerce')
        lon = pd.to_numeric(row['DEC_LONG'], errors='coerce')
        
        if pd.notna(lat) and pd.notna(lon):
            if 39.0 <= lat <= 43.0 and -81.0 <= lon <= -74.0:
                return lat, lon, False
        
        # Default to county center or PA center
        return 40.9147, -77.8476, True
        
    except Exception as e:
        print(f"Error processing coordinates: {e}")
        return 40.9147, -77.8476, True

def process_chunk(chunk, db: Session):
    """Process a chunk of records"""
    records = []
    skipped = 0
    for idx, row in chunk.iterrows():
        try:
            lat, lon, is_estimated = get_coordinates(row)
            hour = validate_hour(row['HOUR_OF_DAY'])
            
            crash = Crash(
                crn=str(safe_int(row['CRN'])),
                crash_datetime=datetime(
                    year=safe_int(row['CRASH_YEAR'], 2023),
                    month=safe_int(row['CRASH_MONTH'], 1),
                    day=1,
                    hour=hour
                ),
                location=from_shape(Point(lon, lat), srid=4326),
                county=str(safe_int(row['COUNTY'])),
                municipality=str(safe_int(row['MUNICIPALITY'])),
                hour_of_day=hour,
                weather=str(safe_int(row['WEATHER1'])),
                road_condition=str(safe_int(row['ROAD_CONDITION'])),
                severity='FATAL' if safe_int(row['FATAL_COUNT']) > 0 
                        else 'INJURY' if safe_int(row['INJURY_COUNT']) > 0 
                        else 'PDO',
                fatal_count=safe_int(row['FATAL_COUNT']),
                injury_count=safe_int(row['INJURY_COUNT']),
                estimated_location=is_estimated
            )
            records.append(crash)
            
        except Exception as e:
            print(f"Error processing record {idx}: {str(e)}")
            skipped += 1
            continue
    
    if records:
        try:
            db.bulk_save_objects(records)
            db.commit()
            return len(records), sum(1 for r in records if r.estimated_location), skipped
        except Exception as e:
            print(f"Error saving batch: {str(e)}")
            db.rollback()
            return 0, 0, skipped
    return 0, 0, skipped

def load_crash_data(db: Session):
    csv_path = DATA_DIR / 'CRASH_2023.csv'
    print(f"Loading data from: {csv_path}")
    
    if not csv_path.exists():
        print(f"Error: File not found at {csv_path}")
        return

    # Smaller chunk size to prevent memory issues
    chunk_size = 50
    total_processed = 0
    total_estimated = 0
    total_skipped = 0

    print(f"\nProcessing data in chunks of {chunk_size} records")
    print(f"Reading from: {csv_path}")
    
    try:
        # First, count total rows
        total_rows = sum(1 for _ in open(csv_path)) - 1  # subtract 1 for header
        print(f"Total rows in CSV: {total_rows}")
        
        for chunk_number, chunk in enumerate(pd.read_csv(csv_path, chunksize=chunk_size, low_memory=False)):
            processed, estimated, skipped = process_chunk(chunk, db)
            total_processed += processed
            total_estimated += estimated
            total_skipped += skipped
            
            # Print progress every 1000 records
            if chunk_number % 20 == 0:
                progress = (total_processed / total_rows) * 100
                print(f"Progress: {progress:.2f}% | Processed: {total_processed} | Estimated: {total_estimated} | Skipped: {total_skipped}")
                
            # Commit every 1000 records
            if chunk_number % 20 == 0:
                db.commit()

        print(f"\nFinal Statistics:")
        print(f"Successfully processed: {total_processed}")
        print(f"With estimated locations: {total_estimated}")
        print(f"Skipped records: {total_skipped}")
        print(f"Success rate: {(total_processed/total_rows)*100:.2f}%")
        
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        db.rollback()
        return
    finally:
        db.commit()

def main():
    print("Checking data directory...")
    print(f"Data directory path: {DATA_DIR}")
    print(f"Data directory exists: {DATA_DIR.exists()}")
    
    if DATA_DIR.exists():
        print(f"Contents of data directory: {[x.name for x in DATA_DIR.iterdir() if x.is_file()]}")
    
    db = SessionLocal()
    try:
        print("\nStarting data loading process...")
        load_crash_data(db)
        print("Data loading completed!")
    finally:
        db.close()

if __name__ == "__main__":
    main()