# loading env variables
from dotenv import load_dotenv
load_dotenv()
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from langchain.output_parsers import ResponseSchema 
from langchain.output_parsers import StructuredOutputParser 
# used to define types/type hints
from typing import List

model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.9)

prompt1 = """ 
Can you tell me what are some of the things I would be doing for the following internship description, in terms of both technical skills 
and soft skills for example, "good communication skills". Here is the internship description:
{jobDescription}
"""

prompt2 = """ 
I will give you some skills/responsibilites from an internship description. Ask youself if the technical skills here are too complicated for a 
computer science student to understand. If they are, can you explain what the 
technical responsibilites in a simple way. Then give me an example of what the student would be doing for each technical responsibility so they get a 
better idea of each responsibililty means. If they are already not too complicated then create an example task of what the student would be 
doing for each of the skills. Here are the skills:
{skillsSummary}
Here is the job description for your reference: {jobDescription}
Here is some information about the experience for the student to help in your reply: {userContext}
"""

prompt3 = """ 
Out of the example tasks for a set of job requirements that I will give you, which example would be the most realistic that a student could do a 
coding project over that is still relevant to the internship? Here is the set of example tasks a student would be doing for a particular internship
description:
{exampleTasks}

Here is context about the student and thier level of experience: {userContext}

Here is the internship description these example tasks came from:
{jobDescription}

Please pick an example task or two to create a coding project for the student given thier experience and have the project relate to the internship
please use the example tasks to help you do this.
"""

prompt4_v2 = """ 
I have these project ideas in order to target certain internships I want to apply to and standout: 
{projectIdeas}
This is the end of the project ideas.

Now here are the descriptions of the internships that I want to target with these projects:
{jobDescriptions}
This is the end of the jobDescriptions

Try to combine these projects that are targeting the above internships into one project. The new project must be  
realistic for a student with the following skills and skill level and still relate to the all the internships being applied too: {userContext}

In your response please list the technologies, frameworks, libraries and overall tech stack need to complete the project. 
"""

prompt5_v2 = """ 
Your task is to evaluate the following project idea to see if it is realistic for a student with this experience {userContext} to do.
Here are some questions and guidance to help you do this:

Are there are multiple programming languages involved? If so select the programming language that can best accomplish what needs to be done.
For example if you have python and java, just pick one since you can do almost all the same things with either one, do not make the project more 
complex by adding another programming language when you do not need to. 

For each technology/framework or library in the project ask yourself if the student could realistically learn this tech while going to school on 
a full time schedule and given thier level of experience.
List your reasoning for why you should or should not include each piece of technology or library you have in the new project.

What internships is this project targeting that is mentioned in the projectIdea?

With the information you have gathered modify the project details to fit the reasoning you have gathered. Restate the project idea and the learning objectives
related to each of the internships in the orginal project idea but tailored to the new version of the project idea. Make sure to state how the updated project aligns and
targets the internships. Name the internships identified.
Here is the project idea:
{projectIdea}

Here are the format instructions: {formatInstructions_5v2}
"""
#Does the project use a modern tech stack for the given task? Replace outdated tech with more modern tech that the student should learn if it would be beneficial to
#what is required in the internship.

prompt6 = """ 
can you give step by step detailed instructions for what a student would need to do to complete the following project. Provide resources 
for the instructions, do not just say things like "attain a dataset" say what kind of dataset and where to get the dataset, 
include libraries the student could use to accomplish a certain step. Do not say things like learn about X topic, be more specific than that. The step by step instructions
should be in a tutorial like form with lots of details. For each technology or framework or library include what its purpose is related to the project:

Here is the project idea:
{projectIdea}

Also create three resume bullet points about the project you generate that the user can put on thier resume. Only include three resume bullet points, be concise and clear with the 
resume bullet points.

{formatInstructions}
"""

targetInternships = ResponseSchema(name="targetInternships", description="These are the internships that are mentioned or targeted by the project idea. This is list [Company 1 postion a, company 2 position b]", type='List[str]')
relevance = ResponseSchema(name="relevance", description="This is a summary of the relevance of the new project and how it aligns to the internships it targets",type='str')
reasoning = ResponseSchema(name="reasoning", description="This is a summary of your reasoning for why the project is suitable for the user and also relevant to the target interships",type='str')
updatedProject = ResponseSchema(name="updatedProject", description="This is the restated or updated project idea you came up with given your reasoning that include the learning objectives, title of project and the project idea itself",type='str')
skillReasoning = ResponseSchema(name="skillReasoning", description="This is where you put the reasoning you have to include or not include each technology/framework/library in the updated project to keep the project realistically doable. The format should be a list of strings where each item in the list is the reasoning for each skill.", type='List[str]')
responseSchemas_5v2 = [targetInternships, relevance, reasoning, updatedProject, skillReasoning]
# returns a StructuredOutputParser using the list of ResponseSchema Objects - this is how StructuredOutputParsers are constructed
output_parser_5v2 = StructuredOutputParser.from_response_schemas(responseSchemas_5v2)
# returns the format instructions str
format_instructions_5v2 = output_parser_5v2.get_format_instructions()

input_prompt1 = ChatPromptTemplate.from_template(prompt1)
input_prompt2 = ChatPromptTemplate.from_template(prompt2)
input_prompt3 = ChatPromptTemplate.from_template(prompt3)

chain1 = input_prompt1 | model | StrOutputParser() 
chain2 = (
    {"skillsSummary": chain1, "userContext":itemgetter("userContext"), "jobDescription": itemgetter("jobDescription")}
    | input_prompt2
    | model
    | StrOutputParser()
)

chain3 = (
    {"exampleTasks": chain2, "userContext": itemgetter("userContext"), "jobDescription": itemgetter("jobDescription")}
    | input_prompt3
    | model
    | StrOutputParser()
)

""" 
This returns the first version of the project ideas for each internship description.
"""
def getDemoProjects(job, userContext):
    response = chain3.invoke({"jobDescription": job, "userContext": userContext})
    return response

""" 
This takes in the demo projects for each individual internship descriptions and the original internship descriptions 
for each job. 
"""
def combinedProjects(demoProjects, jobs, userContext):
    input_prompt4_v2 = ChatPromptTemplate.from_template(prompt4_v2)
    chain4 = input_prompt4_v2 | model | StrOutputParser() 
    combinedProjs = chain4.invoke({"projectIdeas": demoProjects, "userContext": userContext, "jobDescriptions": jobs})
    return combinedProjs 

applyLinksSchema = ResponseSchema(name= "job_apply_links", description="This is the field where the links given to apply to the job description should be placed, you can find these links in each job description under job apply link. You should put these in an array of links for the final response, for example: job_apply_links: [link1, link2, etc..]")
title_schema = ResponseSchema(name="projTitle", description="This is the name of the project that you generated for the user.", type='str')
target_skills = ResponseSchema(name="targetSkills", description="This is a list of the skills you used from skills extracted to create the project, these are the skills you found in common, include the compnay that each skill came from.")
skills_extracted = ResponseSchema(name="skillsExtracted", description="These are the skills extracted that you recieved for this step, please put them here in the original format you recieved them in.")
summary_schema = ResponseSchema(name="projSummary", description="This is a short summary/description of the project generated.", type='str')
techStack_schema = ResponseSchema(name="techStack", description="This is a list of the tech stack to be used for completing the project. Each item in the tech stack is an element in a list of strings.",type='List[str]')
step_schema = ResponseSchema(name="steps", description="""each step name in the project instructions will be a key in a dictionary where the values are a list of strings with the instructions for that step. For example: 
2. Design the frontend interface to display a map.
   - How to: Utilize Mapbox GL JS or Leaflet to add a map component to your React app.
     - For Mapbox GL JS, refer to the official documentation: https://docs.mapbox.com/mapbox-gl-js/api/
     - For Leaflet, refer to the official documentation: https://leafletjs.com/reference-1.7.1.html 
     this step would have the following format as a dictionary:
     "{'2. Design the frontend interface to display a map.': ['- How to: Utilize Mapbox GL JS or Leaflet to add a map component to your React app.','For Mapbox GL JS, refer to the official documentation: https://docs.mapbox.com/mapbox-gl-js/api/', ect... ]} """, type='Dict[str, List[str]]')
resumeBulletPoints = ResponseSchema(name="resumeBulletPoints", description="This is where you put the generated resume bullet points for the project that was generated. This will be a list of strings where each string is a bullet point.", type='List[str]')
# List of ResponseSchemas to be used by StructuredOutputParser to parse the output of LLM
responseSchemas2 = [title_schema, summary_schema, techStack_schema, step_schema, applyLinksSchema, targetInternships, reasoning, resumeBulletPoints]
# returns a StructuredOutputParser using the list of ResponseSchema Objects - this is how StructuredOutputParsers are constructed
output_parser2 = StructuredOutputParser.from_response_schemas(responseSchemas2)
# returns the format instructions str
format_instructions2 = output_parser2.get_format_instructions()

# takes in combined project idea and user context
# returns updated project that is more realistic 
def evaluateCombinedProj(combinedProj, userContext):
    input_prompt5_v2 = ChatPromptTemplate.from_template(prompt5_v2)
    chain5 = input_prompt5_v2 | model | StrOutputParser() 
    updatedProj = chain5.invoke({"userContext": userContext, "projectIdea": combinedProj, "formatInstructions_5v2": format_instructions_5v2})
    return updatedProj

def getFinalProj(updatedProj):
    input_prompt6 = ChatPromptTemplate.from_template(prompt6)
    chain6 = input_prompt6 | model
    finalProj = chain6.invoke({"projectIdea": updatedProj, "formatInstructions": format_instructions2})
    response_as_dict = output_parser2.parse(finalProj.content)
    return response_as_dict
