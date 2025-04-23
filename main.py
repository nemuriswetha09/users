import base64
from datetime import datetime
import random
from io import StringIO
from fastapi import FastAPI, File, UploadFile, HTTPException
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import EmployeeIn, EmployeeSummary
from database import collection
from utils import generate_random_password, hash_password, encode_password_to_base64, generate_username
from fastapi import HTTPException, Body
from fastapi import FastAPI, HTTPException, Body
from bson.binary import Binary
import base64
from passlib.context import CryptContext
import random
import string


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Function to create an employee
async def create_employee(emp: EmployeeIn):
    # Generate username
    username = generate_username(emp.e_name, emp.e_id)
    
    # Generate random password and hash it
    plain_password = generate_random_password()
    hashed_pw = hash_password(plain_password)

    # Convert the hashed password to Base64 binary format
    binary_encoded_password = encode_password_to_base64(hashed_pw)

    # Add active timestamp and device ID
    active_timestamp = datetime.now().strftime("%d/%m/%Y, %I:%M:%S %p")
    current_device_id = ""  # Placeholder for current device ID initially
    current_session = ""  # Placeholder for current session initially

    # Prepare document to insert into the database
    doc = emp.dict()  # Converts to dict to insert into MongoDB
    doc["username"] = username
    doc["password"] = binary_encoded_password  # Store the Base64-encoded password
    doc["activeTimestamp"] = active_timestamp
    doc["currentDeviceID"] = current_device_id  # Placeholder for device ID
    doc["currentSession"] = current_session  # Placeholder for session ID
    # doc["plain_password"] = None  # Do not store the plain password

    # Insert into MongoDB collection
    result = await collection.insert_one(doc)
    print("Inserted ID:", result.inserted_id)

    # Return employee summary (excluding plain password)
    return {
        "e_id": emp.e_id,
        "e_name": emp.e_name,
        "email": emp.email,
        "userStatus": emp.userStatus,
        "Username": username,
        "Password": plain_password,  # Only include plain password in the response for the user
    }

# Single employee endpoint
@app.post("/add-employee")
async def add_employee(emp: EmployeeIn):
    result = await create_employee(emp)
    return {
        "message": "Employee added successfully",
        "employee_summary": result  # Return employee summary
    }
#  CSV bulk upload endpoint
@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    try:
        contents = await file.read()
        file_str = contents.decode("utf-8")
        csv_file = StringIO(file_str)
        df = pd.read_csv(csv_file)

        required_columns = {
            "e_id", "e_name", "email", "address1", "address2",
            "role", "mobile", "altMobile", "latitude",
            "longitude", "physicalAddress", "userStatus"
        }

        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns in CSV: {missing}"
            )

        employee_summaries = []
        failed_rows = []

        for index, row in df.iterrows():
            try:
                employee_data = EmployeeIn(**row.to_dict())
                result = await create_employee(employee_data)
                employee_summaries.append(result)
            except Exception as e:
                failed_rows.append({"row": index + 1, "error": str(e)})

        return {
            "message": "CSV uploaded and processed successfully",
            "employee_summaries": employee_summaries,
            "failed_rows": failed_rows
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Function for validation
def is_valid_e_id(e_id: int) -> bool:
    return isinstance(e_id, int) and e_id > 0
 
 


# Initialize password context for bcrypt hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Function to generate random password
def generate_random_password(length: int = 10) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=length))

# Function to hash the password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Function to check if the password is in Base64 binary format
def is_binary_password(pw):
    try:
        if isinstance(pw, Binary):
            return True
        base64.b64decode(pw)
        return False
    except Exception:
        return False
# Password reset function
@app.post("/forgot-password")
async def forgot_password(e_name: str = Body(..., embed=True), e_id: int = Body(..., embed=True)):
    # Clean up the name input
    e_name = " ".join(e_name.strip().lower().split())

    # Simulate employee database lookup
    employee = await collection.find_one({
        "e_name": {"$regex": f"^{e_name}$", "$options": "i"},
        "e_id": e_id
    })

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Get the old password from the database
    old_password = employee.get("password")

    # Check if the old password is in Binary or Base64 format
    if isinstance(old_password, Binary) or is_binary_password(old_password):
        print("Old password is in Binary/Base64 format")

    # Generate a new plain password
    new_plain_password = generate_random_password()

    # Hash the new plain password
    new_hashed_password = hash_password(new_plain_password)

    # Update the employee's password with the new hashed password
    await collection.update_one(
        {"_id": employee["_id"]},
        {"$set": {"password": new_hashed_password}}
    )

    # Return the plain password to the user (be cautious about returning this in production)
    return {
        "message": "Password reset successfully.",
        "username": employee.get("username"),
        "new_plain_password": new_plain_password  # Make sure you know the risks of sending this in response
    }
