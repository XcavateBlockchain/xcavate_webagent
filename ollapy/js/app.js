// js/app.js
console.log("APP.JS LOADED");
import * as config from './config.js';
import * as api from './api.js';
import * as state from './state.js';
import * as ui from './ui.js';

let currentAbortController = null; // Used to cancel in-flight requests

const DEFAULT_QUICK_REPLIES = [
    'Help Me Fix It',
    'Create Support Ticket'
];

// --- BUSINESS LOGIC AND EVENT HANDLING ---

async function loadChat(chatId) {
    try {
        const chatData = await api.getChat(chatId);
        if (chatData && chatData.id) {
            state.setCurrentModel(config.DEFAULT_OLLAMA_MODEL);
            ui.updateChatTitle(state.getCurrentModel());
            
            state.setActiveChat(chatData.id, chatData);
            ui.clearChatLog();
            state.getCurrentChat().history.forEach(turn => ui.addMessageToLog(turn.role, turn.content, turn.responseTime));
            ui.setWelcomeState(state.getCurrentChat().history.length === 0);
            
            await refreshHistoryList();
            updateTotalTokenCount();

        } else {
            await startNewChat();
        }
    } catch (error) {
        console.error("Error while loading chat:", error);
        await startNewChat();
    }
}

async function startNewChat() {
    state.resetState();
    ui.clearChatLog();
    state.clearAttachments();
    ui.clearAttachmentsUI();
    ui.setWelcomeState(true);
    await refreshHistoryList();
    updateTotalTokenCount();
}

async function deleteChat(chatId) {
    if (!confirm("Are you sure you want to delete this chat?")) return;
    await api.deleteChat(chatId);
    if (state.getActiveChatId() === chatId) {
        await startNewChat();
    } else {
        await refreshHistoryList();
    }
}

async function handleFormSubmit(event) {
    event.preventDefault();

    let userPrompt = ui.dom.promptInput.value.trim();
    const attachments = state.getAttachments();

    if (!userPrompt && attachments.length === 0) return;
    ui.setWelcomeState(false);
    ui.clearInlineQuickReplies();

    // Append attachment content to the prompt
    if (attachments.length > 0) {
        const attachmentsContent = attachments
            .map(file => `--- ATTACHMENT: ${file.name} ---\n${file.content}`)
            .join('\n\n');
        userPrompt = userPrompt 
            ? `${userPrompt}\n\n${attachmentsContent}`
            : attachmentsContent;
    }

    const startTime = performance.now();
    ui.clearPromptInput();
    state.clearAttachments();
    ui.clearAttachmentsUI();
    ui.toggleLoading(true);


    if (!state.getActiveChatId()) {
        const newChatId = Date.now().toString();
        const newChat = {
            id: newChatId,
            title: userPrompt.length > 30 ? userPrompt.substring(0, 27) + '...' : userPrompt,
            history: [],
            model: state.getCurrentModel()
        };
        state.setActiveChat(newChatId, newChat);
        await api.saveChat(state.getCurrentChat());
        await refreshHistoryList();
    }

    ui.addMessageToLog('user', userPrompt);
    state.pushToHistory({ role: 'user', content: userPrompt });
    updateTotalTokenCount();

    const aiMessageElement = ui.addMessageToLog('assistant', '<span class="cursor"></span>');
    let fullResponse = '';

    // Initialize a new AbortController for each request
    currentAbortController = new AbortController();

    try {
        await api.streamOllamaResponse(
            state.getCurrentChat().history,
            state.getCurrentModel(),
            // onChunk
            (parsed) => {
                if (parsed.message && parsed.message.content) {
                    fullResponse += parsed.message.content;
                }
                const htmlContent = marked.parse(fullResponse);
                aiMessageElement.innerHTML = DOMPurify.sanitize(htmlContent) + '<span class="cursor"></span>';
                ui.scrollToBottom();

                if (parsed.done) {
                    state.pushToHistory({ role: 'assistant', content: fullResponse });
                    updateTotalTokenCount();
                }
            },
            // onDone
            async () => {
                aiMessageElement.querySelector('.cursor')?.remove();
                const duration = ((performance.now() - startTime) / 1000).toFixed(2);
                ui.addResponseTime(aiMessageElement, duration);

                const quickReplies = generateQuickReplies(userPrompt, fullResponse);
                ui.renderInlineQuickReplies(aiMessageElement, quickReplies, submitQuickAction);

                const lastTurn = state.getCurrentChat().history[state.getCurrentChat().history.length - 1];
                if (lastTurn.role === 'assistant') {
                    lastTurn.responseTime = duration;
                }
                await api.saveChat(state.getCurrentChat());
            },
            currentAbortController.signal // Pass the cancellation signal
        );
    } catch (error) {
        if (error.name === 'AbortError') {
            console.warn("Request cancelled by user.");
            aiMessageElement.textContent = 'Response cancelled.';
            aiMessageElement.style.color = 'var(--color-yellow)'; // Styling for cancelled state
        } else {
            console.error('Ollama request error:', error);
            aiMessageElement.style.color = '#ff8a80';
            aiMessageElement.textContent = `Error: ${error.message}. Make sure Ollama is running.`;
        }
    } finally {
        ui.toggleLoading(false);
        currentAbortController = null; // Reset controller
    }
}

function handleCancelClick() {
    if (currentAbortController) {
        currentAbortController.abort();
    }
}

async function submitQuickAction(promptText) {
    if (!promptText) return;
    ui.dom.promptInput.value = promptText;
    await handleFormSubmit({ preventDefault: () => {} });
}

function generateQuickReplies(lastUserPrompt, lastAssistantResponse) {
    const combined = `${lastUserPrompt} ${lastAssistantResponse}`.toLowerCase();
    if (combined.includes('payment') || combined.includes('transaction')) {
        return ['Check Transaction Status', 'Create Support Ticket'];
    }
    if (combined.includes('account') || combined.includes('login')) {
        return ['Reset My Account', 'Contact Support'];
    }
    if (combined.includes('feature') || combined.includes('app')) {
        return ['Show Me More Features', 'How Do I Use This?'];
    }
    return DEFAULT_QUICK_REPLIES;
}

// --- INTERNAL UTILITIES ---

function estimateTokens(text) { return Math.ceil(text.length / 4); }

function updateTotalTokenCount() {
    const currentPrompt = ui.dom.promptInput.value.trim();
    const attachments = state.getAttachments();
    
    let combinedText = state.getCurrentChat().history.map(turn => turn.content).join(' ');
    
    if (currentPrompt) {
        combinedText += ` ${currentPrompt}`;
    }

    if (attachments.length > 0) {
        const attachmentsContent = attachments
            .map(file => file.content)
            .join(' ');
        combinedText += ` ${attachmentsContent}`;
    }

    const tokenCount = estimateTokens(combinedText);
    const maxTokens = config.MAX_CONTEXT_WINDOW;
    console.log(`Token Count: ${tokenCount}, Max Tokens: ${maxTokens}, Current Model: ${state.getCurrentModel()}`);
    ui.updateTokenUI(tokenCount, maxTokens);
}

async function refreshHistoryList() {
    const chats = await api.getChats();
    ui.renderHistoryList(chats, state.getActiveChatId(), loadChat, deleteChat);
}

// --- INITIALIZATION ---

async function init() {
    // Set initial title
    ui.updateChatTitle(state.getCurrentModel());

    // Attach primary event listeners
    ui.dom.form.addEventListener('submit', handleFormSubmit);
    ui.dom.newChatBtn.addEventListener('click', startNewChat);
    ui.dom.cancelButton.addEventListener('click', handleCancelClick); // Cancel button listener
    ui.dom.attachButton.addEventListener('click', () => ui.dom.fileInput.click()); // Trigger click on hidden file input
    ui.dom.fileInput.addEventListener('change', handleFileInputChange); // Handle file selection
    ui.bindQuickStartActions(submitQuickAction);

    // Start first chat
    await startNewChat();
}

// Run initialization only when DOM is ready.
document.addEventListener('DOMContentLoaded', () => {
    init();

    const promptInput = document.getElementById('prompt-input');
    if (promptInput) {
        promptInput.addEventListener('input', function() {
            autoResizeTextarea(this);
            updateTotalTokenCount(); // Update token counter on input
        });
        // Initialize correct height
        autoResizeTextarea(promptInput);

        // Enter submits, Shift+Enter inserts a newline
        promptInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const form = document.getElementById('chat-form');
                if (form) form.requestSubmit();
            }
        });
    }

    const toggleBtn = document.getElementById('toggle-sidebar-btn');
    const sidebar = document.querySelector('.sidebar-controls');
    const appLayout = document.querySelector('.app-layout');

    if (toggleBtn && sidebar && appLayout) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            appLayout.classList.toggle('sidebar-collapsed');
        });
    }

    const chatContainer = document.querySelector('.chat-container');
    const dropZone = document.getElementById('drop-zone');

    let dragCounter = 0;

    chatContainer.addEventListener('dragenter', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dragCounter++;
        if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
            chatContainer.classList.add('drag-over');
        }
    });

    chatContainer.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dragCounter--;
        if (dragCounter === 0) {
            chatContainer.classList.remove('drag-over');
        }
    });

    chatContainer.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
    });

    chatContainer.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dragCounter = 0;
        chatContainer.classList.remove('drag-over');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            
            let filesProcessed = 0;
            for (const file of files) {
                if (file.type.startsWith('text/')) {
                    const reader = new FileReader();
                    reader.onload = (event) => {
                        const fileContent = event.target.result;
                        state.addAttachment({ name: file.name, content: fileContent });
                        ui.renderAttachments(state.getAttachments(), removeAttachment);
                        updateTotalTokenCount();
                        filesProcessed++;
                    };
                    reader.onerror = (error) => {
                        console.error("Error while reading file:", error);
                        alert("Unable to read file.");
                        filesProcessed++;
                        if (filesProcessed === files.length) {
                            ui.renderAttachments(state.getAttachments(), removeAttachment);
                            updateTotalTokenCount(); // Update token count even on error
                        }
                    };
                    reader.readAsText(file);
                } else {
                    alert(`Unsupported file: ${file.name}. You can attach text files only.`);
                    filesProcessed++;
                    if (filesProcessed === files.length) {
                        ui.renderAttachments(state.getAttachments(), removeAttachment);
                        updateTotalTokenCount(); // Update token count even if file is not supported
                    }
                }
            }
        }
    });
});

// Auto-expand textarea up to 10 lines
function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    const maxRows = 10;
    const lineHeight = parseInt(window.getComputedStyle(textarea).lineHeight) || 20;
    const maxHeight = lineHeight * maxRows;
    textarea.style.height = Math.min(textarea.scrollHeight, maxHeight) + 'px';
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden';
}



function removeAttachment(fileName) {
    state.removeAttachment(fileName);
    ui.renderAttachments(state.getAttachments(), removeAttachment);
    updateTotalTokenCount(); // Update token count after removing attachments
}

async function handleFileInputChange(event) {
    const files = event.target.files;
    if (files.length > 0) {
        let filesProcessed = 0;
        for (const file of files) {
            if (file.type.startsWith('text/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const fileContent = e.target.result;
                    state.addAttachment({ name: file.name, content: fileContent });
                    ui.renderAttachments(state.getAttachments(), removeAttachment);
                    updateTotalTokenCount();
                    filesProcessed++;
                };
                reader.onerror = (error) => {
                    console.error("Error while reading file:", error);
                    alert("Unable to read file.");
                    filesProcessed++;
                    if (filesProcessed === files.length) {
                        ui.renderAttachments(state.getAttachments(), removeAttachment);
                        updateTotalTokenCount();
                    }
                };
                reader.readAsText(file);
            } else {
                alert(`Unsupported file: ${file.name}. You can attach text files only.`);
                filesProcessed++;
                if (filesProcessed === files.length) {
                    ui.renderAttachments(state.getAttachments(), removeAttachment);
                    updateTotalTokenCount();
                }
            }
        }
    }
    // Clear the input so the same file can be selected again if needed
    event.target.value = '';
}