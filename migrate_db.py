import sqlite3
import os
from app import app

# Get the database path from the app config
with app.app_context():
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    print(f"Database URI: {db_uri}")
    
    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.replace('sqlite:///', '')
    else:
        # Handle the case where it's a relative path
        db_path = db_uri.replace('sqlite://', '')
        
    print(f"Extracted database path: {db_path}")
    
    # Handle relative path if needed
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.getcwd(), db_path)
        print(f"Absolute database path: {db_path}")
    
    # Verify the file exists
    if not os.path.exists(db_path):
        print(f"WARNING: Database file not found at {db_path}")
    else:
        print(f"Database file found: {db_path}")

print(f"Migrating database at: {db_path}")

try:
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if column exists
    cursor.execute("PRAGMA table_info(users)")
    columns_info = cursor.fetchall()
    print(f"Current table columns: {columns_info}")
    
    columns = [info[1] for info in columns_info]
    
    if 'is_active' not in columns:
        print("Adding is_active column to users table...")
        # Add the is_active column with a default value of 1 (True)
        cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
        print("Column added successfully!")
    else:
        print("Column is_active already exists.")
    
    # Commit the transaction
    conn.commit()
    print("Migration completed successfully!")

except Exception as e:
    print(f"Migration failed: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    # Close the connection if it was opened
    if 'conn' in locals() and conn:
        conn.close() 