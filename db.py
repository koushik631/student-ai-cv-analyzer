
import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parent / ".env")

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "student_cv_analyzer")

if not MONGO_URI:
    raise ValueError("MONGO_URI is missing from .env")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)

db = client[DB_NAME]

# Collections for the CV Analyzer
students = db["students"]
cv_analyses = db["cv_analyses"]


def test_connection():
    try:
        client.admin.command("ping")
        print("MongoDB connected successfully!")
        print("Database:", DB_NAME)

        # Insert one test document
        result = students.insert_one({
            "name": "Test Student",
            "email": "test@example.com",
            "purpose": "connection_test"
        })

        print("Test document inserted:", result.inserted_id)

        # Read it back
        print("Saved document:", students.find_one({
            "_id": result.inserted_id
        }))

    except Exception as error:
        print("MongoDB connection failed:", error)


if __name__ == "__main__":
    test_connection()
