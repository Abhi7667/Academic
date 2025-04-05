import sqlite3
from tabulate import tabulate

def view_table(table_name):
    # Connect to database
    conn = sqlite3.connect('instance/database.db')
    cursor = conn.cursor()
    
    # Get all data from table
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    # Get column names
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Print table
    print(f"\n=== {table_name} Table ===")
    print(tabulate(rows, headers=columns, tablefmt='grid'))
    
    conn.close()

def main():
    # Updated table names to match SQLAlchemy model definitions
    tables = ['users', 'students', 'teachers', 'subjects', 'timetables', 'performances', 'notifications']
    
    for table in tables:
        try:
            view_table(table)
        except sqlite3.OperationalError as e:
            print(f"Error viewing {table}: {e}")

if __name__ == "__main__":
    main()