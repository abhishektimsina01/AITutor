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
import operator
from BaseModel import Task

# id and agent_name
mapper = {
    1 : 'Researcher',
    5 : 'END'
}

# Research Graph
class ResearchState(TypedDict):
    # Sub-goal given by the supervisor
    sub_goal : str
    
    # plan made by the researcher agent
    agent_plan : Annotated[list[Task], operator.add]

    # explaination done by agent (either toolMessage or the AiMessage)
    agent_explain : Annotated[list[str], operator.add]

    # key points covered by this agent
    key_points : Annotated[list[str], operator.add]


# MaterialGraph (Q/A_and_flashcards and study planner))
class MaterialsState(TypedDict):
    # sub-goal given by the supervisor(Helper Supervisor)
    sub_goal : str


class RAGState(TypedDict):
    pass

class YoutubeState(TypedDict):
    pass

class TaskSpecificState(TypedDict):
    pass

# Main State
class State(TypedDict):
    goal : str
    title : str
    need_RAG : bool
    agent_id : Annotated[list[int], operator.add]
    Researcher : ResearchState
    YoutubeAgent : YoutubeState
    TaskSpecific : TaskSpecificState
