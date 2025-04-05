import sqlite3
from tabulate import tabulate

def view_users():
    # Connect to the database
    conn = sqlite3.connect('instance/database.db')
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute("""
        SELECT u.id, u.username, u.email, u.role, u.created_at,
               CASE 
                   WHEN u.role = 'student' THEN s.grade || ' - ' || s.roll_number
                   WHEN u.role = 'teacher' THEN t.department
                   ELSE 'N/A'
               END as details
        FROM users u
        LEFT JOIN students s ON u.id = s.user_id
        LEFT JOIN teachers t ON u.id = t.user_id
        ORDER BY u.created_at DESC
    """)
    
    users = cursor.fetchall()
    
    # Print users in a nice table format
    headers = ['ID', 'Username', 'Email', 'Role', 'Created At', 'Details']
    print("\nRegistered Users:")
    print(tabulate(users, headers=headers, tablefmt='grid'))
    
    conn.close()

if __name__ == "__main__":
    view_users() 