// js/api.js - API client for OpenAI-based LangGraph backend

let walletAddress = null;
let hasWallet = false;

export function setWalletInfo(address, connected) {
    walletAddress = address;
    hasWallet = connected;
}

export function getWalletInfo() {
    return { walletAddress, hasWallet };
}

export async function getRuntimeConfig() {
    const response = await fetch('/api/config');
    return await response.json();
}

export async function getChats() {
    const response = await fetch('/api/chats');
    return await response.json();
}

export async function getChat(id) {
    const response = await fetch(`/api/chats/${id}`);
    return await response.json();
}

export async function saveChat(chatData) {
    const payload = {
        ...chatData,
        walletAddress: walletAddress,
        hasWallet: hasWallet
    };
    return fetch('/api/chats', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
}

export async function deleteChat(id) {
    return fetch(`/api/chats/${id}`, { method: 'DELETE' });
}

const SYSTEM_PROMPT = `You are RealXmarket's customer support assistant. Help users with their account, transactions, wallet connections, and platform-related questions.

GUIDELINES:
- Answer clearly and helpfully in a friendly, professional tone
- Use ONLY official RealXmarket documentation - do not speculate or make up information
- When you don't know the answer, automatically use the search_realxmarket_docs tool to find it (no need to announce this to the user)
- If the documentation has no relevant results, honestly say: "I couldn't find this in the RealXmarket documentation. Please contact RealXmarket support for personalized assistance."
- For account recovery, security, KYC, transaction issues, and wallet problems - prioritize accurate info from docs
- Keep responses concise but complete - users want quick, clear answers
- If a question is outside RealXmarket's scope (general crypto advice, third-party services), politely redirect to RealXmarket-specific topics`;

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
        if (error.name === 'AbortError') {
            // Re-throw AbortError so the caller knows the request was cancelled
            throw error;
        } else {
            console.error('Stream error:', error);
            throw error;
        }
    }
}
