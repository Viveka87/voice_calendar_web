from datetime import datetime, timedelta
from db import get_db


def get_today_events_db():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    today = datetime.now().strftime("%Y-%m-%d")

    query = "SELECT * FROM events WHERE DATE(event_date) = %s"
    cursor.execute(query, (today,))
    events = cursor.fetchall()

    cursor.close()
    db.close()

    return events


def get_week_events_db():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    today = datetime.now()
    end_week = today + timedelta(days=7)

    query = """
        SELECT * FROM events
        WHERE event_date BETWEEN %s AND %s
    """

    cursor.execute(query, (today.strftime("%Y-%m-%d"),
                           end_week.strftime("%Y-%m-%d")))

    events = cursor.fetchall()

    cursor.close()
    db.close()

    return events