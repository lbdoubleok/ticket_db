import threading
import requests

URL = "http://localhost:5000/book/1"
NUM_USERS = 20  # จำลองคน 20 คนกดพร้อมกัน

results = []

def fake_user_books_ticket(user_id):
    response = requests.get(URL)
    results.append(response.text)

threads = []
for i in range(NUM_USERS):
    t = threading.Thread(target=fake_user_books_ticket, args=(i,))
    threads.append(t)

# ยิงทุก thread พร้อมกันให้ใกล้เคียง "เวลาเดียวกัน" ที่สุด
for t in threads:
    t.start()
for t in threads:
    t.join()

success_count = sum(1 for r in results if "สำเร็จ" in r)
print(f"จำนวนคนจองสำเร็จ: {success_count} (ที่นั่งที่มีจริง: 3)")