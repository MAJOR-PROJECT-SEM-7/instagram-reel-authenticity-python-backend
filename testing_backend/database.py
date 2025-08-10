# database.py
from pymongo import MongoClient
from core.config import settings

client = MongoClient(settings.MONGODB_URL)

db = client["internal_testing_tool"]
users_collection = db["users"]
tests_collection = db["tests"]
