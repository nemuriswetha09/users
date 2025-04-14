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

# Forgot password endpoint
@app.post("/forgot-password")
async def forgot_password(e_name: str, e_id: int):
    employee = await collection.find_one({"e_name": e_name, "e_id": e_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    return {
        "message": "Password retrieved successfully",
        "username": employee.get("username"),
        "plain_password": employee.get("plain_password")
    }
