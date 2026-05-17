"""Unit tests for langgraph_agent.py"""
import pytest
import os
from unittest.mock import patch, MagicMock, Mock

# Set up environment before importing
os.environ["OPENAI_API_KEY"] = "test-api-key"

# Mock external dependencies at module level
import sys
from unittest.mock import MagicMock, Mock

# Create proper mock classes that work with isinstance
class MockSystemMessage:
    pass

class MockAIMessage:
    def __init__(self, content=""):
        self.content = content

class MockToolMessage:
    def __init__(self, content="", name="", tool_call_id=""):
        self.content = content
        self.name = name
        self.tool_call_id = tool_call_id

def mock_convert_to_messages(msgs):
    """Mock conversion that returns messages as-is or wrapped"""
    result = []
    for m in msgs:
        if isinstance(m, dict):
            if m.get("role") == "system":
                result.append(MockSystemMessage())
            elif m.get("role") == "user":
                result.append({"role": "user", "content": m.get("content", "")})
            elif m.get("role") == "assistant":
                result.append({"role": "assistant", "content": m.get("content", "")})
            else:
                result.append(m)
        else:
            result.append(m)
    return result


# Create mock modules before importing langgraph_agent
mock_langchain_core = MagicMock()
mock_langchain_core.tools.tool = lambda f: f

mock_langchain_core_messages = MagicMock()
mock_langchain_core_messages.ToolMessage = MockToolMessage
mock_langchain_core_messages.SystemMessage = MockSystemMessage
mock_langchain_core_messages.AIMessage = MockAIMessage
mock_langchain_core_messages.convert_to_messages = mock_convert_to_messages

mock_langchain_core.messages = mock_langchain_core_messages
mock_langchain_core.tools = MagicMock()
mock_langchain_core.tools.tool = lambda f: f

sys.modules['langchain_core'] = mock_langchain_core
sys.modules['langchain_core.messages'] = mock_langchain_core_messages
sys.modules['langchain_core.tools'] = mock_langchain_core.tools

mock_langchain_openai = MagicMock()
sys.modules['langchain_openai'] = mock_langchain_openai

mock_langgraph = MagicMock()
sys.modules['langgraph'] = mock_langgraph

mock_langgraph_graph = MagicMock()
mock_langgraph_graph.StateGraph = MagicMock()
mock_langgraph_graph.END = "END"
sys.modules['langgraph.graph'] = mock_langgraph_graph

mock_langgraph_message = MagicMock()
mock_langgraph_message.add_messages = lambda x, y: x + y
sys.modules['langgraph.graph.message'] = mock_langgraph_message


class TestSystemPrompt:
    """Tests for system prompt content"""

    def test_system_prompt_exists(self):
        from langgraph_agent import SYSTEM_PROMPT
        assert SYSTEM_PROMPT is not None
        assert len(SYSTEM_PROMPT) > 0

    def test_system_prompt_contains_guidelines(self):
        from langgraph_agent import SYSTEM_PROMPT
        assert "GUIDELINES:" in SYSTEM_PROMPT
        assert "RealXmarket" in SYSTEM_PROMPT


class TestAgentState:
    """Tests for AgentState TypedDict"""

    def test_agent_state_structure(self):
        from langgraph_agent import AgentState
        # Just verify the type exists
        assert AgentState is not None


class TestSearchRealxmarketDocsTool:
    """Tests for search_realxmarket_docs tool"""

    @patch('langgraph_agent.search_realxmarket_docs')
    def test_tool_invocation(self, mock_tool):
        from langgraph_agent import search_realxmarket_docs
        mock_tool.invoke.return_value = "Search results"

        result = search_realxmarket_docs.invoke("test query")
        assert result == "Search results"


class TestCreateLlmWithTools:
    """Tests for create_llm_with_tools function"""

    def test_requires_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
                from langgraph_agent import create_llm_with_tools
                with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                    create_llm_with_tools()

    @patch('langgraph_agent.ChatOpenAI')
    def test_creates_llm_with_model(self, mock_chat_openai):
        mock_llm_instance = MagicMock()
        mock_chat_openai.return_value = mock_llm_instance

        from langgraph_agent import create_llm_with_tools
        llm = create_llm_with_tools("gpt-4o")

        mock_chat_openai.assert_called_once()
        assert llm is not None

    @patch('langgraph_agent.ChatOpenAI')
    def test_binds_tools_to_llm(self, mock_chat_openai):
        mock_llm_instance = MagicMock()
        mock_bound_llm = MagicMock()
        mock_llm_instance.bind_tools.return_value = mock_bound_llm
        mock_chat_openai.return_value = mock_llm_instance

        from langgraph_agent import create_llm_with_tools
        llm = create_llm_with_tools()

        mock_llm_instance.bind_tools.assert_called_once()


class TestAiNode:
    """Tests for ai_node function"""

    def test_ai_node_processes_messages(self):
        with patch('langgraph_agent.convert_to_messages', side_effect=mock_convert_to_messages):
            from langgraph_agent import ai_node, SystemMessage

            state = {"messages": [{"role": "user", "content": "test"}]}
            mock_llm = MagicMock()
            mock_response = MagicMock()
            mock_response.tool_calls = []
            mock_llm.invoke.return_value = mock_response

            result = ai_node(state, mock_llm)

            assert "messages" in result
            assert "tool_output" in result

    def test_ai_node_detects_tool_calls(self):
        with patch('langgraph_agent.convert_to_messages', side_effect=mock_convert_to_messages):
            from langgraph_agent import ai_node, SystemMessage

            state = {"messages": [{"role": "user", "content": "test"}]}
            mock_llm = MagicMock()
            mock_response = MagicMock()
            mock_tool_call = MagicMock()
            mock_response.tool_calls = [mock_tool_call]
            mock_llm.invoke.return_value = mock_response

            result = ai_node(state, mock_llm)

            assert result.get("_has_tool_call") is True


class TestToolNode:
    """Tests for tool_node function"""

    def test_tool_node_no_tool_calls(self):
        from langgraph_agent import tool_node

        state = {"messages": [{"role": "assistant", "content": "Hello"}]}
        result = tool_node(state)

        assert result["tool_output"] == ""

    @patch('langgraph_agent.search_realxmarket_docs')
    def test_tool_node_executes_search_tool(self, mock_search_tool):
        from langgraph_agent import tool_node

        mock_tool_call = {
            "name": "search_realxmarket_docs",
            "args": {"query": "wallet connection"}
        }
        mock_message = MagicMock()
        mock_message.tool_calls = [mock_tool_call]

        state = {"messages": [mock_message]}
        mock_search_tool.invoke.return_value = "Wallet connection docs"

        result = tool_node(state)

        assert result["tool_output"] == "Wallet connection docs"
        mock_search_tool.invoke.assert_called_once_with("wallet connection")


class TestFinalAnswerNode:
    """Tests for final_answer_node function"""

    @patch('langgraph_agent.ChatOpenAI')
    def test_final_answer_without_tool_output(self, mock_chat_openai):
        from langgraph_agent import final_answer_node

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_llm.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_llm

        state = {"messages": [{"role": "user", "content": "test"}], "tool_output": ""}

        result = final_answer_node(state, mock_llm)

        assert "messages" in result

    @patch('langgraph_agent.ChatOpenAI')
    def test_final_answer_with_tool_output(self, mock_chat_openai):
        from langgraph_agent import final_answer_node, ToolMessage

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_llm.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_llm

        state = {
            "messages": [{"role": "user", "content": "test"}],
            "tool_output": "Search results"
        }

        result = final_answer_node(state, mock_llm)

        assert "messages" in result


class TestCreateAgentGraph:
    """Tests for create_agent_graph function"""

    @patch('langgraph_agent.create_llm_with_tools')
    @patch('langgraph_agent.StateGraph')
    def test_creates_workflow(self, mock_state_graph, mock_create_llm):
        from langgraph_agent import create_agent_graph

        mock_workflow = MagicMock()
        mock_compiled = MagicMock()
        mock_workflow.compile.return_value = mock_compiled
        mock_state_graph.return_value = mock_workflow

        graph = create_agent_graph()

        assert mock_workflow.compile.called
        assert graph is not None

    @patch('langgraph_agent.create_llm_with_tools')
    @patch('langgraph_agent.StateGraph')
    def test_adds_nodes(self, mock_state_graph, mock_create_llm):
        from langgraph_agent import create_agent_graph

        mock_workflow = MagicMock()
        mock_compiled = MagicMock()
        mock_workflow.compile.return_value = mock_compiled
        mock_state_graph.return_value = mock_workflow

        graph = create_agent_graph()

        assert mock_workflow.add_node.called
        assert mock_workflow.set_entry_point.called


class TestStreamAgentResponse:
    """Tests for stream_agent_response function"""

    @patch('langgraph_agent.convert_to_messages', side_effect=mock_convert_to_messages)
    @patch('langgraph_agent.create_llm_with_tools')
    @patch('langgraph_agent.ChatOpenAI')
    def test_streams_response_without_tool(self, mock_chat_openai, mock_create_llm, mock_convert):
        from langgraph_agent import stream_agent_response, SystemMessage

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_llm.invoke.return_value = mock_response
        mock_create_llm.return_value = mock_llm

        mock_simple_llm = MagicMock()
        mock_chunk = MagicMock()
        mock_chunk.content = "Hello"
        mock_simple_llm.stream.return_value = [mock_chunk, MagicMock(content=" world")]
        mock_chat_openai.return_value = mock_simple_llm

        messages = [{"role": "user", "content": "test"}]
        result = list(stream_agent_response(messages))

        assert len(result) > 0
        assert any(r.get("done") for r in result)

    @patch('langgraph_agent.convert_to_messages', side_effect=mock_convert_to_messages)
    @patch('langgraph_agent.create_llm_with_tools')
    @patch('langgraph_agent.ChatOpenAI')
    def test_handles_tool_call_in_stream(self, mock_chat_openai, mock_create_llm, mock_convert):
        from langgraph_agent import stream_agent_response

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_tool_call = {
            "name": "search_realxmarket_docs",
            "args": {"query": "test"},
            "id": "call_123"
        }
        mock_response.tool_calls = [mock_tool_call]
        mock_llm.invoke.return_value = mock_response
        mock_create_llm.return_value = mock_llm

        mock_search_tool = MagicMock()
        mock_search_tool.invoke.return_value = "Search results"

        with patch('langgraph_agent.search_realxmarket_docs', mock_search_tool):
            mock_simple_llm = MagicMock()
            mock_chunk = MagicMock()
            mock_chunk.content = "Answer"
            mock_simple_llm.stream.return_value = [mock_chunk]
            mock_chat_openai.return_value = mock_simple_llm

            messages = [{"role": "user", "content": "test"}]
            result = list(stream_agent_response(messages))

            assert mock_search_tool.invoke.called
            assert any(r.get("done") for r in result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
