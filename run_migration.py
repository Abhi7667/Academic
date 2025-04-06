from app import app, db
from sqlalchemy import text
from models import Subject

def run_migration():
    with app.app_context():
        try:
            # Add type column if it doesn't exist
            db.session.execute(text('ALTER TABLE subjects ADD COLUMN type VARCHAR(20) NOT NULL DEFAULT "Theory"'))
            db.session.commit()
            print("Migration successful!")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("Column already exists")
            else:
                print(f"Error: {e}")

if __name__ == "__main__":
    run_migration()