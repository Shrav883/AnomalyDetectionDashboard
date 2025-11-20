import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Load .env file
load_dotenv()

DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not all([DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD]):
    raise RuntimeError("Database config missing in .env (DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD)")

# Build ODBC connection string
odbc_str = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_NAME};"
    f"UID={DB_USER};"
    f"PWD={DB_PASSWORD};"
    "TrustServerCertificate=yes;"
)

# URL-encode and build final SQLAlchemy URL
connection_url = f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_str)}"

# Create engine
engine = create_engine(connection_url, future=True)

def test_connection():
    """Simple DB health check."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, None
    except SQLAlchemyError as exc:
        return False, str(exc)
