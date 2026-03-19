# this will contain all the tools required by all agentsfrom langchain_core.tools import tool
from langchain_tavily import TavilySearch
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()   


llm = ChatGroq(
    api_key=os.getenv("api_key"),
        model="llama-3.3-70b-versatile"
)

tavily_research_tool = TavilySearch(max_results=3, include_answer= True, search_depth= "advanced", auto_parameters=True)


# making dictionary for each of the agents tool
# research agent
research_tools = [tavily_research_tool]
research_tools_by_name = {tool.name : tool for tool in research_tools}

# task_specific_agent
materials_tools = []
materials_tools_by_name = {tool.name : tool for tool in materials_tools}

#rag_agent
rag_tools = []
rag_tools_by_name = {tool.name : tool for tool in rag_tools}

# youtube_agent
youtube_tools = []
youtube_tools_by_name = {tool.name : tool for tool in youtube_tools}


# LLM for each agents with tools binded to it
llm = ChatGroq(model= os.getenv("model"), api_key=os.getenv("api_key"))
research_agent_with_tool =  llm.bind_tools([tavily_research_tool])
rag_agent_with_tool = llm.bind_tools(rag_tools)
youtube_agent_with_tool = llm.bind_tools(youtube_tools)
task_agent_with_tool = llm.bind_tools(materials_tools)