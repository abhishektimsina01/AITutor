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
from Structure.TypedDict import MaterialsState, material_mapper, StudyPlannerState
from Structure.BaseModel import material_sub_goal_schema, study_step_schema, study_planner_schema, QA_schema
from tools import llm

def MiniSuervisor(state : MaterialsState):
    # get the sub-goal from the user and this will chose which agent to route the goal to with what goal.
    sub_goal = state['sub_goal']
    agent_ids = state.get("agent_ids", [])
    print(agent_ids)
    record = {}
    for agent_id in material_mapper:
        if not agent_id in agent_ids:
            record[agent_id] = material_mapper[agent_id]
    prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Supervisor Agent.

    Your job is to select EXACTLY ONE worker agent to handle the given goal.

    ------------------------
    ALL AGENTS:
    1. QAandFlashCards → Generate Q/A or flashcards
    2. StudyPlanner → Create study roadmap
    3. END → Use ONLY if no valid agent remains
    ------------------------

    ALREADY USED AGENTS:
    {agent_ids}

    AVAILABLE AGENTS (ONLY CHOOSE FROM HERE):
    {record}

    ------------------------
    STRICT RULES:
    - You MUST select ONLY ONE agent from AVAILABLE AGENTS
    - NEVER select an agent that is already used
    - If ALL meaningful agents are already used → select END
    - Do NOT invent new agents
    - Do NOT ignore AVAILABLE AGENTS list
    - Do NOT return anything except valid JSON

    ------------------------
    Decision Logic:
    1. Check if a suitable agent exists in AVAILABLE AGENTS
    2. If yes → choose it
    3. If no → choose END

    ------------------------
    Return format:
    {format}
    """),
    ("human", "goal: {sub_goal}")
]).partial(format=material_sub_goal_schema.get_format_instructions())
    chain = prompt | llm | material_sub_goal_schema
    result = chain.invoke({"record" : record, 'sub_goal' : sub_goal, "agent_ids" : agent_ids})
    # if study and qa/flashcard agent are already then dont add them
    if 1 in agent_ids or 2 in agent_ids:
        print("agent already used")
        print("Material Supervisor ✅")
        return {'agent_ids' : [3]}
    else:
        print("Material Supervisor ✅")
        return {'agent_ids' : [result.id], result.agent : {'goal' : result.sub_goal}}


def StudyPlanner(state : MaterialsState):
    print("StudyPlanner reached✅")
    sub_goal = state.get("StudyPlanner", {}).get("goal", "")
    print(sub_goal)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert in planning a study roadmap in various topics. You will get a goal and you have to generate a roadmap that is helpful.\n
         ****Rules****"
         - You will generate a roadmap from basic to advance or course based roadmap targetting beginners and intermediate if not mentioned in goal.
         - You will generate a answer in given format and the content should contain multiple points not like topic with sub-topics.\n
         ****Format****
         - plan : {plan} (list of steps)
         - step : {step} (format of step)
         """),
        ("human", "goal : {sub_goal}")
    ]).partial(step = study_step_schema.get_format_instructions(), plan = study_planner_schema.get_format_instructions())
    chain = prompt | llm | study_planner_schema
    result = chain.invoke({'sub_goal' : sub_goal}).roadmap
    key_points = []
    plan = []
    for step in result:
        key_points.append(step.sub_goal)
        plan.append({
            'id' : step.id,
            'sub_goal' : step.sub_goal,
            'content' : step.content 
        })

    study_planner_state : StudyPlannerState= {
        'goal' : sub_goal, 
        'key_points' : key_points,
        'content' : {
            'roadmap' : plan
        }
    }
    print(study_planner_state)
    print("Study Planner ✅")
    return {"StudyPlanner" : study_planner_state}


def QAandFlashCards(state : MaterialsState):
    sub_goal = state.get("QAandFlashCards", {}).get("goal", "")
    prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a educational researcher agent that can make "
    "1.Question Answer and "
    "2.flashcards "
    "but only one of the two can be used"
    "You will get a goal and u have to analyze the goal and decide whether to produce interview based question / answer, exam style question answer etc or the study helper flashcard"
    "****Format*****"
    "{qa}"
    "****RULE****"
    "for flashcards there should be one or two word answer max"),
    ("human", "goal : {goal}")
    ]).partial(qa = QA_schema.get_format_instructions())
    chain = prompt | llm | QA_schema
    result = chain.invoke({'goal' : sub_goal})
    print(result)
    print("QA and Flashcards ✅")
    data = {
            'goal' : sub_goal,
            'QAandFlashCards' : {
                'question' : result.question,
                'answer' : result.answer
            }
    }
    return {'QAandFlashCards' : data}
    
def SubAgentSelection(state : MaterialsState):
    # print(state.get('agent_ids', []))
    agent_id = state['agent_ids'][-1]
    print("Agents that are used are: ", agent_id)
    print("next agent--->", material_mapper[agent_id])
    print("Routing completed Supervisor ✅")
    if agent_id == 1:
        return "QAandFlashCards"
    
    elif agent_id == 2:
        return "StudyPlanner"
    
    else:
        return "END"

subGraph = StateGraph(MaterialsState)
subGraph.add_node("MiniSupervisor", MiniSuervisor)
subGraph.add_node("StudyPlanner", StudyPlanner)
subGraph.add_node("QAandFlashCards", QAandFlashCards)

subGraph.add_edge(START, "MiniSupervisor")
subGraph.add_conditional_edges("MiniSupervisor", SubAgentSelection,{"QAandFlashCards" : "QAandFlashCards", "StudyPlanner" : "StudyPlanner", "END" : END})
subGraph.add_edge("QAandFlashCards", "MiniSupervisor")
subGraph.add_edge("StudyPlanner", "MiniSupervisor")

subSystem = subGraph.compile()

subSystem