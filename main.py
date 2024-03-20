from flask import Flask, request, jsonify
from config import get_database, app
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
    matchedDocs = collection.find({"tags": tags}, projection)
    jsonDocs = []
    print("got the results")
    for doc in matchedDocs:
        print(doc.get("jobTitle"))
        print(type(doc))
        print(doc)
        #jsonDoc = json.dumps(doc)
        jsonDocs.append(doc)
    
    return jsonify({"jobs": jsonDocs})

# if we run the file directly do this, if we are importing this file then dont
# do this, maybe you just want another file to access the functions 
if __name__ == "__main__":
    # logic for connecting to db 

    app.run(host="0.0.0.0", port=80)
