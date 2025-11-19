import os 
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

#load .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in .env")

#global engine object
engine = create_engine(DATABASE_URL, future=True)

def test_connection():
    """Running a simple query to verify DB Connectivity"""
    with engine.connect() as conn:
        return conn.execute(text("SELECT 1")).scalar_one()
