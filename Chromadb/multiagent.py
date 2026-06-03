import os
from typing import Annotated, List, Tuple, TypedDict, Union
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END, START

load_dotenv()

llm = ChatGroq(model_name="llama-3.3-70b-versatile", groq_api_key=os.getenv("GROQ_API_KEY"))

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    next_agent : str

def research_agent(state: AgentState):
    print("Researching....")
    response = llm.invoke(state['messages'] + [HumanMessage(content="Provide a brief technical fact about Groq LPUs.")])
    return {"messages": [response]}

def coding_agent(state: AgentState):
    print("Coding....")
    response = llm.invoke(state['messages'] + [HumanMessage(content="Write a simple python code")])
    return {"messages": [response]}

def supervisor_router(state : AgentState):
    print("Supervising....")
    prompt = "Based on user request should we call the 'researcher', the 'coder', or 'FINISH'?"
    last_message = state['messages'][-1].content.lower()
    if "code" in last_message:
        return  "coder"
    elif "fact" in last_message:
        return  "researcher"
    return "FINISH"

workflow = StateGraph(AgentState)

workflow.add_node("researcher", research_agent)
workflow.add_node("coder", coding_agent)

workflow.set_entry_point("researcher")
workflow.add_conditional_edges("researcher", supervisor_router, {"coder": "coder", "researcher": "researcher", "FINISH": END})
workflow.add_edge("coder", END)

app = workflow.compile()


if __name__ == "__main__":
    inputs = {"messages": [HumanMessage(content="I need info on Groq and some code.")]}
    
    for output in app.stream(inputs):
        print(output)
    
