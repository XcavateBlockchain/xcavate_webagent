# langgraph_agent.py - LangGraph agent with OpenAI GPT-4o and RealXmarket docs tool
from typing import TypedDict, Annotated, List, Any
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
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
SYSTEM_PROMPT = """You are RealXmarket's customer support assistant. Help users with their account, transactions, wallet connections, and platform-related questions.

GUIDELINES:
- Answer clearly and helpfully in a friendly, professional tone
- Use ONLY official RealXmarket documentation - do not speculate or make up information
- When you don't know the answer, automatically use the search_realxmarket_docs tool to find it (no need to announce this to the user)
- If the documentation has no relevant results, honestly say: "I couldn't find this in the RealXmarket documentation. Please contact RealXmarket support for personalized assistance."
- For account recovery, security, KYC, transaction issues, and wallet problems - prioritize accurate info from docs
- Keep responses concise but complete - users want quick, clear answers
- If a question is outside RealXmarket's scope (general crypto advice, third-party services), politely redirect to RealXmarket-specific topics"""

# LLM with tool binding - uses OpenAI API
def create_llm_with_tools(model_name: str = "gpt-4o"):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    llm = ChatOpenAI(
        model=model_name,
        temperature=0.1,
        api_key=api_key
    )
    return llm.bind_tools([search_realxmarket_docs])

# Node: AI reasoning
def ai_node(state: AgentState, llm):
    messages = state["messages"]

    # Convert dict messages to LangChain message objects
    from langchain_core.messages import convert_to_messages
    messages = convert_to_messages(messages)

    # Prepend system prompt if not already present
    has_system = any(isinstance(m, SystemMessage) for m in messages)
    if not has_system:
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    # Print the full prompt being sent to the AI
    print("\n" + "="*60)
    print("FULL PROMPT SENT TO AI:")
    print("="*60)
    for msg in messages:
        role = type(msg).__name__
        content = msg.content[:200] + "..." if len(str(msg.content)) > 200 else msg.content
        print(f"\n[{role}]\n{content}")
    print("="*60 + "\n")

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
        print(f"\n[TOOL CALL] search_realxmarket_docs with query: {query}\n")
        result = search_realxmarket_docs.invoke(query)
        print(f"[TOOL RESPONSE] {result}\n")
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
    from langchain_openai import ChatOpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    simple_llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.1,
        api_key=api_key
    )
    response = simple_llm.invoke(messages)
    return {"messages": [response], "tool_output": ""}

# Create workflow
def create_agent_graph(model: str = "gpt-4o"):
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

# Streaming version - handles tool calls and streams tokens
def stream_agent_response(messages: List[dict], model: str = "gpt-4o"):
    from langchain_core.messages import SystemMessage, AIMessage, convert_to_messages

    # Convert messages
    msg_list = convert_to_messages(messages)

    # Add system prompt if not present
    has_system = any(isinstance(m, SystemMessage) for m in msg_list)
    if not has_system:
        msg_list = [SystemMessage(content=SYSTEM_PROMPT)] + list(msg_list)

    llm = create_llm_with_tools(model)

    # First invocation to check for tool calls
    response = llm.invoke(msg_list)
    tool_calls = getattr(response, 'tool_calls', [])

    if tool_calls:
        # Handle tool call
        tool_call = tool_calls[0]
        func_name = tool_call.get("name", "") if isinstance(tool_call, dict) else getattr(tool_call, 'name', '')

        if func_name == "search_realxmarket_docs":
            args = tool_call.get("args", {}) if isinstance(tool_call, dict) else getattr(tool_call, 'args', {})
            query = args.get("query", "") if isinstance(args, dict) else ""
            print(f"\n[TOOL CALL] search_realxmarket_docs with query: {query}\n")
            result = search_realxmarket_docs.invoke(query)
            print(f"[TOOL RESPONSE] {result}\n")

            # Add the AI message with tool_calls first (required by OpenAI API)
            msg_list.append(response)

            # Then add the tool message
            tool_call_id = tool_call.get('id', 'call_001') if isinstance(tool_call, dict) else getattr(tool_call, 'id', 'call_001')
            msg_list.append(ToolMessage(
                content=result,
                name="search_realxmarket_docs",
                tool_call_id=tool_call_id
            ))

            # Stream the final response
            simple_llm = ChatOpenAI(model="gpt-4o", temperature=0.1, api_key=os.environ.get("OPENAI_API_KEY"))
            for chunk in simple_llm.stream(msg_list):
                if hasattr(chunk, 'content') and chunk.content:
                    yield {"messages": [chunk]}
                # Print the full AI response
                if hasattr(chunk, 'content'):
                    print(chunk.content, end="")
                else:
                    print(chunk)
            yield {"done": True}
            return

    # No tool call - stream the response directly
    simple_llm = ChatOpenAI(model=model, temperature=0.1, api_key=os.environ.get("OPENAI_API_KEY"))
    for chunk in simple_llm.stream(msg_list):
        if hasattr(chunk, 'content') and chunk.content:
            yield {"messages": [chunk]}

    yield {"done": True}
