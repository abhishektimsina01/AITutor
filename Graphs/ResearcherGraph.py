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
from Structure.BaseModel import plan_schema, task_schema
from Structure.TypedDict import ResearchState
from tools import research_agent_with_tool, research_tools_by_name, llm

def Planner(state : ResearchState):
    goal = state['sub_goal']
    # prompt = PromptTemplate(template="goal : {sub_goal} \n\n{format}", input_variables=['sub_goal'], partial_variables={"format" : task_schema.get_format_instructions()})
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You as an excellent planner agent that can generate a beautiful productive plan to give to the worker agents to execute on the basis of your plan. Workers agents will explain based on you plan so make the plan good. 
         Total number of steps must be less than 7. \n
         
         ****TOOL USAGE RULE****
            Set "tool_required" = true ONLY if the goal includes ANY time-dependent intent.

            Time-dependent means:
            - current
            - latest
            - recent
            - today
            - now
            - trending
            - live
            - real-time
            - updated information

            If ANY of these appear or are implied → tool_required = true

            Otherwise (theoretical, general, timeless knowledge) → tool_required = false

            You MUST strictly follow this mapping.\n
                    
         ***Structure***
         Just give me list of steps in the following JSON format:\n
        {plan}\n\n
         where each task is in the form of:\n
         {task}"""),
        ("human", "Goal : {goal}")]).partial(plan = plan_schema.get_format_instructions(), task = task_schema.get_format_instructions())
    chain = prompt | llm | plan_schema
    plan = chain.invoke({'goal' : goal}).plan
    print(plan)
    key_points = []
    agent_plan = []
    for step in plan:
        agent_plan.append({
            'id' : step.id,
            'goal' : step.goal,
            'tool_required' : step.tool_required
        })
        key_points.append(step.goal)
    print(agent_plan)
    return {'agent_plan' : agent_plan, 'key_points' : key_points}


def Researcher(state : ResearchState):
    plan = state['agent_plan']
    explaination = []
    prompt = ChatPromptTemplate.from_messages([
        ('system', """
    You are a **Research & Explanation Agent**.

    You will receive **one task at a time**. Your job is to produce content that directly satisfies the goal.
    Rules:
    - Focus only on the current task. Do not explain unrelated concepts.
    - Adapt explanation to goal type: definition, math, numeric example, summary, etc.
    - Output concise, relevant explanation. No forced headings, templates, or extra text.
    """),
        ('human', "task : {task}")
    ])
    for step in plan:
        print(step)
        if step['tool_required'] == True:
            # do the llm call with the tool_required
            output = research_agent_with_tool.invoke(step['goal'])
            if not output.tool_calls :
                print("⚠️No tools called despite of the tool_required : TRUE")
                print(output.content)
            else:
                tool_recommended = output.tool_calls[0]
                tool_name = research_tools_by_name[tool_recommended['name']]
                tool_output = tool_name.invoke(tool_recommended['args'])['answer']
                print(tool_output)
                explaination.append(tool_output)
        else:
            chain = prompt | llm | StrOutputParser()
            # result = chain.invoke(step['goal'])
            message = HumanMessage(content=step['goal'])  # wrap goal
            result = chain.invoke([message])              
            print(result)
            explaination.append(result)

    return {'agent_explain' : explaination}

researchGraph = StateGraph(ResearchState)

researchGraph.add_node("Planner", Planner)
researchGraph.add_node("Researcher", Researcher)

researchGraph.add_edge(START, "Planner")
researchGraph.add_edge("Planner", "Researcher")
researchGraph.add_edge("Researcher", END)

ResearcherSubGraph = researchGraph.compile()
ResearcherSubGraph