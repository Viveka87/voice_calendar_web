import mysql.connector

def get_db():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="voice_app"
    )
    return db