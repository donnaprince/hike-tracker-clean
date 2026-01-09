from fastapi import APIRouter
from backend.db import get_db

router = APIRouter(prefix="/api")

@router.get("/parks")
def get_parks():
    """
    Return a sorted list of National Park unit names (UNITNAME).
    """
    db = get_db()

    parks = db.trails.distinct("unit_name")

    # Remove null / empty values
    parks = [p for p in parks if p and p.strip()]

    return sorted(parks)
