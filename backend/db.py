import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI not set")

_client = MongoClient(MONGODB_URI)

def get_db():
    return _client["hiking"]   # 🔑 MUST MATCH ingest_trails.py
