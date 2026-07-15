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
    print("HOST:", os.getenv("MYSQLHOST"))
    print("USER:", os.getenv("MYSQLUSER"))
    print("DB:", os.getenv("MYSQLDATABASE"))
    return pymysql.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT", 3306)),
        ssl={"ssl": {}}   # 🔥 important for many cloud DBs
        #connect_timeout=10 
    )
    