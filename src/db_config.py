import mysql.connector

def db_connection():
    con=mysql.connector.connect(
       host="mysql",
       user="root",
       password="root",
       database="cloud_inventory"
        
    )
    return con