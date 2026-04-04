from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Literal

# BaseModels

class Task(BaseModel):
    '''contains information of each step of the plan'''
    id : int = Field(description="id of the step")
    goal : str = Field(description="goal that the user needs to reach after reding the task's answer")
    tool_required : bool = Field("True if research tool is required and False if not")

task_schema = PydanticOutputParser(pydantic_object=Task)

class Plan(BaseModel):
    '''list of plan'''
    plan : list[Task]

plan_schema = PydanticOutputParser(pydantic_object=Plan)

class Goal(BaseModel):
    '''contains the goal for the particualr agent with name of the agent'''
    # title : str = Field(description = "name or title based upon the user query")
    id : int = Field(description = "id of the agent in integer")
    agent : Literal['Researcher', 'RAG', 'Materials', 'YoutubeAgent', 'END'] = Field(description="one specific agent that is to be choosen for the work")
    sub_goal : str = Field(description = "goal that is provided the to the specific one agent")

sub_goal_schema = PydanticOutputParser(pydantic_object=Goal)

class RAG_agent_type(BaseModel):
    pass


class Youtube_agent_type(BaseModel):
    pass


class StudyStep(BaseModel):
    id : int = Field(description="step of the plan")
    sub_goal : str = Field(description="topic of the step")
    content : str = Field(description="Content of the topic in sub-points")

class StudyPlannerModel(BaseModel):
    roadmap : list[StudyStep] = Field("Contains list of step of the roadmap")

study_step_schema = PydanticOutputParser(pydantic_object=StudyStep)
study_planner_schema = PydanticOutputParser(pydantic_object=StudyPlannerModel)

class QAandFlashCardsModel(BaseModel):
    question : list[str] = Field(description="list of question")
    answer : list[str] = Field(description="list of asnwers")

QA_schema = PydanticOutputParser(pydantic_object=QAandFlashCardsModel)

class MaterialGoal(BaseModel):
    '''contains the goal for the particualr agent with name of the agent'''
    id : int = Field(description = "id of the agent in integer")
    agent : Literal['QAandFlashCards', "StudyPlanner", "END"] = Field(description="one specific agent that is to be choosen for the work")
    sub_goal : str = Field(description = "goal that is provided the to the specific one agent")

material_sub_goal_schema = PydanticOutputParser(pydantic_object=MaterialGoal)