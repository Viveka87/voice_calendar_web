# import mysql.connector

# def get_db():
#    db = mysql.connector.connect(
#        host="localhost",
#        user="root",
#        password="",
#        database="voice_app"
#    )
#    return db

import pymysql
import os

def get_db():
    host = os.getenv("MYSQLHOST")
    user = os.getenv("MYSQLUSER")
    password = os.getenv("MYSQLPASSWORD")
    database = os.getenv("MYSQLDATABASE")
    port = int(os.getenv("MYSQLPORT"))

    print("HOST:", host)
    print("USER:", user)
    print("DB:", database)
    print("PORT:", port)

    try:
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            connect_timeout=10
        )
        print("✅ CONNECTED TO RAILWAY DB")
        return conn

    except Exception as e:
        print("❌ DB ERROR:", e)
        return None