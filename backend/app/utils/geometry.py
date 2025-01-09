# app/utils/geometry.py
from typing import List, Tuple, Dict
import numpy as np
from sqlalchemy import func, text
from geoalchemy2.functions import ST_Transform, ST_DWithin, ST_Distance, ST_Buffer
from geoalchemy2.elements import WKTElement
from app.models.crash import Crash  # Updated import path
from shapely.geometry import Point, Polygon
from datetime import datetime, timedelta

def create_hex_grid(bounds: Tuple[float, float, float, float], cell_size_km: float = 1.0) -> List[Dict]:
    """
    Create a hexagonal grid over the specified bounds.
    
    Args:
        bounds: (min_lon, min_lat, max_lon, max_lat)
        cell_size_km: Size of hexagon in kilometers
        
    Returns:
        List of hexagon polygons in GeoJSON format
    """
    min_lon, min_lat, max_lon, max_lat = bounds
    
    # Convert km to degrees (approximate)
    dx = cell_size_km / 111.0  # 111km per degree at equator
    dy = dx * np.cos(np.radians(min_lat))  # Adjust for latitude
    
    # Calculate grid size
    cols = int((max_lon - min_lon) / dx) + 1
    rows = int((max_lat - min_lat) / dy) + 1
    
    hexagons = []
    
    for row in range(rows):
        for col in range(cols):
            # Calculate center point
            center_x = min_lon + col * dx + (0.5 * dx if row % 2 else 0)
            center_y = min_lat + row * dy
            
            # Create hexagon vertices
            angles = np.linspace(0, 360, 7)[:-1]  # 6 points, remove last to avoid duplicate
            vertices = []
            for angle in angles:
                rad = np.radians(angle)
                x = center_x + dx/2 * np.cos(rad)
                y = center_y + dy/2 * np.sin(rad)
                vertices.append((x, y))
            
            hexagon = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [vertices + [vertices[0]]]  # Close polygon
                },
                'properties': {
                    'row': row,
                    'col': col,
                    'center': [center_x, center_y]
                }
            }
            hexagons.append(hexagon)
    
    return hexagons

def calculate_hotspots(db_session, start_date: datetime = None, end_date: datetime = None, 
                      min_crashes: int = 3, radius_meters: float = 500) -> List[Dict]:
    """
    Calculate crash hotspots using spatial clustering and temporal analysis.
    
    Args:
        db_session: SQLAlchemy database session
        start_date: Start date for analysis
        end_date: End date for analysis
        min_crashes: Minimum number of crashes to consider a hotspot
        radius_meters: Radius for spatial clustering in meters
        
    Returns:
        List of hotspots with risk scores and contributing factors
    """
    query = db_session.query(
        Crash.location,
        func.count(Crash.id).label('crash_count'),
        func.sum(Crash.fatal_count).label('fatal_count'),
        func.sum(Crash.injury_count).label('injury_count'),
        func.array_agg(Crash.weather).label('weather_conditions'),
        func.array_agg(Crash.road_condition).label('road_conditions'),
        func.array_agg(Crash.hour_of_day).label('hours'),
    )
    
    if start_date:
        query = query.filter(Crash.crash_datetime >= start_date)
    if end_date:
        query = query.filter(Crash.crash_datetime <= end_date)
    
    # Group crashes within spatial proximity
    query = query.group_by(
        func.ST_SnapToGrid(Crash.location, radius_meters)
    ).having(func.count(Crash.id) >= min_crashes)
    
    results = query.all()
    
    hotspots = []
    for result in results:
        # Extract coordinates
        point = f"SRID=4326;{result.location}"
        coords = db_session.query(
            func.ST_X(func.ST_Transform(point, 4326)),
            func.ST_Y(func.ST_Transform(point, 4326))
        ).first()
        
        # Calculate risk score
        base_score = result.crash_count
        severity_multiplier = (result.fatal_count * 3 + result.injury_count * 2) / result.crash_count
        
        hotspots.append({
            'location': {
                'type': 'Point',
                'coordinates': [coords[0], coords[1]]
            },
            'crash_count': result.crash_count,
            'risk_score': base_score * severity_multiplier,
            'fatal_count': result.fatal_count,
            'injury_count': result.injury_count,
            'weather_patterns': analyze_patterns(result.weather_conditions),
            'road_conditions': analyze_patterns(result.road_conditions),
            'time_patterns': analyze_time_patterns(result.hours)
        })
    
    return hotspots

def analyze_patterns(values: List[str]) -> Dict:
    """Analyze patterns in categorical values"""
    if not values:
        return {}
        
    counts = {}
    total = len(values)
    for val in values:
        if val:
            counts[val] = counts.get(val, 0) + 1
            
    return {k: v/total for k, v in counts.items()}

def analyze_time_patterns(hours: List[int]) -> Dict:
    """Analyze temporal patterns in crash times"""
    if not hours:
        return {}
        
    periods = {
        'morning': 0,   # 6-10
        'midday': 0,    # 10-14
        'afternoon': 0, # 14-18
        'evening': 0,   # 18-22
        'night': 0      # 22-6
    }
    
    total = len(hours)
    for hour in hours:
        if 6 <= hour < 10:
            periods['morning'] += 1
        elif 10 <= hour < 14:
            periods['midday'] += 1
        elif 14 <= hour < 18:
            periods['afternoon'] += 1
        elif 18 <= hour < 22:
            periods['evening'] += 1
        else:
            periods['night'] += 1
            
    return {k: v/total for k, v in periods.items()}