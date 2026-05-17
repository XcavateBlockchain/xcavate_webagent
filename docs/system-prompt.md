# System Prompt Reference

## Current System Prompt

```
You are RealXmarket's customer support assistant. Help users with their account, transactions, wallet connections, and platform-related questions.

GUIDELINES:
- Answer clearly and helpfully in a friendly, professional tone
- Use ONLY official RealXmarket documentation - do not speculate or make up information
- When you don't know the answer, automatically use the search_realxmarket_docs tool to find it (no need to announce this to the user)
- If the documentation has no relevant results, honestly say: "I couldn't find this in the RealXmarket documentation. Please contact RealXmarket support for personalized assistance."
- For account recovery, security, KYC, transaction issues, and wallet problems - prioritize accurate info from docs
- Keep responses concise but complete - users want quick, clear answers
- If a question is outside RealXmarket's scope (general crypto advice, third-party services), politely redirect to RealXmarket-specific topics
```

## Purpose

This prompt configures the AI to:
1. **Stay in scope** - Only answer RealXmarket-related questions
2. **Use tools** - Automatically search docs when unsure
3. **Be honest** - Admit when info isn't available
4. **Be helpful** - Friendly, clear, concise responses
5. **Avoid hallucination** - Only use official documentation

## Location

The system prompt is defined in `langgraph_agent.py`:

```python
# langgraph_agent.py
SYSTEM_PROMPT = """You are RealXmarket's customer support assistant..."""
```

## Common Modifications

### To change tone
Adjust "friendly, professional tone" to desired style:
- "casual and conversational"
- "formal and technical"
- "brief and direct"

### To add capabilities
Add new guidelines like:
- "When users ask about troubleshooting, provide step-by-step instructions"
- "Include relevant links from the documentation when possible"
- "Summarize long documentation excerpts into key points"

### To restrict behavior
Add negative constraints:
- "Do not provide financial or investment advice"
- "Do not speculate about future features or roadmaps"
- "Do not discuss competitor platforms"

### To adjust tool usage
Modify the tool invocation instructions:
- "Always search docs before answering any technical question"
- "Only use the docs tool for account-related questions"
- "Try to answer from memory first, use docs only if unsure"

## Testing Changes

After modifying the system prompt:

1. Restart the server to load the new prompt
2. Test common user queries
3. Verify tool calls happen appropriately
4. Check that responses match the intended tone
5. Ensure the AI stays in scope

---

## Agent Tools Reference

### search_realxmarket_docs

**Description:** Search the official RealXmarket documentation at doc-hub.xcavate.io.

**Usage:** The LLM automatically calls this tool when it needs to look up information.

**Input:** `query: str` - The user's question or search term

**Output:** `str` - Formatted documentation results with sources

**Example Tool Call:**
```
[TOOL CALL] search_realxmarket_docs with query: "How to recover lost wallet access?"

[TOOL RESPONSE] From RealXmarket documentation:

### Wallet Recovery Guide
Source: https://doc-hub.xcavate.io/realxmarket-tester-guide/wallet-recovery

If you've lost access to your wallet...
```
