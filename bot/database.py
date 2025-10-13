# bot/database.py
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

# --- 1️⃣ Database connection ---
def get_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        return connection
    except Error as e:
        print(f"MySQL connection error: {e}")
        return None


# --- 2️⃣ Initialize database table ---
def init_db():
    connection = get_connection()
    if connection is None:
        return
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grievances (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT,
            username VARCHAR(255),
            grievance TEXT,
            issue VARCHAR(255) DEFAULT 'General complaint',
            location VARCHAR(255) DEFAULT 'unknown',
            ai_reply VARCHAR(500) DEFAULT '',
            status VARCHAR(50) DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    connection.commit()
    cursor.close()
    connection.close()


# --- 3️⃣ Save grievance ---
def save_grievance(user_id, username, grievance, issue="General complaint", location="unknown", ai_reply=""):
    """
    Save a grievance into the MySQL database.
    """
    conn = get_connection()
    if conn is None:
        print("Failed to connect to database.")
        return
    cursor = conn.cursor(dictionary=True)

    query = """
    INSERT INTO grievances (user_id, username, grievance, issue, location, ai_reply, status)
    VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
    """
    cursor.execute(query, (user_id, username, grievance, issue, location, ai_reply))
    conn.commit()
    cursor.close()
    conn.close()


# --- 4️⃣ Get user grievances ---
def get_status(user_id):
    connection = get_connection()
    if connection is None:
        return []
    cursor = connection.cursor(dictionary=True)
    query = "SELECT id, grievance, issue, location, ai_reply, status, created_at FROM grievances WHERE user_id = %s ORDER BY id DESC"
    cursor.execute(query, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return rows
