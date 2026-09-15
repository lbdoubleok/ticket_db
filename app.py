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
def book_naive(concert_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Step 1: อ่านจำนวนที่นั่งเหลือ
    cursor.execute("SELECT available_seats FROM concerts WHERE id = %s", (concert_id,))
    concert = cursor.fetchone()
    available = concert["available_seats"]

    # หน่วงเวลาเล็กน้อย เพื่อ "ขยาย" ช่วงเวลาที่ race condition จะเกิด
    # (ในระบบจริง การหน่วงนี้เกิดเองจาก network/processing time)
    time.sleep(0.5)

    # Step 2: เช็คว่าที่นั่งพอไหม
    if available > 0:
        # Step 3: บันทึกการจอง
        cursor.execute(
            "INSERT INTO bookings (concert_id, user_name, seats) VALUES (%s, %s, %s)",
            (concert_id, "guest", 1)
        )
        # Step 4: ลดจำนวนที่นั่งเหลือ
        cursor.execute(
            "UPDATE concerts SET available_seats = available_seats - 1 WHERE id = %s",
            (concert_id,)
        )
        conn.commit()
        result = "✅ จองสำเร็จ!"
    else:
        result = "❌ ที่นั่งเต็มแล้ว"

    cursor.close()
    conn.close()
    return result

if __name__ == "__main__":
    app.run(debug=True)