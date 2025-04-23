import random
import string
from passlib.context import CryptContext
import base64
from bson.binary import Binary

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_random_password(length: int = 10) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=length))

def hash_password(password: str) -> str:
    """
    Hash the password using bcrypt and return the hashed string.
    """
    return pwd_context.hash(password)

def generate_username(name: str, eid: int) -> str:
    """
    Generate a username by concatenating name and last 3 digits of employee ID.
    """
    return name.lower().replace(" ", "") + str(eid)[-3:]

def encode_password_to_base64(hashed_password: str) -> str:
    """
    Convert the hashed password to Base64 binary format.
    """
    return base64.b64encode(hashed_password.encode('utf-8')).decode('utf-8')
# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Generate a random plain password
def generate_random_password(length: int = 10) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=length))

# Hash the password using bcrypt
def hash_password(password: str) -> str:
    return pwd_context.hash(password)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_random_password(length: int = 10) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=length))

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def is_binary_password(pw):
    try:
        if isinstance(pw, Binary):
            return True
        base64.b64decode(pw)
        return False
    except Exception:
        return False
