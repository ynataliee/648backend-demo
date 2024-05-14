from flask import Flask, request, jsonify, abort
from config import get_database, app
from projects import generateProjects
import requests
import pickle
import json
import os
import re
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt, check_password_hash
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient

from projects import generateProjects
from generateProjects_v3 import getDemoProjects, combinedProjects, evaluateCombinedProj, getFinalProj

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
    "interests": [],
    "aboutUser": [], 
    "savedProjects": [], # projects the user has "liked" or selected to save
    "likedJobs": [], # all the jobs the user has selected, in other words, thier history of selected jobs
    "currentlySelectedJobs": [] # the most recent set of jobs they have selected, these will be used to generate projects from
}

#session_schema for storing sessions
session_schema = {
    "createdAt": "",
    "email": "",
    "token": ""
}

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

@app.route("/saveProjects", methods = ["GET", "POST"])
@jwt_required()
def saveProjects():
    
    db = get_database("sample_training")
    collection = db["sessions"]

    # email = request.json["email"]
    jwtEmail = get_jwt_identity()

    if(jwtEmail != request.json["email"]):
        return jsonify({
            "response": "You're not Authorized",
            "status": 401
        })

    token = request.json["token"]

    if(validateSession(jwtEmail, token) == False):
        return jsonify({
            "response": "You're not Authorized",
            "status": 401
        })

    collection = db["users"]

    if( request.method == "POST" ):
        collection = db["users"]
        # frontend should send back the savedJobs with the field savedProjects 
        userSavedProjects = request.json["generatedProjects"] # change to a different key after testing
        
        for index in range( len(userSavedProjects) ):
            collection.find_one_and_update({"email": jwtEmail},
                                    { '$push': { "savedProjects" : userSavedProjects[index] } } )
        
        
        return jsonify({
            "response": "Projects have been saved.",
            "status": 200
        })
    
    if( request.method == "GET" ):
        collection = db["users"]
        returnSavedJobs = []

        queryResult = collection.find_one({ "email": str(jwtEmail) }, {"_id": False, "username": False, "password": False,
                                                                       "email": False, "interests": False, "likedJobs": False,
                                                                       "currentlySelectedJobs": False})
        
        for index in range (len(queryResult["savedProjects"])):
            returnSavedJobs.append(queryResult["savedProjects"][index])

        return jsonify({
            "response": returnSavedJobs,
            "status": 200
        })


@app.route("/register", methods = ["POST"])
def registerUser():
    db = get_database("sample_training")
    collection = db["users"]

    username = request.json["username"]
    password = request.json["password"]
    email = request.json["email"]

    userExist = collection.find_one({"email": email }, {'_id': False})

    if(userExist != None):
        return jsonify({
            "response": "This user already exist",
            "status": 403
        })
    else:
        # user_schema["username"] = username
        # user_schema["password"] = Bcrypt.generate_password_hash(password).decode('utf-8')
        # user_schema["email"] = email
        collection.insert_one({
            "username": username,
            "password": Bcrypt.generate_password_hash(password).decode('utf-8'),
            "email": email,
            "interests": [],
	    "aboutUser":[],
            "savedProjects": [],
            "likedJobs": [],
            "currentlySelectedJobs": []
        })

        #later on should clear session_schema after insert

        return jsonify({
            "response": "User has been registered.",
            "status": 200
        })


# CURRENTLY UNDER MODIFICATION    
@app.route("/login", methods = ["POST"])    
def login():
    db = get_database("sample_training")
    collection = db["users"]

    email = request.json["email"]
    password = request.json["password"]

    response = collection.find_one({"email": email}, {'_id': False})
    if (response == None):
        return jsonify({
            "response": "User doesn't exist",
            "status": 404
        })

    responsePass = response["password"]

    if ( Bcrypt.check_password_hash(responsePass, password) == True):

        sessionCollection = db["sessions"]

        if( sessionCollection.find_one({"email": email}, {'_id': False}) != None):
            print(sessionCollection.find_one({"email": email}, {'_id': False}))
            return jsonify({
                "response": "This user already has an active session",
                "status": 403
            })

        # ### We are here trying to store session into new collection
        # sessionDate = get_bson_datetime()

        sessionToken = create_access_token(identity=email)

        isNewUser = 1
        responseProfile = response["aboutUser"]
        responseInterest = response["interests"]

        if( len(responseProfile) == 0 or len(responseInterest) == 0 ):
            isNewUser = 0

        sessionCollection.insert_one({
            "createdAt": datetime.utcnow(),
            "email": email,
            "token": sessionToken
        })

        # later on should clear session_schema after insert

        return jsonify({
            "response": f'{email} has been logged in',
            "token": f'{sessionToken}',
            "expires": "60 minutes",
            "email": email,
	    "isNewUser": isNewUser,
            "status": 200
        })
    else:
        return jsonify({
            "repsonse": "Password doesn't match",
            "status": 401
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
            "status": 401
        })

    requestToken = request.json["token"]

    if( validateSession(requestEmail, requestToken) == True ):
        query = collection.find_one({"email": requestEmail}, {'_id': False})
        collection.delete_one(query)
        return jsonify({
            "response": "User has been logged out",
            "status": 200
        })
    else:
        return jsonify({
            "response": "Unable to perform logout",
            "status": 404
        })

@app.route("/interestTags", methods = ["GET", "POST"])
def interestTags():
    if request.method == "GET":
        db = get_database("sample_training")
        collection = db["interestTags"]

        projection = {"_id" : 0}
        doc = collection.find_one({}, projection)
        tags = doc.get("interests")
        
        return jsonify({"interestTags": tags, "status": "200"})
    else:
        db = get_database("sample_training")
        collection = db["users"]

        email = request.json.get("email")
        print("Email: ", email, "\n")
        recievedInterests = request.json.get("selectedInterests")
        # exception handling
        if recievedInterests == None:
            return jsonify({"Message": "You did not send any selected interests for the user", "status": "404"})

        doc = collection.find_one({"email": email}, {"_id": 0})

        # more exception handling
        if doc == None:
            return jsonify({"Message": f"No user with email {email} exists.", "status": "404"})
        
        # the user exists and we can get thier interests
        savedInterests = doc["interests"]
        for interest in recievedInterests:
            if interest not in savedInterests:
                savedInterests.append(interest)

        update = {"$set": {"interests": savedInterests}}
        collection.update_one({"email": email}, update) 

        return jsonify({"savedInterests": savedInterests, "status": "200"})
    
@app.route("/aboutUserTags", methods = ["GET", "POST"])
def aboutUserTags():
    if request.method == "GET":
        # accessing the collection with the about user tags 
        db = get_database("sample_training")
        collection = db["aboutUserTags"]

        # retrieving the doc with the tags in it, only showing fields we need
        projection = {"_id" : 0}
        doc = collection.find_one({}, projection)

        gradeLevel = doc.get("gradeLevel")
        technicalSkills = doc.get("technicalSkills")

        return jsonify({"gradeLevelTags": gradeLevel, "technicalSkillsTags": technicalSkills, "status": "200"})
    else:
        db = get_database("sample_training")
        collection = db["users"]

        email = request.json.get("email")
        # frontend needs to put the selected about user tags into a field called aboutUser
        # this is a list of strings where each string is a tag that the user selected 
        recievedAboutUser = request.json.get("aboutUser")
        # exception handling
        if recievedAboutUser == None:
            return jsonify({"Message": f"You did not send any about user tags for {email}", "status": "404"})

        # getting doc with users information 
        doc = collection.find_one({"email": email}, {"_id": 0})
        # more exception handling
        if doc == None:
            return jsonify({"Message": f"No user with email {email} exists.", "status": "404"})
        
        # the user exists and we can get thier about tags
        savedAboutUser = doc["aboutUser"]
        for tag in recievedAboutUser:
            if tag not in savedAboutUser:
                savedAboutUser.append(tag)

        update = {"$set": {"aboutUser": savedAboutUser}}
        collection.update_one({"email": email}, update) 

        return jsonify({"savedAboutUser": savedAboutUser, "status": "200"})

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

@app.route("/searchJobs", methods = ["GET", "POST"])
def getJobs():
    if request.method == "GET":
        # loading database
        db = get_database("sample_training")
        collection = db["users"]
        # check if the user exists in the database with thier email 
        email = request.headers["email"]
        doc = collection.find_one({"email": email}, {"_id": 0})
        if doc == None:
            return jsonify({"Message": f"No user with email {email} exists.", "status": "404"})
        # if we made it to here then we have the users information
        savedInterests = doc["interests"]

        # handle the case where the user has no saved interests yet 
        if len(savedInterests) == 0:
            return jsonify({"Message": f"User with email {email} has no saved interests.", "Error": "No saved interests.", "status": "404"})
        
        # call the jobs api to search for jobs 
        url = "https://jsearch.p.rapidapi.com/search"

        # format request to jobsAPI 
        querystring = {"query":f" {savedInterests} internships in san francisco ca","page":"1","num_pages":"1"}
        headers = {
            "X-RapidAPI-Key": "377585313cmshf1355d5b402d248p1b423bjsn233ad30d00f0",
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }

        # uncomment lines 135 and 136 to make a request to the real jobsAPI endpoint
        jobsApiRes = requests.get(url, headers=headers, params=querystring)
        jsonJobsResponse = jobsApiRes.json()

        # Open the pickle file where the jobsAPI response was saved, to use it as example data 
        # to not waste our free api calls
        #with open('./output/jobsAPIResponse2.pickle', 'rb') as f:
            # Deserialize the data from the file
            #data = pickle.load(f)
        # turn the saved jobsapi response to json format 
        #dummyJsonData = json.dumps(data)
        #jsonDict = json.loads(dummyJsonData)

        #jsonDict["status"] = "200"
        jsonJobsResponse["status"] = "200"
        print(jsonJobsResponse)
	# currently returning dummy data
        return jsonJobsResponse #jsonify(jsonDict)

    if request.method == "POST":
        # loading database
        db = get_database("sample_training")
        collection = db["users"]
        # check if the user exists in the database with thier email 
        email = request.json.get("email")
        doc = collection.find_one({"email": email}, {"_id": 0})
        if doc == None:
            return jsonify({"Message": f"No user with email {email} exists.", "status": "404"})
        
        # save the jobs into the users likedJobs field
        likedJobs = doc["likedJobs"]
        recievedJobs = request.json.get("jobsSelected")

        if recievedJobs == None:
            return jsonify({"Message": f"You did not send any jobs for this user.", "status": "404"})
            
        for job in recievedJobs:
            newJob = isNewJob(job, likedJobs)
            if newJob:
                likedJobs.append(job)

        update = {"$set": {"likedJobs": likedJobs, "currentlySelectedJobs": recievedJobs}}
        collection.update_one({"email": email}, update) 

        return jsonify({"jobsAdded": likedJobs, "status": "200"})

@app.route("/generateProjects", methods = ["GET"])
def genProjects():
    db = get_database("sample_training")
    collection = db["users"]
    # check if the user exists in the database with thier email 
    email = request.headers["email"]
    doc = collection.find_one({"email": email}, {"_id": 0})

    if doc == None:
        return jsonify({"Message": f"No user with email {email} exists.", "status": "404"})

    # retrieving the jobs to use to generate the projects from 
    selectedJobs = doc["currentlySelectedJobs"]
    userContext = doc["aboutUser"]
    if len(selectedJobs) == 0:
        return jsonify({"message": "User has no recently selected jobs to generate a project from.", "status": "404"})

    # calling LLM to generate the projects, they will be appended to the projects list
    demoProjects = []
    for job in selectedJobs:
        # project is a dictionary
        demoProject = getDemoProjects(job=job, userContext=userContext)
        demoProjects.append(demoProject)

    combinedProject = combinedProjects(demoProjects, selectedJobs, userContext)
    updatedProject = evaluateCombinedProj(combinedProject, userContext)
    finalProject = getFinalProj(updatedProject)
    projs = []
    projs.append(finalProject)
    return jsonify({"generatedProjects": projs, "status": "200"})

@app.route("/getProjects", methods = ["GET"])
def getProjects():
    db = get_database("sample_training")
    collection = db["users"]
    # check if the user exists in the database with thier email 
    email = request.headers["email"]
    doc = collection.find_one({"email": email}, {"_id": 0})
    if doc == None:
        return jsonify({"Message": f"No user with email {email} exists.", "status": "404"})
    savedProjects = doc["savedProjects"]

    if len(savedProjects) == 0:
        return jsonify({"message": "No projects generated for this user yet..", "status": "404"})

    return jsonify({"savedProjects": savedProjects, "status": "200"})


# if we run the file directly do this, if we are importing this file then dont
# do this, maybe you just want another file to access the functions 
if __name__ == "__main__":
    # logic for connecting to db 

    app.run(host="0.0.0.0", port=os.getenv('FLASK_PORT'))
