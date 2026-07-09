#import mysql.connector

#def get_db():
#    db = mysql.connector.connect(
#        host="localhost",
#        user="root",
#        password="",
#        database="voice_app"
 #   )
#    return db

import pymysql
import os

#connection = pymysql.connect(
#   host=os.getenv("mysql.railway.internal"),
#    user=os.getenv("root"),
#    password=os.getenv("bUdioCPHdvgMASYdOQzuStIVqkXRNcMj"),
#    database=os.getenv("railway"),
#    port=int(os.getenv("3306"))
#)
def get_db():
    return pymysql.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        #port=int(os.getenv("MYSQLPORT"))
        port=int(os.getenv("MYSQLPORT", 3306))
    )