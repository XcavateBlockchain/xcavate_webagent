// js/api.js - API client for OpenAI-based LangGraph backend

export async function getChats() {
    const response = await fetch('/api/chats');
    return await response.json();
}

export async function getChat(id) {
    const response = await fetch(`/api/chats/${id}`);
    return await response.json();
}

export async function saveChat(chatData) {
    return fetch('/api/chats', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(chatData),
    });
}

export async function deleteChat(id) {
    return fetch(`/api/chats/${id}`, { method: 'DELETE' });
}

const SYSTEM_PROMPT = `You are a RealXmarket support assistant. Answer questions using only the official documentation.

When you don't know something, use the search_realxmarket_docs tool to find answers.

If documentation returns no results, say: "I couldn't find this in the RealXmarket documentation. Please contact RealXmarket support for assistance."

Be brief and professional.`;

export async function streamAgentResponse(history, model, onChunk, onDone, signal) {
    const currentHistory = [
        { role: 'system', content: SYSTEM_PROMPT },
        ...history
    ];

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages: currentHistory, model }),
            signal,
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.statusText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();

            if (done) {
                onDone();
                return;
            }

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.trim()) {
                    try {
                        const parsed = JSON.parse(line);

                        if (parsed.error) {
                            onChunk({ content: `Error: ${parsed.error}` });
                        } else if (parsed.message?.content) {
                            onChunk(parsed.message);
                        }

                        if (parsed.done) {
                            onDone();
                            return;
                        }
                    } catch (e) {
                        console.error('JSON parsing error:', e);
                    }
                }
            }
        }
    } catch (error) {
        if (error.name !== 'AbortError') {
            console.error('Stream error:', error);
            throw error;
        }
    }
}
