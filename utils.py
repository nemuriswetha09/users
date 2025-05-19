import random
import bcrypt
from bson.binary import Binary
def generate_password_from_name(E_Name: str) -> str:
    """Generate password in format: name_XXX where XXX is random 3 digits."""
    # Extract first name from full name
    name_parts =E_Name.strip().lower().split()
    first_name = name_parts[0] if name_parts else "user"
    
    # Generate random 3-digit number
    random_digits = random.randint(100, 999)
    
    return f"{first_name}_{random_digits}"
def hash_password_bcrypt(password: str) -> bytes:
    """Hash the password using bcrypt and return the bytes."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)


def convert_to_mongodb_binary(hashed_password: bytes) -> Binary:
    """Convert hashed password to MongoDB Binary format for secure storage."""
    return Binary(hashed_password)


def generate_username(E_Name: str, E_ID: int) -> str:
    """Generate a unique username based on employee's name and ID."""
    E_Name_cleaned = " ".join(E_Name.strip().lower().split())
    name_parts = E_Name_cleaned.split()
    first_name = name_parts[0] if name_parts else "user"
    return f"{first_name}{E_ID}".lower()
