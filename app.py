from flask import Flask, render_template
import mysql.connector
import os
from dotenv import load_dotenv
import time
import logging
import threading

load_dotenv()  # โหลดค่าจากไฟล์ .env

MAX_CONCURRENT_USERS = 5  # ยอมให้เข้าไปจองพร้อมกันได้สูงสุด 5 คน
current_users_in_room = 0
room_lock = threading.Lock()

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

@app.route("/")
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM concerts")
    concerts = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("index.html", concerts=concerts)

@app.route("/book/<int:concert_id>")
def book_safe(concert_id):
    global current_users_in_room

    # เช็คว่าห้องรอเต็มไหม
    with room_lock:
        if current_users_in_room >= MAX_CONCURRENT_USERS:
            logging.info("User sent to waiting room (room full)")
            return "⏳ ระบบมีคนใช้งานหนาแน่น กรุณารอสักครู่แล้วลองใหม่"
        current_users_in_room += 1

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()

        cursor.execute(
            "SELECT available_seats FROM concerts WHERE id = %s FOR UPDATE",
            (concert_id,)
        )
        concert = cursor.fetchone()
        available = concert["available_seats"]

        time.sleep(150)

        if available > 0:
            cursor.execute(
                "INSERT INTO bookings (concert_id, user_name, seats) VALUES (%s, %s, %s)",
                (concert_id, "guest", 1)
            )
            cursor.execute(
                "UPDATE concerts SET available_seats = available_seats - 1 WHERE id = %s",
                (concert_id,)
            )
            conn.commit()
            logging.info(f"Booking SUCCESS: concert_id={concert_id}")
            result = "✅ จองสำเร็จ!"
        else:
            conn.rollback()
            logging.warning(f"Booking REJECTED (sold out): concert_id={concert_id}")
            result = "❌ ที่นั่งเต็มแล้ว"

    except Exception as e:
        conn.rollback()
        result = f"⚠️ เกิดข้อผิดพลาด: {e}"

    finally:
        cursor.close()
        conn.close()
        # ออกจากห้องรอ ไม่ว่าผลจะเป็นยังไง
        with room_lock:
            current_users_in_room -= 1

    return result

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

if __name__ == "__main__":
    app.run(debug=True)