// js/api.js
import { OLLAMA_BASE_URL } from './config.js';

// API helpers for Flask backend
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

// Updated: function now accepts model as argument
export async function streamOllamaResponse(history, model, onChunk, onDone, signal) {
    const response = await fetch(`${OLLAMA_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: model, messages: history, stream: true }),
        signal: signal,
    });

    if (!response.ok) {
        throw new Error(`Ollama server error: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) {
            onDone();
            break;
        }
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        lines.forEach(line => {
            if (line.trim()) {
                try {
                    onChunk(JSON.parse(line));
                } catch (e) {
                    console.error('JSON parsing error:', e, 'on line:', line);
                }
            }
        });
    }
}