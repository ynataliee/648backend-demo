from flask import Flask, request, jsonify, abort
from config import get_database, app
import requests
import pickle
import json
import os
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt, check_password_hash
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient



# jsonify is used to create a json response
# CORS is for cross origin requests 
# CORS gives web servers the ability to say they want to opt into allowing 
# cross-origin access to their resources
# CORS is a part of HTTP that lets servers specify *any other hosts* from which a 
# browser should permit loading of content --> so we would need to have this to specify that we allow our front end
# to access these objects 
# what happens if we don't have this ??
# Two objects have the same *origin* only when the scheme(protocol), hostname(domain), and port of URL all match.
# default port for the HTTPS protocol is 443


'''
create -> name, skills, interests (to make it easier maybe let the user type this in for milestone 2, 
in the real app we want to controll the skills and interests to avaoid typos and stuff)

get -> search by project tags 

we need to create a class to represent each of our users and the object fields(like projects)
that are in our DB so that we can use jsonable_encoder to turn everything we need to send to the backend 
to json

'''
#initialising our libraries with this app
load_dotenv()
Bcrypt = Bcrypt(app)

app.config['JWT_SECRET_KEY'] = os.getenv('FLASK_SECRET')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=60)
jwt = JWTManager(app)
#

#User_schema for storing users
user_schema = {
    "username": "",
    "password": "",
    "email": "",
    "userTags": ""
}

#session_schema for storing sessions
session_schema = {
    "createdAt": "",
    "email": "",
    "token": ""
}


#testing
@app.route("/test", methods = ["GET"])
@jwt_required()
def getUser():
    db = get_database("sample_training")
    collection = db["sessions"]

    # email = request.json["email"]
    jwtEmail = get_jwt_identity()
    token = request.json["token"]

    if(validateSession(jwtEmail, token) == True):
        return jsonify({
            "response": "Authorized user found",
            "status": "200"
        })
    else:
        return jsonify({
            "response": "You are not authorized",
            "status": "401"
        })
    
    
####  

    
def validateSession(email, token):
    db = get_database("sample_training")
    collection = db["sessions"]

    sessionEmail = collection.find_one({"email": str(email)}, {'_id': False})
    if ( sessionEmail != None ):
        print("sessionEmail found")
        if( sessionEmail["token"] == token ):
            print("The tokens match")
            return True 
    else:
        return False

@app.route("/register", methods = ["POST"])
def registerUser():
    db = get_database("sample_training")
    collection = db["users"]

    username = request.json["username"]
    password = str(request.json["password"])
    email = request.json["email"]

    userExist = collection.find_one({"email": email }, {'_id': False})

    if(userExist != None):
        return jsonify({
            "response": "This user already exist",
            "status": "403"
        })
    else:
        user_schema["username"] = username
        user_schema["password"] = Bcrypt.generate_password_hash(password).decode('utf-8')
        user_schema["email"] = email
        collection.insert_one(user_schema)

        #later on should clear session_schema after insert

        return jsonify({
            "response": "User has been registered.",
            "status": "200"
        })

# CURRENTLY UNDER MODIFICATION    
@app.route("/login", methods = ["POST"])    
def login():
    db = get_database("sample_training")
    collection = db["users"]

    email = request.json["email"]
    password = str(request.json["password"])

    response = collection.find_one({"email": email}, {'_id': False})
    if( response == None):
        return jsonify({
            "response": "User doesn't exist",
            "status": "404"
        })
    
    responsePass = response["password"]

    if ( Bcrypt.check_password_hash(responsePass, password) == True):

        sessionCollection = db["sessions"]

        if( sessionCollection.find_one({"email": email}, {'_id': False}) != None):
            print(sessionCollection.find_one({"email": email}, {'_id': False}))
            return jsonify({
                "response": "This user already has an active session",
                "status": "403"
            })

        # ### We are here trying to store session into new collection
        # sessionDate = get_bson_datetime()

        sessionToken = create_access_token(identity=email)
        

        sessionCollection.insert_one({
            "createdAt": datetime.utcnow(),
            "email": email,
            "token": sessionToken
        })

        #later on should clear session_schema after insert

        return jsonify({
            "response": f'{email} has been logged in',
            "token": f'{sessionToken}',
            "expires": "60 minutes",
            "email": email,
            "status": "200"
        })
    else:
        return jsonify({
            "repsonse": "Password doesn't match",
            "status": "401"
        })

@app.route("/logout", methods = ["POST"])
@jwt_required()
def logout():
    db = get_database("sample_training")
    collection = db["sessions"]

    requestEmail = request.json["email"]
    if(requestEmail != get_jwt_identity()):
        return jsonify({
            "response": "You are not authorized to perform this action",
            "status": "401"
        })

    requestToken = request.json["token"]

    if( validateSession(requestEmail, requestToken) == True ):
        query = collection.find_one({"email": requestEmail}, {'_id': False})
        collection.delete_one(query)
        return jsonify({
            "response": "User has been logged out",
            "status": "200"
        })
    else:
        return jsonify({
            "response": "Unable to perform logout",
            "status": "404"
        })


@app.route("/projects", methods = ["GET"])
def get_projects():
    db = get_database("sample_training")
    collection = db["records"]
    res = collection.find_one({"name": "Sam See"})
    print(type(res.get("projects")))
    # to use jsonify you need to turn data into a python dictionary and 
    # then we can call jsonify on it
    # the get() returns a list of python dictionaries 
    data = {}
    data["projects"] = res.get("projects")
    # for proj in res.get("projects"):
    #     projects[]
    response = jsonify(data)
    return response

@app.route("/search", methods = ["GET"])
def job_search():
    tags = request.args.get('tags')
    #print("TAGS: ", tags, "\n\n")
    db = get_database("sample_training")
    collection = db["jobDescriptions"]

    print("tag from query: ", tags, "\n")
    projection = {"_id" : 0}

    regex_pattern = re.escape(tags) + '.*'
    regex_query = {"tags": {"$regex": regex_pattern, "$options": "i"}}

    matchedDocs = collection.find(regex_query, projection)
    jsonDocs = []
    print("got the results")
    for doc in matchedDocs:
        print(doc.get("jobTitle"))
        print(type(doc))
        print(doc)
        #jsonDoc = json.dumps(doc)
        jsonDocs.append(doc)
    
    return jsonify({"jobs": jsonDocs})

@app.route("/interestTags", methods = ["GET", "POST"])
def interestTags():
    if request.method == "GET":
        db = get_database("sample_training")
        collection = db["interestTags"]

        projection = {"_id" : 0}
        doc = collection.find_one({}, projection)
        tags = doc.get("interests")
        print("type: ", type(tags))
        for tag in tags:
            print("tag: ", tag, "\n")
        return jsonify({"interestTags": tags})
    else:
        """TO DO 
        - Need to store the interests selected into the doc for the user 
        - this means that we need the user logged in to save thier interests
        - case where we can do this without having the user loggedin??
        """
        db = get_database("sample_training")
        collection = db["testUsers"]

        email = request.json.get("email")
        recievedInterests = request.json.get("selectedInterests")

        doc = collection.find_one({"email": email}, {"_id": 0})
        savedInterests = doc["interests"]
        for interest in recievedInterests:
            if interest not in savedInterests:
                savedInterests.append(interest)

        update = {"$set": {"interests": savedInterests}}
        collection.update_one({"email": email}, update)
        # if the interest is not already in the list of interests then add it 

        return jsonify({"savedInterests": savedInterests})

def isNewJob(job, likedJobs):
    """ 
        likedJobs is a list of dictionaries
        job is single dictionary with info about a job
    """
    if len(likedJobs) == 0:
        return True

    title = job["job_title"]
    print("title : ", title, "\n")
    for job in likedJobs:
        if job["job_title"] == title:
            return False
    return True

@app.route("/getJobs", methods = ["GET", "POST"])
def getJobs():
    if request.method == "GET":
        # loading database
        db = get_database("sample_training")
        collection = db["testUsers"]
        # check if the user exists in the database with thier email 
        email = request.headers["email"]
        doc = collection.find_one({"email": email}, {"_id": 0})
        if doc == None:
            return jsonify({"Message": f"No user with email {email} exists."})
        # if we made it to here then we have the users information
        savedInterests = doc["interests"]

        # handle the case where the user has no saved interests yet 
        if len(savedInterests) == 0:
            return jsonify({"Message": f"User with email {email} has no saved interests.", "Error": "No saved interests."})
        
        # call the jobs api to search for jobs 
        url = "https://jsearch.p.rapidapi.com/search"

        # format request to jobsAPI 
        querystring = {"query":f" {savedInterests} internships in san francisco ca","page":"1","num_pages":"1"}
        headers = {
            "X-RapidAPI-Key": "377585313cmshf1355d5b402d248p1b423bjsn233ad30d00f0",
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }

        # uncomment lines 135 and 136 to make a request to the real jobsAPI endpoint
        #jobsApiRes = requests.get(url, headers=headers, params=querystring)
        #jsonJobsResponse = jobsApiRes.json()

        # Open the pickle file where the jobsAPI response was saved, to use it as example data 
        # to not waste our free api calls
        with open('./output/jobsAPIResponse2.pickle', 'rb') as f:
            # Deserialize the data from the file
            data = pickle.load(f)
        # turn the saved jobsapi response to json format 
        dummyJsonData = json.dumps(data)
        jsonDict = json.loads(dummyJsonData)
        print(type(jsonDict))
        # pickle json response so that we dont have to make more calls to the jobs API
        # Convert JSON object to a Python dictionary
        #responseToDict = json.loads(json.dumps(jsonJobsResponse))
        # Pickle the Python dictionary
        #with open("./output/jobsAPIResponse2.pickle", "wb") as pickle_file:
            #pickle.dump(responseToDict, pickle_file)
        
        return dummyJsonData #jsonJobsResponse

    if request.method == "POST":
         # loading database
        db = get_database("sample_training")
        collection = db["testUsers"]
        # check if the user exists in the database with thier email 
        email = request.json.get("email")
        doc = collection.find_one({"email": email}, {"_id": 0})
        if doc == None:
            return jsonify({"Message": f"No user with email {email} exists."})
        
        # save the jobs into the users likedJobs field
        likedJobs = doc["likedJobs"]
        recievedJobs = request.json.get("jobsSelected")
        for job in recievedJobs:
            newJob = isNewJob(job, likedJobs)
            if newJob:
                likedJobs.append(job)

        update = {"$set": {"likedJobs": likedJobs}}
        collection.update_one({"email": email}, update) 

        return jsonify({"jobsAdded": likedJobs})



# if we run the file directly do this, if we are importing this file then dont
# do this, maybe you just want another file to access the functions 
if __name__ == "__main__":
    # logic for connecting to db 

    app.run(host="0.0.0.0", port=os.getenv('FLASK_PORT'))
