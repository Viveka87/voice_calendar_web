from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
#import mysql.connector
import dateparser
from dateparser.search import search_dates
from datetime import timedelta, datetime, date
from dateutil.parser import parse
import re

import pymysql
from db import get_db
from events.event_queries import get_today_events_db, get_week_events_db
from email_service.sender import send_email
import threading
import time

app = Flask(__name__)
CORS(app)

# MySQL connection
# def get_db():
#  db = mysql.connector.connect(
#     host="localhost",
#     user="root",
#     password="",
#     database="voice_app"
# )
#  return db
@app.route('/debug-insert')
def debug_insert():
    import os
    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO events (text, event_date, event_time) VALUES (%s, %s, %s)",
            ("test event", "2026-07-14", "12:00:00")
        )
        db.commit()

        cursor.execute("SELECT * FROM events")
        data = cursor.fetchall()

        return {
            "status": "success",
            "data": str(data),
            "host": os.getenv("MYSQLHOST"),
            "db": os.getenv("MYSQLDATABASE")
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "host": os.getenv("MYSQLHOST"),
            "user": os.getenv("MYSQLUSER")
        }
import threading
import time

def scheduler():
    while True:
        now = datetime.now()

        # send at 8 AM
        if now.hour == 8 and now.minute == 0:
            today_events = get_today_events_db()
            week_events = get_week_events_db()
            send_email(today_events, week_events)

            time.sleep(60)  # avoid duplicate send

        time.sleep(30)


threading.Thread(target=scheduler, daemon=True).start()

@app.route('/send-email-summary')
def send_summary():
    try:
        today_events = get_today_events_db()
        week_events = get_week_events_db()

        send_email(today_events, week_events)

        return jsonify({"message": "Email sent successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/')
def home():
    events = ["Event 1", "Event 2", "Event 3", "Event 4"]
    return render_template("index.html", events=events)

from datetime import timedelta

from datetime import timedelta, datetime, date

@app.route('/get-events')
def get_events():
    try:
        db = get_db()
        #cursor = db.cursor(dictionary=True)
        cursor = db.cursor(pymysql.cursors.DictCursor)
            
        cursor.execute("SELECT * FROM events")
        events = cursor.fetchall()

        for e in events:

            # ✅ FIX DATE
            if isinstance(e.get("event_date"), (datetime, date)):
                e["event_date"] = e["event_date"].strftime("%Y-%m-%d")

            # ✅ FIX TIME (ALL CASES)
            val = e.get("event_time")

            if val:

                # 🔥 timedelta fix
                if isinstance(val, timedelta):
                    total_seconds = int(val.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    e["event_time"] = f"{hours:02}:{minutes:02}"

                # ✅ datetime.time
                elif hasattr(val, "strftime"):
                    e["event_time"] = val.strftime("%H:%M")

                else:
                    e["event_time"] = str(val)

            else:
                e["event_time"] = ""

        cursor.close()
        db.close()

        return jsonify(events)

    except Exception as e:
        print("ERROR:", e)   # 🔥 VERY IMPORTANT
        return jsonify({"error": str(e)}), 500
    
@app.route('/add-event', methods=['POST'])
def add_event():
    print("REQUEST DATA:", request.data)
    print("REQUEST JSON:", request.json)
    data = request.json
    raw_text = data.get("text", "").strip()
    text_lower = raw_text.lower()
    now = datetime.now()

    # =====================================================
    # 1. TIME EXTRACTION
    # =====================================================

    hour, minute = None, 0

    # 9:30 pm / 6 pm
    time_match = re.search(
        r'\b(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)\b',
        text_lower
    )

    # 24 hr
    time_match_24 = re.search(r'\b(\d{1,2}):(\d{2})\b', text_lower)

    # 9 o'clock
    oclock_match = re.search(r'\b(\d{1,2})\s*o[\' ]?clock\b', text_lower)

    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        ampm = time_match.group(3).replace(".", "")

        if "pm" in ampm and hour != 12:
            hour += 12
        if "am" in ampm and hour == 12:
            hour = 0

    elif time_match_24:
        hour = int(time_match_24.group(1))
        minute = int(time_match_24.group(2))

    elif oclock_match:
        hour = int(oclock_match.group(1))
        minute = 0

    else:
        # default by keywords
        if "morning" in text_lower:
            hour = 9
        elif "afternoon" in text_lower:
            hour = 14
        elif "evening" in text_lower:
            hour = 18
        elif "night" in text_lower:
            hour = 20

    # fallback time
    if hour is None:
        hour = 9
        minute = 0

    event_time = datetime.strptime(f"{hour}:{minute}:00", "%H:%M:%S").time()

    # =====================================================
    # 2. DATE EXTRACTION
    # =====================================================

    event_date = None

    if "day after tomorrow" in text_lower:
        event_date = now + timedelta(days=2)

    elif "tomorrow" in text_lower:
        event_date = now + timedelta(days=1)

    elif "today" in text_lower:
        event_date = now

    elif "yesterday" in text_lower or "day before yesterday" in text_lower:
        return jsonify({"error": "❌ Cannot add past events"}), 400

    # 🔥 exact date like June 20th
    if not event_date:
        date_match = re.search(
            r'\b(\d{1,2}(st|nd|rd|th)?\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*|'
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{1,2}(st|nd|rd|th)?)\b',
            text_lower
        )

        if date_match:
            parsed = dateparser.parse(
                date_match.group(0),
                settings={"PREFER_DATES_FROM": "future"}
            )
            event_date = parsed if parsed else now

    # 🔥 weekdays
    if not event_date:
        weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2,
            "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
        }

        for day in weekdays:
            if day in text_lower:
                diff = (weekdays[day] - now.weekday()) % 7
                if diff == 0:
                    diff = 7
                event_date = now + timedelta(days=diff)
                break

    # fallback
    if not event_date:
        parsed = dateparser.parse(
            text_lower,
            settings={"PREFER_DATES_FROM": "future"}
        )
        event_date = parsed if parsed else now

    event_date = event_date.date()

    # =====================================================
    # 3. VALIDATE FUTURE
    # =====================================================

    event_datetime = datetime.combine(event_date, event_time)

    if event_datetime <= now:
        return jsonify({
            "error": "❌ This event time is already expired"
        }), 400

    # =====================================================
    # 4. CLEAN TEXT (FINAL FIX)
    # =====================================================

    cleaned_text = text_lower

    # remove time
    cleaned_text = re.sub(
        r'\b\d{1,2}(:\d{2})?\s*(a\.?m\.?|p\.?m\.?)\b', '', cleaned_text)
    cleaned_text = re.sub(r'\b\d{1,2}:\d{2}\b', '', cleaned_text)

    # remove oclock
    cleaned_text = re.sub(r'\b\d{1,2}\s*o[\' ]?clock\b', '', cleaned_text)
    cleaned_text = re.sub(r'\bo[\' ]?clock\b', '', cleaned_text)

    # remove date words
    cleaned_text = re.sub(
        r'\b(today|tomorrow|day after tomorrow|yesterday|day before yesterday)\b',
        '', cleaned_text)

    # remove time words
    cleaned_text = re.sub(
        r'\b(morning|afternoon|evening|night)\b', '', cleaned_text)

    # remove months
    cleaned_text = re.sub(
        r'\b(january|february|march|april|may|june|july|august|'
        r'september|october|november|december|'
        r'jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\b',
        '', cleaned_text)

    # remove dates
    cleaned_text = re.sub(r'\b\d{1,2}(st|nd|rd|th)?\b', '', cleaned_text)

    # remove am pm leftovers
    cleaned_text = re.sub(r'\b(a\s*m|p\s*m|am|pm)\b', '', cleaned_text)

    # clean symbols
    cleaned_text = re.sub(r'[^\w\s]', ' ', cleaned_text)

    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

    # fallback
    if not cleaned_text:
        cleaned_text = "Reminder"

    # =====================================================
    # DEBUG
    # =====================================================

    print("\n========== DEBUG ==========")
    print("RAW:", raw_text)
    print("DATE:", event_date)
    print("TIME:", event_time)
    print("TEXT:", cleaned_text)
    print("==========================\n")

    # =====================================================
    # 5. INSERT DB
    # =====================================================

    db = get_db()
    cursor = db.cursor()
 
    cursor.execute(
        "INSERT INTO events (text, event_date, event_time) VALUES (%s, %s, %s)",
        (cleaned_text, event_date, event_time.strftime("%H:%M:%S"))
    )

    db.commit()
    cursor.close()
    db.close()

    return jsonify({
        "message": "✅ Event Saved",
        "date": str(event_date),
        "time": event_time.strftime("%H:%M:%S"),
        "text": cleaned_text
    })

@app.route('/update-event/<int:id>', methods=['PUT'])
def update_event(id):
    from datetime import datetime, timedelta, time
    import re

    data = request.json
    raw_text = data.get("text", "").strip()
    text_lower = raw_text.lower()

    print("✅ UPDATE CALLED:", id, raw_text)

    now = datetime.now()

    # =========================
    # DB CONNECT
    # =========================
    db = get_db()
    #cursor = db.cursor(dictionary=True)
    cursor = db.cursor(pymysql.cursors.DictCursor)
    
    # =========================
    # GET OLD EVENT
    # =========================
    cursor.execute("SELECT * FROM events WHERE id=%s", (id,))
    old_event = cursor.fetchone()

    if not old_event:
        return jsonify({"error": "Event not found"}), 404

    # =========================
    # FIX TIME (🔥 MAIN BUG FIX)
    # =========================
    db_time = old_event["event_time"]

    if isinstance(db_time, timedelta):
        total_seconds = int(db_time.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        event_time = time(hours, minutes)
    else:
        event_time = db_time

    event_date = old_event["event_date"]

    # =========================
    # UPDATE TIME IF GIVEN
    # =========================
    time_match = re.search(
        r'\b(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)\b',
        text_lower
    )

    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        ampm = time_match.group(3).replace(".", "")

        if "pm" in ampm and hour != 12:
            hour += 12
        if "am" in ampm and hour == 12:
            hour = 0

        event_time = time(hour, minute)

    # =========================
    # UPDATE DATE IF GIVEN
    # =========================
    if "tomorrow" in text_lower:
        event_date = (now + timedelta(days=1)).date()

    elif "today" in text_lower:
        event_date = now.date()

    elif "day after tomorrow" in text_lower:
        event_date = (now + timedelta(days=2)).date()

    # =========================
    # VALIDATE FUTURE ONLY
    # =========================
    event_datetime = datetime.combine(event_date, event_time)

    if event_datetime <= now:
        return jsonify({
            "error": "❌ Cannot update past event"
        }), 400

    # =========================
    # CLEAN TEXT
    # =========================
    cleaned_text = re.sub(
        r'\b(today|tomorrow|day after tomorrow|morning|evening|am|pm|\d{1,2}(:\d{2})?)\b',
        '',
        text_lower
    )

    cleaned_text = re.sub(r'[^\w\s]', ' ', cleaned_text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

    if not cleaned_text:
        cleaned_text = old_event["text"]

    # =========================
    # UPDATE DB
    # =========================
    cursor.execute(
        "UPDATE events SET text=%s, event_date=%s, event_time=%s WHERE id=%s",
        (cleaned_text, event_date, event_time.strftime("%H:%M:%S"), id)
    )

    db.commit()

    print("✅ UPDATED:", cleaned_text, event_date, event_time)

    cursor.close()
    db.close()

    return jsonify({"message": "✅ Updated successfully"})

@app.route('/delete-event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    db = get_db()
    #cursor = db.cursor()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    cursor.execute(
        "DELETE FROM events WHERE id = %s",
        (event_id,)
    )

    db.commit()
    cursor.close()
    db.close()


    return jsonify({"message": "deleted"})

# ================== SCHEDULER FULL CODE ==================

import schedule


# ✅ DAILY JOB → 6:00 AM (Today events)
def daily_job():
    from events.event_queries import get_today_events_db
    from email_service.sender import send_today_email

    print("📅 Sending DAILY events...")

    today_events = get_today_events_db()
    send_today_email(today_events)


# ✅ WEEKLY JOB → Sunday 9:00 PM (Weekly events)
def weekly_job():
    from events.event_queries import get_week_events_db
    from email_service.sender import send_weekly_email

    print("📆 Sending WEEKLY events...")

    week_events = get_week_events_db()
    send_weekly_email(week_events)


# ✅ SET SCHEDULE TIMES

# Daily at 6:00 AM
schedule.every().day.at("18:00").do(daily_job)

# Weekly Sunday at 9:00 PM
schedule.every().sunday.at("21:00").do(weekly_job)


# ✅ RUN SCHEDULER LOOP
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(30)


# ✅ START BACKGROUND THREAD
threading.Thread(target=run_scheduler, daemon=True).start()

# ================== END ==================


if __name__ == '__main__':
    app.run()
    # app.run(debug=True)
    # port = int(os.environ.get("PORT", 5000))
    # app.run(host="0.0.0.0", port=port)