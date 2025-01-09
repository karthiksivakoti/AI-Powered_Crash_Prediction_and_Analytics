# app/data_loader.py
import pandas as pd
import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from datetime import datetime
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from pathlib import Path
from app.db_init import Base, Crash, engine, SessionLocal

# Set up proper path handling
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / 'frontend' / 'public' / 'data'

# PA county centers for default coordinates
COUNTY_CENTERS = {
    '1': (40.9147, -77.8476),  # Centre County (roughly center of PA)
}

def safe_int(value, default=0):
    try:
        if pd.isna(value):
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default

def get_coordinates(row):
    """Get coordinates with fallback to county center"""
    try:
        lat = pd.to_numeric(row['DEC_LAT'], errors='coerce')
        lon = pd.to_numeric(row['DEC_LONG'], errors='coerce')
        
        if pd.notna(lat) and pd.notna(lon):
            if 39.0 <= lat <= 43.0 and -81.0 <= lon <= -74.0:
                return lat, lon, False
        
        county = str(safe_int(row['COUNTY'], 1))
        default_lat, default_lon = COUNTY_CENTERS.get(county, (40.9147, -77.8476))
        return default_lat, default_lon, True
        
    except Exception as e:
        print(f"Error processing coordinates: {e}")
        return 40.9147, -77.8476, True

def load_crash_data(db: Session):
    csv_path = DATA_DIR / 'CRASH_2023.csv'
    print(f"Loading data from: {csv_path}")
    
    if not csv_path.exists():
        print(f"Error: File not found at {csv_path}")
        return

    # Read the CSV file
    df = pd.read_csv(csv_path, low_memory=False)
    total_records = len(df)
    print(f"\nFound {total_records} records")

    processed = 0
    estimated = 0
    errors = 0
    batch_size = 1000
    current_batch = []

    for idx, row in df.iterrows():
        try:
            lat, lon, is_estimated = get_coordinates(row)
            
            if is_estimated:
                estimated += 1

            crash = Crash(
                crn=str(safe_int(row['CRN'])),
                crash_datetime=datetime(
                    year=safe_int(row['CRASH_YEAR'], 2023),
                    month=safe_int(row['CRASH_MONTH'], 1),
                    day=1,
                    hour=safe_int(row['HOUR_OF_DAY'], 0)
                ),
                location=from_shape(Point(lon, lat), srid=4326),
                county=str(safe_int(row['COUNTY'])),
                municipality=str(safe_int(row['MUNICIPALITY'])),
                hour_of_day=safe_int(row['HOUR_OF_DAY'], 0),
                weather=str(safe_int(row['WEATHER1'])),
                road_condition=str(safe_int(row['ROAD_CONDITION'])),
                severity='FATAL' if safe_int(row['FATAL_COUNT']) > 0 
                        else 'INJURY' if safe_int(row['INJURY_COUNT']) > 0 
                        else 'PDO',
                fatal_count=safe_int(row['FATAL_COUNT']),
                injury_count=safe_int(row['INJURY_COUNT']),
                estimated_location=is_estimated
            )
            
            current_batch.append(crash)
            processed += 1

            # Commit in batches
            if len(current_batch) >= batch_size:
                db.bulk_save_objects(current_batch)
                db.commit()
                current_batch = []
                print(f"Processed {processed} records (Estimated: {estimated}, Errors: {errors})")

        except Exception as e:
            errors += 1
            print(f"Error processing record {idx}: {str(e)}")
            db.rollback()
            continue

    # Commit any remaining records
    if current_batch:
        try:
            db.bulk_save_objects(current_batch)
            db.commit()
        except Exception as e:
            print(f"Error in final commit: {e}")
            db.rollback()

    print(f"\nFinal Statistics:")
    print(f"Total records: {total_records}")
    print(f"Successfully processed: {processed}")
    print(f"With estimated locations: {estimated}")
    print(f"Errors: {errors}")
    print(f"Success rate: {(processed/total_records)*100:.2f}%")

def main():
    db = SessionLocal()
    try:
        print("Starting data loading process...")
        load_crash_data(db)
        print("Data loading completed!")
    finally:
        db.close()

if __name__ == "__main__":
    main()