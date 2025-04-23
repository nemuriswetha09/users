import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from bson import Binary
import base64

# Load environment variables from .env file
load_dotenv()

# Get Mongo URI from .env
mongo_uri = os.getenv("MONGO_URI")

# Async function to update passwords
async def update_passwords():
    client = AsyncIOMotorClient(mongo_uri)
    db = client["testRaider"]
    collection = db["testUsers"]

    employees = [
        {"e_name": "Priyanshu Shrikrushna Rangari", "e_id": 240705, "password": "new_password_1"},
        {"e_name": "Gurram Kumara Swami", "e_id": 231008, "password": "new_password_2"}
    ]

    # Iterate over employees and update their passwords
    for emp in employees:
        # Find employee by E_Name (strip whitespace) and E_ID (ensure it's an integer)
        existing = await collection.find_one({
            "E_Name": emp["e_name"].strip(),
            "E_ID": int(emp["e_id"])  # Ensure E_ID is an integer
        })

        if existing:
            # Convert the password to Binary (assuming password is stored as binary)
            base64_password = base64.b64encode(emp["password"].encode()).decode()

            # Update the password field with base64 encoded value
            result = await collection.update_one(
                {"_id": existing["_id"]},
                {"$set": {"password": Binary(base64_password.encode())}}  # Convert to Binary
            )

            print(f"Updated {emp['e_name']}: matched {result.matched_count}, modified {result.modified_count}")
        else:
            print(f"Employee not found: {emp['e_name']} with ID {emp['e_id']}")

# Main runner
if __name__ == "__main__":
    asyncio.run(update_passwords())
