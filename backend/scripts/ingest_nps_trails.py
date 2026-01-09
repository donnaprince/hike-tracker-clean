"""
Ingest National Park Service (NPS) Trails dataset into MongoDB.

This script:
- Reads NPS Trails shapefile/GeoJSON
- Computes length_km from geometry at load time
- Stores trails with schema: name, alt_name, notes, length_km, geometry, state
- Fails loudly if required fields (TRLNAME) are missing
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, Point
from geopy.distance import geodesic
from backend.db import get_db


# Configuration
NPS_TRAILS_PATH = "backend/data/NPS_Trails_A.shp"


def compute_length_km(geometry) -> float:
    """
    Compute trail length in kilometers from geometry.
    Uses WGS84 ellipsoid for accurate distance calculation.
    """
    if geometry is None:
        raise ValueError("Geometry is None - cannot compute length")
    
    if not isinstance(geometry, LineString):
        raise ValueError(f"Expected LineString, got {type(geometry)}")
    
    # Use geodesic distance for accurate km calculation
    coords = list(geometry.coords)
    if len(coords) < 2:
        return 0.0
    
    total_km = 0.0
    for i in range(len(coords) - 1):
        p1 = Point(coords[i])
        p2 = Point(coords[i + 1])
        # Convert to (lat, lon) for geopy
        distance = geodesic(
            (p1.y, p1.x),  # lat, lon
            (p2.y, p2.x)
        ).kilometers
        total_km += distance
    
    return total_km


def ingest_nps_trails():
    """
    Ingest NPS Trails dataset into MongoDB.
    Fails loudly if required fields are missing.
    """
    print(f"Loading NPS Trails from: {NPS_TRAILS_PATH}")
    
    # Load shapefile
    try:
        gdf = gpd.read_file(NPS_TRAILS_PATH)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"NPS Trails file not found at {NPS_TRAILS_PATH}. "
            "Please ensure the NPS Trails shapefile is available."
        )
    
    print(f"Loaded {len(gdf)} trails from shapefile")
    print(f"Columns: {list(gdf.columns)}")
    
    # Verify required fields exist
    required_fields = ["TRLNAME"]
    missing_fields = [f for f in required_fields if f not in gdf.columns]
    if missing_fields:
        raise ValueError(
            f"Required fields missing from shapefile: {missing_fields}. "
            f"Available fields: {list(gdf.columns)}"
        )
    
    # Reproject to WGS84 (EPSG:4326) if needed
    if gdf.crs != "EPSG:4326":
        print(f"Reprojecting from {gdf.crs} to EPSG:4326...")
        gdf = gdf.to_crs(epsg=4326)
    
    # Get database connection
    db = get_db()
    trails_collection = db.trails
    
    # Ensure spatial index exists
    try:
        trails_collection.create_index([("geometry", "2dsphere")])
        trails_collection.create_index([("state", 1)])
        print("Created indexes")
    except Exception as e:
        print(f"Index creation note: {e}")
    
    inserted = 0
    skipped = 0
    errors = []
    
    print("\nIngesting trails...")
    
    for idx, row in gdf.iterrows():
        try:
            # Required field - fail if missing
            name = row.get("TRLNAME")
            if not name or pd.isna(name):
                errors.append(f"Row {idx}: TRLNAME is missing or empty")
                skipped += 1
                continue
            
            # Optional fields
            alt_name = row.get("TRLALTNAME")
            if alt_name is None or (isinstance(alt_name, float) and pd.isna(alt_name)):
                alt_name = None
            else:
                alt_name = str(alt_name).strip()
            
            notes = row.get("NOTES")
            if notes is None or (isinstance(notes, float) and pd.isna(notes)):
                notes = None
            else:
                notes = str(notes).strip()
            
            # Extract state - may be in various fields
            state = None
            for state_field in ["STATE", "STATE_NAME", "STATE_ABBR"]:
                if state_field in gdf.columns:
                    state_val = row.get(state_field)
                    if not pd.isna(state_val):
                        state = str(state_val).strip()
                        break
            
            # Geometry
            geometry = row.geometry
            if geometry is None:
                errors.append(f"Row {idx} ({name}): Geometry is None")
                skipped += 1
                continue
            
            # Compute length_km at load time
            try:
                length_km = compute_length_km(geometry)
            except Exception as e:
                errors.append(f"Row {idx} ({name}): Failed to compute length: {e}")
                skipped += 1
                continue
            
            # Convert geometry to GeoJSON
            geometry_geojson = geometry.__geo_interface__
            
            # Create trail document
            trail_doc = {
                "name": str(name).strip(),
                "alt_name": alt_name.strip() if alt_name else None,
                "notes": notes.strip() if notes else None,
                "length_km": round(length_km, 2),  # Round to 2 decimal places
                "geometry": geometry_geojson,
                "state": state,
                "source": "nps_trails"
            }
            
            # De-duplication by name + geometry hash
            existing = trails_collection.find_one({
                "name": trail_doc["name"],
                "geometry": trail_doc["geometry"]
            })
            
            if existing:
                skipped += 1
                continue
            
            # Insert trail
            trails_collection.insert_one(trail_doc)
            inserted += 1
            
            if inserted % 100 == 0:
                print(f"  Inserted {inserted} trails...")
        
        except Exception as e:
            errors.append(f"Row {idx}: {str(e)}")
            skipped += 1
            continue
    
    print(f"\n✅ Inserted {inserted} trails")
    print(f"⏭️  Skipped {skipped} trails (duplicates or errors)")
    print(f"Total trails in database: {trails_collection.count_documents({})}")
    
    if errors:
        print(f"\n⚠️  {len(errors)} errors encountered:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")


if __name__ == "__main__":
    ingest_nps_trails()

