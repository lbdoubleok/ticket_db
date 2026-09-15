from flask import Flask, render_template
import mysql.connector
import os
from dotenv import load_dotenv
import time

load_dotenv()  # โหลดค่าจากไฟล์ .env

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
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # เริ่ม Transaction
        conn.start_transaction()

        # SELECT ... FOR UPDATE: ล็อกแถวนี้ไว้ คนอื่นต้องรอ
        cursor.execute(
            "SELECT available_seats FROM concerts WHERE id = %s FOR UPDATE",
            (concert_id,)
        )
        concert = cursor.fetchone()
        available = concert["available_seats"]

        time.sleep(0.5)  # หน่วงเวลาเหมือนเดิม เพื่อทดสอบว่า lock ทำงานจริง

        if available > 0:
            cursor.execute(
                "INSERT INTO bookings (concert_id, user_name, seats) VALUES (%s, %s, %s)",
                (concert_id, "guest", 1)
            )
            cursor.execute(
                "UPDATE concerts SET available_seats = available_seats - 1 WHERE id = %s",
                (concert_id,)
            )
            conn.commit()  # ยืนยัน transaction — ปลดล็อก
            result = "✅ จองสำเร็จ!"
        else:
            conn.rollback()  # ยกเลิก transaction — ปลดล็อก
            result = "❌ ที่นั่งเต็มแล้ว"

    except Exception as e:
        conn.rollback()
        result = f"⚠️ เกิดข้อผิดพลาด: {e}"

    finally:
        cursor.close()
        conn.close()

    return result

if __name__ == "__main__":
    app.run(debug=True)