# langgraph_agent.py - LangGraph agent with Anthropic Claude and RealXmarket docs tool
from typing import TypedDict, Annotated, List, Any
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import ToolMessage, SystemMessage, convert_to_messages
import os

# Tool: RealXmarket documentation search
@tool
def search_realxmarket_docs(query: str) -> str:
    """Search the official RealXmarket documentation at doc-hub.xcavate.io."""
    from realxmarket_docs import search_and_answer
    return search_and_answer(query)

# State definition
class AgentState(TypedDict):
    messages: Annotated[List[Any], add_messages]
    tool_output: str

# System prompt
SYSTEM_PROMPT = """You are a RealXmarket support assistant. Answer questions using only the official documentation.

When you don't know something, use the search_realxmarket_docs tool to find answers.

If documentation returns no results, say: "I couldn't find this in the RealXmarket documentation. Please contact RealXmarket support for assistance."

Be brief and professional."""

# LLM with tool binding - uses Anthropic API
def create_llm_with_tools(model_name: str = "claude-3-5-sonnet-20241022"):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    llm = ChatAnthropic(
        model=model_name,
        temperature=0.1,
        api_key=api_key
    )
    return llm.bind_tools([search_realxmarket_docs])

# Node: AI reasoning
def ai_node(state: AgentState, llm):
    messages = state["messages"]

    # Prepend system prompt if not already present
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    response = llm.invoke(messages)

    tool_calls = getattr(response, 'tool_calls', [])

    return {
        "messages": [response],
        "tool_output": "",
        "_has_tool_call": len(tool_calls) > 0
    }

# Node: Tool execution
def tool_node(state: AgentState):
    last_message = state["messages"][-1]

    if hasattr(last_message, 'tool_calls'):
        tool_calls = last_message.tool_calls
    else:
        tool_calls = []

    if not tool_calls:
        return {"tool_output": ""}

    tool_call = tool_calls[0]
    func_name = tool_call.get("name", "") if isinstance(tool_call, dict) else getattr(tool_call, 'name', '')
    args = tool_call.get("args", {}) if isinstance(tool_call, dict) else getattr(tool_call, 'args', {})

    if func_name == "search_realxmarket_docs":
        query = args.get("query", "") if isinstance(args, dict) else ""
        result = search_realxmarket_docs.invoke(query)
        return {"tool_output": result}

    return {"tool_output": ""}

# Node: Final answer after tool
def final_answer_node(state: AgentState, llm):
    tool_output = state.get("tool_output", "")
    messages = list(state["messages"])

    if tool_output:
        last_msg = messages[-1]
        tool_call_id = "call_001"

        if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
            tc = last_msg.tool_calls[0]
            tool_call_id = tc.get('id', 'call_001') if isinstance(tc, dict) else getattr(tc, 'id', 'call_001')

        messages.append(ToolMessage(
            content=tool_output,
            name="search_realxmarket_docs",
            tool_call_id=tool_call_id
        ))

    # Use LLM without tools for final answer
    from langchain_anthropic import ChatAnthropic
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    simple_llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        temperature=0.1,
        api_key=api_key
    )
    response = simple_llm.invoke(messages)
    return {"messages": [response], "tool_output": ""}

# Create workflow
def create_agent_graph(model: str = "claude-3-5-sonnet-20241022"):
    llm = create_llm_with_tools(model)

    workflow = StateGraph(AgentState)

    def ai(s): return ai_node(s, llm)
    def fa(s): return final_answer_node(s, llm)

    workflow.add_node("ai", ai)
    workflow.add_node("tool", tool_node)
    workflow.add_node("final_answer", fa)

    workflow.set_entry_point("ai")

    def should_use_tools(state):
        return "tools" if state.get("_has_tool_call", False) else "answer"

    workflow.add_conditional_edges(
        "ai",
        should_use_tools,
        {"tools": "tool", "answer": END}
    )

    workflow.add_edge("tool", "final_answer")
    workflow.add_edge("final_answer", END)

    return workflow.compile(checkpointer=None)

# Streaming version
def stream_agent_response(messages: List[dict], model: str = "claude-3-5-sonnet-20241022"):
    graph = create_agent_graph(model)

    for event in graph.stream(
        {"messages": messages},
        stream_mode="values"
    ):
        yield event
