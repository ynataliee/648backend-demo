from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

from langchain_openai import ChatOpenAI
from langchain.output_parsers import ResponseSchema # (1)
from langchain.output_parsers import StructuredOutputParser #(2) 
# used to define types/type hints
from typing import List
import json
# loading env variables
from dotenv import load_dotenv
load_dotenv()

# creating an instance of open ai chat model, as opposed to the non chat llm
# we were using before that sucked
chat = ChatOpenAI(temperature=0.8)

# defining schemas for each part of the structured response from the LLM
title_schema = ResponseSchema(name="projTitle", description="This is the name of the project that you generated for the user.", type='str')
summary_schema = ResponseSchema(name="projSummary", description="This is a short summary/description of the project generated.", type='str')
techStack_schema = ResponseSchema(name="techStack", description="This is a list of the tech stack to be used for completing the project. Each item in the tech stack is an element in a list of strings.",type='List[str]')
step_schema = ResponseSchema(name="steps", description="""each step name in the project instructions will be a key in a dictionary where the values are a list of strings with the instructions for that step. For example: 
2. Design the frontend interface to display a map.
   - How to: Utilize Mapbox GL JS or Leaflet to add a map component to your React app.
     - For Mapbox GL JS, refer to the official documentation: https://docs.mapbox.com/mapbox-gl-js/api/
     - For Leaflet, refer to the official documentation: https://leafletjs.com/reference-1.7.1.html 
     this step would have the following format as a dictionary:
     "{'2. Design the frontend interface to display a map.': ['- How to: Utilize Mapbox GL JS or Leaflet to add a map component to your React app.','For Mapbox GL JS, refer to the official documentation: https://docs.mapbox.com/mapbox-gl-js/api/', ect... ]} """, type='Dict[str, List[str]]')

# List of ResponseSchemas to be used by StructuredOutputParser to parse the output of LLM
response_schemas = [title_schema, summary_schema, techStack_schema, step_schema]
# returns a StructuredOutputParser using the list of ResponseSchema Objects - this is how StructuredOutputParsers are constructed
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
# returns the format instructions str
format_instructions = output_parser.get_format_instructions()

# define the template for the prompt to be used by the chat model
template = (
    """
I will give you the job description of the following internship I want, what specific project can I make that will demonstrate knowledge talked about in 
the description. Create a coding project I can do that will help me stand out to the recruiter, provide step by step instructions on how to complete the 
project and be specific about what the project is, do not generalize. Also include a modern tech stack, emphasis on the modern part and resources to help me get started. Please develop 
descriptive and in depth steps to accomplish the project.
Here is the internship description: {jobDescription}

Here is also some information about me that could be helpful in generating this project: {userContext}
Create a list of steps for the user to do to do the project. Once you have the list of steps, ask yourself how would you further instruct a student on how to do 
those steps. Using the answer to how you would go about doing each step, create the project instructions using these. Once you have a project for me to do, analyze 
the project you have and ask yourself if you could start coding the project right away. If you cannot then the project you created is not detailed and does not have 
specific enough instructions. In this case create another version of the project I could do with better steps so that I can actually do it. 

{formatInstructions}
"""
)

# what would happen if we swapped the contents of the human template and system template -> better results??
system_message_prompt = SystemMessagePromptTemplate.from_template(template)
human_template = "{userContext}"
human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

# this is specifically a prompt template for chat models, for our purposes, chat models give better
# project generations, the llm version kinda sucks in project generation  
chat_prompt = ChatPromptTemplate.from_messages(
    [system_message_prompt, human_message_prompt]
)

def generateProjects(job, userContext="No additional info at this moment"):
    # get a chat completion from the formatted messages
    response = chat.invoke(
        chat_prompt.format_prompt(
            jobDescription=job, userContext=userContext, formatInstructions=format_instructions
        )
    )

    response_as_dict = output_parser.parse(response.content)
    # Convert dictionary to JSON format
    response_as_json = json.dumps(response_as_dict)
    return response_as_json