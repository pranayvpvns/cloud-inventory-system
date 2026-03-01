from pymongo import MongoClient

def get_mongo_connection():
    client = MongoClient("mongodb://mongo:27017/")
    db = client["cloud_inventory_logs"]
    return db