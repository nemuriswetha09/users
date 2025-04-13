from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .database import collection
from .schemas import EmployeeIn
from .utils import generate_random_password, hash_password, generate_username
import csv
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/add-employee")
async def add_employee(emp: EmployeeIn):
    username = generate_username(emp.e_name, emp.e_id)
    plain_password = generate_random_password()
    hashed_pw = hash_password(plain_password)

    doc = emp.model_dump()
    doc["username"] = username
    doc["password"] = hashed_pw
    doc["plain_password"] = plain_password

    # await collection.insert_one(doc)
    result = await collection.insert_one(doc)
    print("Inserted ID:", result.inserted_id) 

    return {
        "message": "Employee added successfully",
        "employee_summary": {
            "e_id": emp.e_id,
            "e_name": emp.e_name,
            "email": emp.email,
            "userStatus": emp.userStatus,
            "Username": username,
            "Password": plain_password,
        }
    }

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))

    added, failed = 0, 0
    summaries = []

    for row in reader:
        try:
            emp = EmployeeIn(**row)
            username = generate_username(emp.e_name, emp.e_id)
            plain_password = generate_random_password()
            hashed_pw = hash_password(plain_password)

            doc = emp.model_dump()
            doc["username"] = username
            doc["password"] = hashed_pw
            doc["plain_password"] = plain_password

            await collection.insert_one(doc)

            summaries.append({
                "e_id": emp.e_id,
                "e_name": emp.e_name,
                "email": emp.email,
                "Username": username,
                "Password": plain_password,
            })
            added += 1
        except Exception as e:
            failed += 1
            continue

    return {
        "message": "CSV Upload Completed",
        "added": added,
        "failed": failed,
        "employee_summaries": summaries
    }

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