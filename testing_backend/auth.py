# routes/auth.py
from fastapi import APIRouter, HTTPException, Header, status
from testing_backend.database import users_collection
from testing_backend.model import UserCreate, UserLogin
import bcrypt
from jose import jwt, JWTError
from core.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
def register(user: UserCreate):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())
    users_collection.insert_one({"email": user.email, "password": hashed_pw})
    return {"msg": "User registered"}

@router.post("/login")
def login(user: UserLogin):
    db_user = users_collection.find_one({"email": user.email})
    if not db_user or not bcrypt.checkpw(user.password.encode("utf-8"), db_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    token = jwt.encode({"email": user.email}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token}

@router.get("/check-login")
def check_login(authorization: str = Header(...)):
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
