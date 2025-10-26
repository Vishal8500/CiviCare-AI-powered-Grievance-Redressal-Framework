# ==========================================
# 🧩 bot/database.py  — Final Integrated Version
# ==========================================
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from priority_index import calculate_priority_index

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


# --------------------------------------------------
# 1️⃣ Connection Helper
# --------------------------------------------------
def get_connection(db_name=None):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=db_name
        )
        return conn
    except Error as e:
        print(f"MySQL connection error: {e}")
        return None


# --------------------------------------------------
# 2️⃣ Database Initialization
# --------------------------------------------------
def init_db():
    """
    Creates the database and grievances table if missing.
    """
    try:
        # Step 1: Create database if missing
        root_conn = get_connection()
        if root_conn is None:
            print("❌ Failed to connect to MySQL server.")
            return
        cur = root_conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        root_conn.commit()
        cur.close()
        root_conn.close()

        # Step 2: Connect to target DB
        conn = get_connection(DB_NAME)
        cur = conn.cursor()

        # Step 3: Create table (Latest Schema)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS grievances (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT,
                username VARCHAR(255),
                grievance TEXT,
                issue VARCHAR(255) DEFAULT 'General complaint',
                location VARCHAR(255) DEFAULT 'unknown',
                photo LONGBLOB,
                additional_data TEXT,
                ai_reply TEXT,
                sentiment_score FLOAT DEFAULT 0,
                keyword_severity FLOAT DEFAULT 0,
                frequency_score FLOAT DEFAULT 0,
                priority_index FLOAT DEFAULT 0,
                status VARCHAR(50) DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database initialized successfully.")
    except Error as e:
        print(f"Database initialization error: {e}")


# --------------------------------------------------
# 3️⃣ Save Grievance (Handles both File object and bytes)
# --------------------------------------------------
import traceback

async def save_grievance(user_id, username, grievance,
                         issue="General complaint", location="unknown",
                         photo_file=None, additional_data=None, ai_reply=""):
    """
    Saves grievance data with optional photo (BLOB) and AI-based priority metrics.
    Works safely with both Telegram File objects and already-downloaded bytes.
    """
    conn = get_connection(DB_NAME)
    if conn is None:
        print("❌ DB connection failed in save_grievance().")
        return

    cur = conn.cursor(dictionary=True)
    photo_blob = None

    # --- Handle photo download or pass raw bytes
    if photo_file:
        try:
            if isinstance(photo_file, bytes):
                # already downloaded in handlers
                photo_blob = photo_file
                print("🖼️ Photo received as raw bytes, skipping download.")
            else:
                # Telegram file object
                print("⬇️ Downloading Telegram photo...")
                file_info = await photo_file.get_file()
                photo_bytes = await file_info.download_as_bytearray()
                photo_blob = bytes(photo_bytes)
                print("✅ Photo downloaded successfully.")
        except Exception as e:
            print(f"⚠️ Failed to download photo: {e}")
            traceback.print_exc()

    # --- Calculate Priority Index
    try:
        sentiment, keyword_sev, freq, priority_idx = calculate_priority_index(grievance, issue)
    except Exception as e:
        print(f"⚠️ Priority index calculation failed: {e}")
        sentiment, keyword_sev, freq, priority_idx = 0, 0, 0, 0

    # --- Insert into DB
    query = """
        INSERT INTO grievances (
            user_id, username, grievance, issue, location,
            photo, additional_data, ai_reply,
            sentiment_score, keyword_severity, frequency_score, priority_index, status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending')
    """

    try:
        cur.execute(query, (
            user_id, username, grievance, issue, location,
            photo_blob, additional_data, ai_reply,
            sentiment, keyword_sev, freq, priority_idx
        ))
        conn.commit()
        print(f"✅ Grievance {cur.lastrowid} saved (priority={priority_idx:.3f})")
    except Error as e:
        print(f"❌ Error saving grievance: {e}")
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()



# --------------------------------------------------
# 4️⃣ Retrieve Grievance Status
# --------------------------------------------------
def get_status(user_id):
    conn = get_connection(DB_NAME)
    if conn is None:
        return []
    cur = conn.cursor(dictionary=True)
    query = """
        SELECT id, grievance, issue, location, photo,
               additional_data, ai_reply, status,
               sentiment_score, keyword_severity,
               frequency_score, priority_index, created_at
        FROM grievances
        WHERE user_id = %s
        ORDER BY id DESC
    """
    try:
        cur.execute(query, (user_id,))
        rows = cur.fetchall()
        return rows
    except Error as e:
        print(f"Error fetching user status: {e}")
        return []
    finally:
        cur.close()
        conn.close()
