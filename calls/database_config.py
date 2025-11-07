
# --- copilot ---
# import os
# from dotenv import load_dotenv

# load_dotenv()

# username = os.getenv("USERNAME")
# password = os.getenv("PASSWORD")
# dbname = os.getenv("DBNAME")

# mongo_uri = f"mongodb+srv://{username}:{password}@cluster0.xxxxx.mongodb.net/{dbname}?retryWrites=true&w=majority"


# calls/database_config.py
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()  # reads .env in project root
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI not set. Copy .env.example -> .env and set MONGO_URI")

# Connect
client = MongoClient(MONGO_URI)
# Replace 'smartbitesDB' with your DB name if needed
db = client["smartbites"]  # returns the database name from the URI if included

# Example collections (create as needed)
users_collection = db["users"]


# Helper functions
def insert_one(collection, doc):
    return collection.insert_one(doc)

def insert_many(collection, docs):
    return collection.insert_many(docs)

def find(collection, query=None, projection=None, limit=0):
    query = query or {}
    cursor = collection.find(query, projection)
    if limit:
        cursor = cursor.limit(limit)
    return cursor

def find_one(collection, query=None, projection=None):
    return collection.find_one(query or {}, projection)

def update_one(collection, filter_query, update_doc, upsert=False):
    return collection.update_one(filter_query, {"$set": update_doc}, upsert=upsert)

def delete_one(collection, filter_query):
    return collection.delete_one(filter_query)