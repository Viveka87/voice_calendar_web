import smtplib
from email.mime.text import MIMEText
from config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS, TO_EMAIL
from collections import defaultdict

def format_events(title, events):
    if not events:
        return f"{title}:\nNo events\n"

    grouped = defaultdict(list)

    for e in events:
        date = str(e.get("event_date"))
        grouped[date].append(e)

    text = f"{title}:\n"

    for date in sorted(grouped.keys()):
        text += f"\n📅 {date}\n"

        for e in grouped[date]:
            name = e.get("text") or e.get("title") or "No Title"
            time = e.get("event_time") or ""

            text += f"  • {time} - {name}\n"

    return text

def send_email(today_events, week_events):
    body = ""
    body += format_events("Today's Events", today_events)
    body += "\n"
    body += format_events("This Week's Events", week_events)

    msg = MIMEText(body)
    msg["Subject"] = "Event Summary"
    msg["From"] = EMAIL_USER
    msg["To"] = TO_EMAIL

    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASS)
    server.send_message(msg)
    server.quit()