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
from BaseModel import Task, QAandFlashCardsModel, StudyPlannerModel

# id and agent_name
mapper = {
    1 : 'Researcher',
    3 : 'Materials',
    5 : 'END'
}

material_mapper = {
    1 : "QAandFlashCards",
    2 : "StudyPlanner",
    3 : "END"
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


class StudyPlannerState(TypedDict):
    goal : str
    key_points : list[str] = Field(description="contains the key points of the plan of the topic to study made by the studyPlanner")
    content : StudyPlannerModel

class QAandFlashCardsState(TypedDict):
    goal : str
    QAandFlashCards : QAandFlashCardsModel


# MaterialGraph (Q/A_and_flashcards and study planner))
class MaterialsState(TypedDict):
    # sub-goal given by the supervisor(Helper Supervisor)
    agent_ids : Annotated[list[int], operator.add]
    sub_goal : str
    StudyPlanner : StudyPlannerState
    QAandFlashCards : QAandFlashCardsState


class RAGState(TypedDict):
    pass

class YoutubeState(TypedDict):
    pass

# Main State
class State(TypedDict):
    goal : str
    title : str
    need_RAG : bool
    agent_ids : Annotated[list[int], operator.add]
    Researcher : ResearchState
    # YoutubeAgent : Youtube_agent_type
    Materials : MaterialsState