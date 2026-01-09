from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId


class PyObjectId(ObjectId):
    """
    Custom ObjectId class for Pydantic compatibility.
    MongoDB uses ObjectId for document IDs, and this class helps
    Pydantic serialize/deserialize them properly.
    """
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class User(BaseModel):
    """
    User model for authentication and user management.
    Stores user email and hashed password for secure authentication.
    """
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    email: str = Field(..., description="User's email address")
    password_hash: str = Field(..., description="Hashed password for authentication")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Trail(BaseModel):
    """
    Trail model representing hiking trails.
    Includes trail details like name, distance, difficulty, region,
    and GeoJSON geometry for mapping purposes.
    """
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., description="Name of the trail")
    distance_miles: float = Field(..., gt=0, description="Trail distance in miles")
    difficulty: int = Field(..., ge=1, le=5, description="Trail difficulty rating (1-5)")
    region: str = Field(..., description="Geographic region where the trail is located")
    geometry: Dict[str, Any] = Field(..., description="GeoJSON geometry object for trail mapping")

    @field_validator('geometry')
    @classmethod
    def validate_geometry(cls, v):
        """Validate that geometry is a valid GeoJSON object."""
        if not isinstance(v, dict):
            raise ValueError("Geometry must be a dictionary")
        if 'type' not in v:
            raise ValueError("Geometry must have a 'type' field")
        return v

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class CompletedHike(BaseModel):
    """
    CompletedHike model tracking user's completed hikes.
    Links a user to a trail they've completed, with the date
    and their personal difficulty rating.
    """
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="Reference to the User who completed the hike")
    trail_id: PyObjectId = Field(..., description="Reference to the Trail that was completed")
    completed_date: datetime = Field(..., description="Date when the hike was completed")
    user_difficulty: int = Field(..., ge=1, le=5, description="User's personal difficulty rating (1-5)")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

