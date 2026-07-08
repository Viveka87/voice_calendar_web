from datetime import datetime, timedelta
from db import get_db


def get_today_events_db():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT * FROM events
        WHERE DATE(event_date) = CURDATE()
        ORDER BY event_date ASC, event_time ASC
    """

    cursor.execute(query)
    events = cursor.fetchall()

    cursor.close()
    db.close()
    return events


def get_week_events_db():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT * FROM events
        WHERE event_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
        ORDER BY event_date ASC, event_time ASC
    """

    cursor.execute(query)
    events = cursor.fetchall()

    cursor.close()
    db.close()
    return events