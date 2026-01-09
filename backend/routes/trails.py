from fastapi import APIRouter
from backend.db import get_db

router = APIRouter()
db = get_db()

# --------------------------------------------------
# Fast list endpoint (NO geometry)
# Used for sidebar, dropdowns, search
# --------------------------------------------------
@router.get("/trails")
def list_trails(region: str | None = None):
    query = {}
    if region:
        query["region"] = region

    return list(
        db.trails.find(
            query,
            {
                "_id": 0,
                "name": 1,
                "length_km": 1,
                "region": 1
            }
        )
    )


# --------------------------------------------------
# Names only (autocomplete / selectbox)
# --------------------------------------------------
@router.get("/trails/names")
def get_trail_names():
    return sorted(db.trails.distinct("name"))


# --------------------------------------------------
# Geometry ONLY for one trail (map view)
# --------------------------------------------------
@router.get("/trails/by-name/{trail_name}")
def get_trail_by_name(trail_name: str):
    return list(
        db.trails.find(
            {"name": trail_name},
            {
                "_id": 0,
                "geometry": 1,
                "length_km": 1,
                "name": 1
            }
        )
    )
