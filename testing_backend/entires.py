# routes/auth.py
from fastapi import APIRouter, HTTPException, Header, status, Body
from testing_backend.database import users_collection, tests_collection
from testing_backend.model import FinalResponse, EntryCreateRequest, EntrySummary
import bcrypt
from jose import jwt, JWTError
from core.config import settings
from datetime import datetime
from bson import ObjectId

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"

def middleware(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")
    token = authorization.split("Bearer ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user = users_collection.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return {"logged_in": True, "email": email}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")



router = APIRouter(prefix="/entries", tags=["Entries"])

@router.post("/create")
def create_entry(authorization: str = Header(...), entry: EntryCreateRequest = Body(...)):
    user_info = middleware(authorization)
    user_email = user_info["email"]
    
    # Create the entry document
    entry_doc = {
        "user_email": user_email,
        "worthy": entry.worthy,
        "feedback": entry.feedback.dict(),
        "response": entry.response.dict(),
        "insta_reel_id": entry.insta_reel_id,
        "created_at": datetime.utcnow()
    }
    
    # Insert into database
    result = tests_collection.insert_one(entry_doc)
    
    return {
        "message": "Entry created successfully",
        "entry_id": str(result.inserted_id)
    }

@router.get("/get")
def get_entries(authorization: str = Header(...)):
    user_info = middleware(authorization)
    user_email = user_info["email"]
    
    # Get all entries for the user with minimal details
    entries = list(tests_collection.find(
        {"user_email": user_email},
        {
            "_id": 1,
            "insta_reel_id": 1,
            "worthy": 1,
            "created_at": 1
        }
    ).sort("created_at", -1))  # Sort by creation date, newest first
    
    # Convert ObjectId to string for JSON serialization
    for entry in entries:
        entry["_id"] = str(entry["_id"])
    
    return {"entries": entries}

@router.get("/get/{entry_id}")
def get_entry_by_id(entry_id: str, authorization: str = Header(...)):
    user_info = middleware(authorization)
    user_email = user_info["email"]
    
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(entry_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid entry ID format")
    
    # Find the entry by ID and user email
    entry = tests_collection.find_one({
        "_id": object_id,
        "user_email": user_email
    })
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # Convert ObjectId to string for JSON serialization
    entry["_id"] = str(entry["_id"])
    
    return entry


