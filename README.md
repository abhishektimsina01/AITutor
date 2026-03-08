AI Tutor is a Multi-Agent System(MAS) that contains of multiple specialized autonomous agents, that performs different speacialized task for providing a learning environment to the students with the help of different tools.

MAS is a agentic asrchitecture that contains of two roles:-
1. Supervisor(Orchestrator)
2. Workers
The supervisor will supervise the workers agents and the aggregate the result as one.

Here, i will apply many advanced LangGraph topics:- 
- Supervisor-Workers Architecture(Multi-Agent System) with dynamic routing using 'Command' types
- Short-term and Long-term memory
- Many advanced tools like searching tools
- scrapping tools,
- external APIs as tools, 
- advanced multi-modal agentic RAG system,
- Human In The Loop(When human support required) and Fault Tolerence(If apis dont respon)
- Adaptability(Sudden changes done during execution)


I will try to build the whole system in the following Tech-stack:- 
- Database for user data as, normal data + references + previous chats(i/o) + threads(if required later)
- FrontEnd using React(Probably AI) or Streamlit
- Backend using Django(Django REST Framework) or TypeScript(Node) or FastAPI(Best for AI backend)
- Agentic System in '.py' file

But for that i need to understand how should my goal need to be distributed on the basis of the given task from the user.
- How the system should set the goal?
- How the goal should be divided into sub-goals that is to be provided to speacialized agents?
- How should the supervisor dynamically route each task to the corresponding agents and only to the required agents?
- How will the Supervisor choose which agent is required and which agent should be left to be idle (cost efficient)? 
- Should we do it parallely or sequentially? (that will be known from the data the autonomous agents demand with the sub-goal)
- How to synthesize it in one(either through supervisor or synthesizer)

The main goal is to know about the routing the orchestrator do, based upon the agents. And how do the agents run parallely.
We can have more complex agents than the ReAct agent so we will need to create sub-graph for the agents Sub -agents on the basis of(LangGraph documentation) and as well as we will require to implement parallel working of required agents.


AI Tutor is a MAS project which consists of multiple speacialzed agents that work to provide different sources of data
- research
- Agentic RAG(document-based)
- scraping and processing it
- Youtube recommendation with little summary of 1 or 2 videos most relevant too
- Coding Agent
- Just Communication
And many more.
The prebuilt, create_react_agent wont be enough for the work.
