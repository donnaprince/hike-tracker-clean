from fastapi import APIRouter
from datetime import datetime
from backend.db import get_db
from bson import ObjectId

router = APIRouter(prefix="/api/my-hikes", tags=["my-hikes"])


@router.post("")
def save_hike(hike: dict):
    """
    Save a completed hike.
    Expected fields: trail_name, length_km, time_hours
    """
    db = get_db()
    
    # Validate required fields
    if "trail_name" not in hike:
        return {"error": "trail_name is required"}
    if "length_km" not in hike:
        return {"error": "length_km is required"}
    if "time_hours" not in hike:
        return {"error": "time_hours is required"}
    
    hike_doc = {
        "trail_name": hike["trail_name"],
        "length_km": float(hike["length_km"]),
        "time_hours": float(hike["time_hours"]),
        "completed_at": datetime.utcnow(),
    }
    
    # Optional fields
    if "trail_id" in hike:
        hike_doc["trail_id"] = hike["trail_id"]
    if "notes" in hike:
        hike_doc["notes"] = hike["notes"]
    
    db.my_hikes.insert_one(hike_doc)
    return {"status": "saved", "hike": hike_doc}


@router.get("")
def get_my_hikes():
    """
    Get all logged hikes.
    Returns hikes with: trail_name, length_km, time_hours, completed_at
    """
    db = get_db()
    hikes = list(db.my_hikes.find(
        {},
        {"_id": 1, "trail_name": 1, "length_km": 1, "time_hours": 1, "completed_at": 1, "notes": 1}
    ))
    
    for h in hikes:
        h["_id"] = str(h["_id"])
        # Ensure all required fields exist
        if "trail_name" not in h:
            h["trail_name"] = "Unknown Trail"
        if "length_km" not in h:
            h["length_km"] = 0.0
        if "time_hours" not in h:
            h["time_hours"] = 0.0
    
    return hikes


@router.delete("/{hike_id}")
def delete_hike(hike_id: str):
    """Delete a logged hike by ID."""
    db = get_db()
    result = db.my_hikes.delete_one({"_id": ObjectId(hike_id)})
    
    if result.deleted_count == 0:
        return {"error": "Hike not found"}
    
    return {"status": "deleted"}
