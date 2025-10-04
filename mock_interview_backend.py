# mock_interview_backend.py
from langgraph.graph import StateGraph, START, END
from typing import Annotated, TypedDict, List, Literal
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver


# Define the state for our graph
class ChatState(TypedDict):
    role: Literal[
        "Software Engineer", 
        "Web Developer", 
        "Frontend Developer", 
        "Backend Developer",
        "AI/ML Engineer",
        "Data Scientist"
    ]
    domain: Literal[
        "SDE",
        "Web Development",
        "Frontend",
        "Backend",
        "AI/ML",
        "Data Science"
    ]
    level: Literal[
        "Entry Level", 
        "Mid Level",
        "Senior Level"
    ]
    messages: Annotated[List[BaseMessage], add_messages]


# Factory to build chatbot
def get_chatbot():
    llm = ChatGroq(model="gemma2-9b-it")

    def chat_node(state: ChatState) -> ChatState:
        """LangGraph node: generates a reply based on chat state."""
        messages = state["messages"]

        # ✅ Add system prompt only ONCE (when no previous messages exist)
        if not any(isinstance(msg, SystemMessage) for msg in messages):
            system_prompt = (
                f"You are an Interview Bot for a {state['role']} candidate.\n"
                f"Domain: {state['domain']}\n"
                f"Level: {state['level']}\n"
                "Firstly greet the candidate only first time and make him comfortable"
                "Your job is to ask relevant interview questions, give hints, and share model answers when asked. "
                "Keep it interactive, professional, and focused on interview preparation."
                "If he has answered well enough so ask the next questions"
            )
            messages.insert(0, SystemMessage(content=system_prompt))

        # Call the LLM
        response = llm.invoke(messages)
        return {"messages": [response]}

    # Build the LangGraph
    graph = StateGraph(ChatState)
    graph.add_node("chat_node", chat_node)
    graph.add_edge(START, "chat_node")
    graph.add_edge("chat_node", END)

    # Memory to persist state (role/domain/level/messages)
    checkpointer = InMemorySaver()
    chatbot = graph.compile(checkpointer=checkpointer)

    return chatbot, checkpointer
