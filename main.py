from datetime import datetime
from io import StringIO
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from schemas import EmployeeIn
from database import collection
from utils import generate_password_from_name,convert_to_mongodb_binary, hash_password_bcrypt, generate_username
import pandas as pd
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI App Initialization
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create single employee record
async def create_employee(emp: EmployeeIn) -> dict:
    try:
        username = generate_username(emp.E_Name, emp.E_ID)
        
        # Check username uniqueness
        existing_user = await collection.find_one({"username": username})
        if existing_user:
            raise HTTPException(status_code=400, detail=f"Username {username} already exists")
        
        # Generate password using name_XXX format
        plain_password = generate_password_from_name(emp.E_Name)
        hashed_pw = hash_password_bcrypt(plain_password)
        encoded_password = convert_to_mongodb_binary(hashed_pw)

        doc = emp.dict()
        doc.update({
            "username": username,
            "password": encoded_password,
            "activeTimestamp": datetime.now().strftime("%d/%m/%Y, %I:%M:%S %p"),
            "currentDeviceID": "",
            "currentSession": ""
        })

        await collection.insert_one(doc)

        return {
            "E_ID": emp.E_ID,
            "E_Name": emp.E_Name,
            "email": emp.email,
            "userStatus": emp.userStatus,
            "Username": username,
            "Password": plain_password  # Returns the plain password for user reference
        }

    except HTTPException:
        # Re-raise HTTPException to preserve the status code and message
        raise
    except Exception as ex:
        logger.error(f"Error creating employee {emp.E_ID}: {ex}")
        raise HTTPException(status_code=500, detail="Internal server error while creating employee")

# Add employee via form
@app.post("/add-employee")
async def add_employee(emp: EmployeeIn):
    result = await create_employee(emp)
    return {
        "message": "Employee added successfully",
        "employee_summary": result
    }

# Bulk add via CSV
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
            "E_ID", "E_Name", "email", "address1", "address2",
            "role", "mobile", "altMobile", "latitude",
            "longitude", "physicalAddress", "userStatus"
        }

        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

        employee_summaries = []
        failed_rows = []

        for index, row in df.iterrows():
            try:
                employee_data = EmployeeIn(**row.to_dict())
                result = await create_employee(employee_data)
                employee_summaries.append(result)
            except Exception as e:
                logger.warning(f"Failed to process row {index + 1}: {e}")
                failed_rows.append({"row": index + 1, "error": str(e)})

        return {
            "message": "CSV processed",
            "employee_summaries": employee_summaries,
            "failed_rows": failed_rows
        }

    except Exception as e:
        logger.error(f"CSV Upload Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process CSV file")




# Forgot Password API
@app.post("/forgot-password")
async def forgot_password(
    E_Name: str = Body(..., embed=True),
    E_ID: int = Body(..., embed=True)
):
    E_Name_cleaned = " ".join(E_Name.strip().lower().split())

    employee = await collection.find_one({
        "E_Name": {"$regex": f"^{E_Name_cleaned}$", "$options": "i"},
        "E_ID": E_ID
    })

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    try:
        # Generate new password using name_XXX format (same name, new 3 digits)
        new_plain_password = generate_password_from_name(employee["E_Name"])
        hashed_password_bytes = hash_password_bcrypt(new_plain_password)
        base64_encoded_password = convert_to_mongodb_binary(hashed_password_bytes)

        await collection.update_one(
            {"_id": employee["_id"]},
            {"$set": {"password": base64_encoded_password}}
        )

        return {
            "message": "Password reset successfully.",
            "username": employee.get("username"),
            "new_plain_password": new_plain_password
        }
    except Exception as e:
        logger.error(f"Password reset failed for {E_Name} (ID: {E_ID}): {e}")
        raise HTTPException(status_code=500, detail="Failed to reset password")
 