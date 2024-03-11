from flask import Flask
from pymongo import MongoClient
from flask_cors import CORS # allows us to send a request form a different URL to the backend 


app = Flask(__name__)
CORS(app)

def get_database(dbname):
    # Provide the mongodb atlas url to connect python to mongodb using pymongo
   CONNECTION_STRING = "mongodb+srv://Natalie:50hdwgxc46nhjczr@csc648.rvaiuma.mongodb.net/"

   # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
   client = MongoClient(CONNECTION_STRING)

   db = client[dbname]
   return db


# This is added so that many files can reuse the function get_database()
if __name__ == "__main__":   
  
   # Get the database
   db = get_database()