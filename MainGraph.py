from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Literal, TypedDict, Optional, List, Annotated
from langchain_ollama import OllamaEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage, BaseMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from langgraph.graph.message import add_messages
from langgraph.types import Command, Interrupt
from dotenv import load_dotenv
import os
import json
from Structure.BaseModel import sub_goal_schema
from Structure.TypedDict import State, mapper, llm
from SubGraphs.ResearcherGraph import ResearcherSubGraph

# FOR THE SUPERVISOR NODE
def Supervisor(state : State):
    goal = state['goal']
    researcher = state.get('Researcher', {}).get("key_points", [])
    agent_ids = state.get('agent_id', [])
    record = {}
    for agent_id in mapper:
        if agent_id in agent_ids:
            record[agent_id] = "used"

    print("Already used agents :", agent_ids)
    print(goal)
    print(researcher)
    prompt = ChatPromptTemplate([
        ('system', """You are a supervisor agent for an AI Tutor and you have a bunch of specialized agents:\n\n
         ****Specialized agents(worker agents) id and their speciality****
         1 --> Researcher : Research on the topics (research that required llm knowledge and research tools)
         5 --> END : If no any agents is required now.\n\n
        
         Now you have to choose one of the above agents based upon the user query and agent specialization/use. \n\n

         ****Specialized agents(worker agents) name and their work till now*****
         Researcher : {researcher_work}
         
         Very important Note : If there is [] with no elements in any of the agent, that means the agent hasn't been used yet. \n\n
         
         ****Agents state****
         {record}

         "used" cannot be used again
         ****Structure****
    
         To provide the specific agent you have to return the goal in the following structure\n

         {format}\n\n

        ****Rules****
         
         - Don't use already used agents
         - Only provide goal to the specialized agent goal when the query seems to demand.
         - Depending upon the user query, its meaning(as you are Tutor) and work done by workers till now, you must call only the required agent at a time,
         - Dont use the used agent twice.

         """),
        ('human', "Goal/Query from user : {goal}")
    ]).partial(format = sub_goal_schema.get_format_instructions(), researcher_work  = researcher, record = record)
    print("⚠️"*50)
    print(prompt.invoke({'goal' : goal}))
    print("⚠️"*50)
    # Generate the title for it
    chain = prompt | llm | sub_goal_schema
    response = chain.invoke({'goal' : goal})
    print('Supervisor Completed ✅')
    print(type(response.id))
    return {'agent_ids' : [response.id], response.agent : {'sub_goal' : response.sub_goal}}

# FOR THE RESEARCH NODE
# it should be complex as its job is not only to extract one knowledge but many aspects like what, how, why, when, exmaples, mechanism etc.
def Researcher(state : State):
    sub_goal = state['Researcher']['sub_goal']
    print("Researcher agent's Goal: ",sub_goal)
    response = ResearcherSubGraph.invoke({'sub_goal' : sub_goal})
    print(response)
    print('Research Completed ✅')
    return {'Researcher' : {
        'sub_goal' : response['sub_goal'],
        'agent_plan' : response['agent_plan'],
        'agent_explain' : response['agent_explain'],
        'key_points' : response['key_points']
    }}

# FOR THE YOUTUBEVIDEOS NODE
def Materials(state : State):
    # We make subgraph as it will contain multiple agents in side the TaskSpecific agent:
    # Sub-Supervisor
    # Worker Agents:
        # Q/A and FlashCards
        # StudyPlanner
    # All agents will have same tool as not needed much
    pass

def YoutubeVideos(state : State):
    pass

# FOR THE RAG AGENT
def RAG(state : State):
    # we have retriever that is used to retrieve the corresponding queries asnwer from the document
    pass

# at the end when all the task are completed then all the results from each agent are synthesized into proper format
def Synthesizer(state : State):
    print("Synthesizer ✅")

    return {}
    # At last synthesize the whole blog/goal that are broken down and submitted to all the agents into one single organized form

def AgentSelection(state : State):
    agent_id = state['agent_id'][-1]
    print("agent id",type(agent_id))
    print("next ---->", agent_id)
    if agent_id == 1:
        return "Researcher"
    elif agent_id == 2: 
        return "RAG"
    elif agent_id == 3:
        return "TaskSpecific"
    elif agent_id == 4:
        return "YoutubeAgent"
    else:
        return "Synthesizer"

graph = StateGraph(State)
graph.add_node("Supervisor", Supervisor)
graph.add_node("Researcher", Researcher)
graph.add_node("Materials", Materials)    
graph.add_node("RAG", RAG)
graph.add_node("YoutubeVideos", YoutubeVideos)
graph.add_node("Synthesizer", Synthesizer)

graph.add_edge(START, "Supervisor")
graph.add_conditional_edges("Supervisor", AgentSelection, {"Researcher" : "Researcher", "RAG" : "RAG", "YoutubeVideos" : "YoutubeVideos", "Materials" : "Materials", "Synthesizer" : "Synthesizer"})
graph.add_edge("Researcher", "Supervisor")
graph.add_edge("RAG", "Supervisor")
graph.add_edge("Materials", "Supervisor")
graph.add_edge("YoutubeVideos", "Supervisor")
graph.add_edge("Synthesizer", END)

MainGraph = graph.compile()

MainGraph

