# bot/database.py
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

# These variables must be defined in your .env file
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME") # Reads the database name from .env


# --- 1️⃣ Database connection ---
def get_connection(db_name=None):
    """
    Connect to MySQL. If db_name is None, connect without selecting a database.
    """
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=db_name
        )
        return connection
    except Error as e:
        print(f"MySQL connection error: {e}")
        return None


# --- 2️⃣ Initialize database ---
def init_db():
    """
    Create the database if it doesn't exist, then create the grievances table.
    """
    try:
        # Step 1: Connect without selecting a database
        connection = get_connection()
        if connection is None:
            print("Could not initialize database: Failed to get connection.")
            return
        cursor = connection.cursor()

        # Step 2: Create database if not exists
        # This will use the DB_NAME specified in your .env file (now civic_grivances)
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        connection.commit()
        cursor.close()
        connection.close()

        # Step 3: Connect to the new database
        connection = get_connection(DB_NAME)
        if connection is None:
            print("Could not initialize database: Failed to connect to DB_NAME.")
            return
        cursor = connection.cursor()

        # Step 4: Create grievances table if not exists (UPDATED SCHEMA)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grievances (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT,
                username VARCHAR(255),
                grievance TEXT,
                issue VARCHAR(255) DEFAULT 'General complaint',
                location VARCHAR(255) DEFAULT 'unknown',
                photo_file_id VARCHAR(255) DEFAULT NULL,    -- New: Stores Telegram file_id for the photo
                additional_data TEXT DEFAULT NULL,          -- New: Stores data from conditional questions
                ai_reply VARCHAR(500) DEFAULT '',
                status VARCHAR(50) DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
        cursor.close()
        connection.close()

    except Error as e:
        print(f"Database initialization error: {e}")


# --- 3️⃣ Save grievance (UPDATED FUNCTION SIGNATURE) ---
def save_grievance(user_id, username, grievance, issue="General complaint", location="unknown", 
                   photo_file_id=None, additional_data=None, ai_reply=""):
    """
    Save a grievance into the MySQL database, now including optional photo_file_id and additional_data.
    """
    conn = get_connection(DB_NAME)
    if conn is None:
        print("Failed to connect to database for saving grievance.")
        return
    cursor = conn.cursor(dictionary=True)

    query = """
    INSERT INTO grievances (user_id, username, grievance, issue, location, photo_file_id, additional_data, ai_reply, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Pending')
    """
    # Note: additional_data can be None, which is fine for MySQL TEXT column
    try:
        cursor.execute(query, (user_id, username, grievance, issue, location, photo_file_id, additional_data, ai_reply))
        conn.commit()
    except Error as e:
        print(f"Error saving grievance to database: {e}")
    finally:
        cursor.close()
        conn.close()


# --- 4️⃣ Get user grievances (UPDATED SELECT) ---
def get_status(user_id):
    """
    Retrieve grievances for a user.
    """
    connection = get_connection(DB_NAME)
    if connection is None:
        return []
    cursor = connection.cursor(dictionary=True)
    # Added photo_file_id and additional_data to SELECT query
    query = "SELECT id, grievance, issue, location, photo_file_id, additional_data, ai_reply, status, created_at FROM grievances WHERE user_id = %s ORDER BY id DESC"
    try:
        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()
        return rows
    except Error as e:
        print(f"Error fetching user status: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


