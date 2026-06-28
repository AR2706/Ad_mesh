import os
import certifi
import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# --- MongoDB Setup (Persistent Storage) ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URI, tlsCAFile=certifi.where())
database = client.admesh_db
user_collection = database.get_collection("users")
rule_collection = database.get_collection("rules")

# --- Redis Setup (High-Speed Data Plane) ---
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def test_connection():
    try:
        await client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")
        
        await redis_client.ping()
        print("✅ Successfully connected to Redis Cache!")
    except Exception as e:
        print(f"❌ Database/Cache connection failed: {e}")