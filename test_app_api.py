import requests
import json
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = "http://127.0.0.1:5002"

def test_can_get_interestTags():
    email = "test1234@gmail.com"
    args = "?email=" + email 
    response = requests.get(ENDPOINT + "/interestTags"+ args)
    json_response = response.json()
    assert json_response.get("status") == "200"

def test_can_post_interestTags():
    payload = {
        "email": "test1234@gmail.com",
        "selectedInterests": ["Cloud Computing", "AWS"]
    }
    response = requests.post(ENDPOINT + "/interestTags", json=payload)
    json_response = response.json()
    assert json_response.get("status") == "200"
    # maybe add another assertion to check if the tags posted actually
    # were put into the db

def test_can_get_aboutUserTags():
    response = requests.get(ENDPOINT + "/aboutUserTags")
    json_response = response.json()
    assert json_response.get("status") == "200"

def test_can_post_aboutUserTags():
    payload = {
        "email": "test1234@gmail.com",
        "aboutUser": ["Computer Science Senior", "Data Structures and Algos"]
    }
    response = requests.post(ENDPOINT + "/aboutUserTags", json=payload)
    json_response = response.json()
    assert json_response.get("status") == "200"

def test_can_searchJobs():
    headers = {"email": "test1234@gmail.com"}
    response = requests.get(ENDPOINT + "/searchJobs", headers=headers)
    json_response = response.json()
    assert json_response.get("status") == "200"

def test_can_post_searchJobs():
    payload = {
        "email": "test1234@gmail.com",
        "jobsSelected": [{"job_title": "Alamar Biosciences, Inc", "job_description": """ 
                                                        We are seeking a Software Engineer Intern with an interest in developing and testing software control and data acquisition software. The successful candidate will be responsible for designing and implementing web-based user interfaces, writing and performing test plans, and more. The candidate will work with innovative technology and collaborate with a highly talented and motivated team to address unmet research and medical needs.

Responsibilities:

    Create, implement, and test web user interfaces using Blazor. 
    Transfer test plans from document files to a web-based platform. 
    Contribute to team discussions, sharing knowledge and expertise with other team members to promote best practices in software engineering and data analysis."""}, 
    
    {"job_title": "zoox", "job_description": """ 
                    The position involves design and implementation of metrics, models, and dashboards that validate the behavior of the Zoox AI software stack in closed-loop simulation. The candidate will have the opportunity to assess the safety, comfort, legal compliance, and other aspects of the autonomy stack and interact with key stakeholders throughout the organization. """}]
    }
    response = requests.post(ENDPOINT + "/searchJobs", json=payload)
    json_response = response.json()
    assert json_response.get("status") == "200"

def test_can_generateProjects():
    headers = {"email": "test1234@gmail.com"}
    response = requests.get(ENDPOINT + "/generateProjects", headers=headers)
    json_response = response.json()
    assert json_response.get("status") == "200"

def test_can_getProjects():
    headers = {"email": "test1234@gmail.com"}
    response = requests.get(ENDPOINT + "/getProjects", headers=headers)
    json_response = response.json()
    assert json_response.get("status") == "200"

def test_can_register():
    payload = {
        "username": "unitTestUser",
        "password": "unitTestPass",
        "email": "unitTest@gmail.com"
    }
    response = requests.post(ENDPOINT + "/register", json=payload)
    json_response = response.json()
    assert json_response.get("status") == "200"

def test_can_logIn_logout():
    payload = {
        "username": "unitTestUser",
        "password": "unitTestPass",
        "email": "unitTest@gmail.com"
    }
    response = requests.post(ENDPOINT + "/login", json=payload)
    json_response = response.json()
    assert json_response.get("status") == "200"

    token = json_response.get("token")
    headers= {"Authorization": "Bearer "+ token}
    payload = {
        "username": "unitTestUser",
        "password": "unitTestPass",
        "email": "unitTest@gmail.com",
        "token": token
    }
    response = requests.post(ENDPOINT + "/logout", json=payload, headers=headers)
    json_response = response.json()
    assert json_response.get("status") == "200"






    
    






















    
    





