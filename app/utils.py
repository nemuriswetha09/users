import random
import string
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_random_password(length: int = 10) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=length))

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def generate_username(name: str, eid: str) -> str:
    return name.lower().replace(" ", "") + str(eid)[-3:]