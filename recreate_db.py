import os
from app import app
from extensions import db
from models import User, Teacher, Student, Subject, Timetable, Performance, Notification

# This script will recreate the database with the updated schema
# Warning: This will delete all existing data!

def recreate_database():
    print("Starting database recreation process...")
    
    with app.app_context():
        # Get database path
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        print(f"Using database: {db_uri}")
        
        # Drop all tables
        print("Dropping all existing tables...")
        db.drop_all()
        print("All tables dropped successfully.")
        
        # Create all tables with the updated schema
        print("Creating tables with updated schema...")
        db.create_all()
        print("Tables created successfully.")
        
        # Create default admin user if needed
        admin_exists = User.query.filter_by(role='admin').first()
        
        if not admin_exists:
            print("Creating default admin user...")
            admin = User(
                username="admin",
                email="admin@example.com",
                role="admin",
                is_active=True
            )
            admin.set_password("admin123")  # Set a default password
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created.")
        
        print("Database recreation completed successfully!")

if __name__ == "__main__":
    # Ask for confirmation
    response = input("This will delete all existing data. Are you sure? (y/n): ")
    
    if response.lower() == 'y':
        recreate_database()
    else:
        print("Operation cancelled.") 