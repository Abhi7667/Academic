import os

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL")

# If not provided, fallback to constructing from individual parameters
if not DATABASE_URL:
    db_user = os.environ.get("PGUSER", "postgres")
    db_password = os.environ.get("PGPASSWORD", "postgres")
    db_host = os.environ.get("PGHOST", "localhost")
    db_port = os.environ.get("PGPORT", "5432")
    db_name = os.environ.get("PGDATABASE", "academic_hub")
    
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# App configuration
class Config:
    SECRET_KEY = os.environ.get("SESSION_SECRET", "dev_key")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
