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
    return pymysql.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT", 3306)),
        ssl={"ssl": {}}   # 🔥 important for many cloud DBs
    )
    print("HOST:", os.getenv("MYSQLHOST"))
    print("DB:", os.getenv("MYSQLDATABASE"))