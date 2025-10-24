import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Get the database URL from the environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("No DATABASE_URL found in .env file")

# Create the SQLAlchemy engine
# This is the main entry point to our database.
# The 'connect_args' is just for SQLite, but it's good practice.
# For MySQL, it's not strictly needed but doesn't hurt.
engine = create_engine(DATABASE_URL)

# Each instance of SessionLocal will be a new database session.
# Think of it as one conversation with your database.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# We will inherit from this Base class to create our database models (tables).
Base = declarative_base()

# Helper function to get a database session
# We'll use this in our API endpoints later
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()