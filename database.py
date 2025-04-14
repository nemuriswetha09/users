from dotenv import load_dotenv
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables from .env file
load_dotenv()

# Get Mongo URI from .env
mongo_uri = os.getenv("MONGO_URI")

# Validate URI
if not mongo_uri:
    raise ValueError("MONGO_URI not found in .env file")

# Try connecting to MongoDB
try:
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongo_uri)

    # Use your actual DB and collection names below
    db = client["testRaider"]
    collection = db["testUsers"]

    # Check MongoDB server info to confirm connection
    client.server_info()  # Will throw an exception if connection fails
    print("MongoDB connection successful!")

except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
