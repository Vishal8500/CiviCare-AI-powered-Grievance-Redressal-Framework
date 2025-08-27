import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

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


def init_db():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grievances (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT,
            username VARCHAR(255),
            grievance TEXT,
            status VARCHAR(50) DEFAULT 'Pending'
        )
    """)
    connection.commit()
    cursor.close()
    connection.close()


def save_grievance(user_id, username, grievance):
    connection = get_connection()
    cursor = connection.cursor()
    query = "INSERT INTO grievances (user_id, username, grievance) VALUES (%s, %s, %s)"
    cursor.execute(query, (user_id, username, grievance))
    connection.commit()
    cursor.close()
    connection.close()


def get_status(user_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT id, grievance, status FROM grievances WHERE user_id = %s ORDER BY id DESC"
    cursor.execute(query, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return rows
