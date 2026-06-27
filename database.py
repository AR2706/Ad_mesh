import os
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

# Fetch the URI, fallback to a local instance if not found
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# Initialize the async Motor client and explicitly pass the SSL certificates
client = AsyncIOMotorClient(MONGO_URI, tlsCAFile=certifi.where())

# Define the database and the two core collections
database = client.admesh_db
user_collection = database.get_collection("users")
rule_collection = database.get_collection("rules")

async def test_connection():
    """Ping the database to ensure the connection is active."""
    try:
        await client.admin.command('ping')
        print("Successfully connected to MongoDB Atlas!")
    except Exception as e:
        print(f"Database connection failed: {e}")