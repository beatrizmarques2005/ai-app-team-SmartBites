
# connect to the mongodb

from pymongo import MongoClient
client = MongoClient("mongodb+srv://smartbites: @smartbitescluster.8zvuc.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")

def get_collection(database, collection_name):
    return client[database][collection_name]