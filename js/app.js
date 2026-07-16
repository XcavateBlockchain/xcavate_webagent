// js/app.js
import * as api from './api.js';
import * as state from './state.js';
import * as ui from './ui.js';
import * as polkadotAuth from './polkadot-auth.js';
import { initTicketForm, showTicketView } from './ticket-form.js';
import { setWalletInfo } from './api.js';

let currentAbortController = null;
let currentAiMessageElement = null;
let runtimeConfig = {
    default_model: null,
    max_context_window: null,
};

const DEFAULT_QUICK_REPLIES = ['Help Me Fix It', 'Create Support Ticket'];

// --- WALLET AUTHENTICATION ---
// Wallet only connects when user clicks "Create Ticket" button

async function initializeWalletStatus() {
    // Check for previously connected wallet (restore without prompting)
    const storedAddress = localStorage.getItem('walletAddress');
    if (storedAddress) {
        api.setWalletInfo(storedAddress, true);
        state.setWalletAuth(storedAddress, null, { address: storedAddress, isConnected: true });
        console.log('[Wallet] Restored:', storedAddress.slice(0, 8) + '...');
    }

    // Initialize ticket form after wallet status is restored
    await initTicketForm();
}


// --- BUSINESS LOGIC AND EVENT HANDLING ---

async function loadChat(chatId) {
    try {
        const chatData = await api.getChat(chatId);
        if (chatData && chatData.id) {
            state.setCurrentModel(runtimeConfig.default_model);
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

async function handleFormSubmit(event, quickActionPrompt = null) {
    event.preventDefault();

    let userPrompt = quickActionPrompt || ui.dom.promptInput.value.trim();
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
    if (!quickActionPrompt) ui.clearPromptInput();
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

    currentAiMessageElement = ui.addMessageToLog('assistant', '<span class="cursor"></span>');
    let fullResponse = '';

    // Initialize a new AbortController for each request
    currentAbortController = new AbortController();

    try {
        await api.streamAgentResponse(
            state.getCurrentChat().history,
            state.getCurrentModel(),
            // onChunk
            (message) => {
                if (message.content) {
                    fullResponse += message.content;
                }
                let htmlContent = marked.parse(fullResponse.trim());
                htmlContent = htmlContent.replace(/\s*\n\s*/g, ' ').replace(/>\s+</g, '><').trim();
                currentAiMessageElement.innerHTML = DOMPurify.sanitize(htmlContent) + '<span class="cursor"></span>';
                ui.scrollToBottom();
            },
            // onDone
            async () => {
                currentAiMessageElement.querySelector('.cursor')?.remove();
                const duration = ((performance.now() - startTime) / 1000).toFixed(2);
                ui.addResponseTime(currentAiMessageElement, duration);

                state.pushToHistory({ role: 'assistant', content: fullResponse.trim() });
                updateTotalTokenCount();

                const quickReplies = generateQuickReplies(userPrompt, fullResponse);
                ui.renderInlineQuickReplies(currentAiMessageElement, quickReplies, submitQuickAction);

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
            const elementToRemove = currentAiMessageElement;
            currentAiMessageElement = null;
            if (elementToRemove && elementToRemove.parentNode) {
                elementToRemove.parentNode.removeChild(elementToRemove);
            }
        } else {
            console.error('OpenAI request error:', error);

            // Check for rate limit error (429)
            const isRateLimitError = error.message?.includes('429') ||
                                     error.message?.includes('rate_limit') ||
                                     error.message?.includes('tokens per min') ||
                                     error.message?.includes('Request too large');

            if (isRateLimitError && currentAiMessageElement) {
                currentAiMessageElement.style.color = '#ff8a80';
                currentAiMessageElement.innerHTML = `
                    <strong>Rate limit exceeded.</strong><br><br>
                    Your OpenAI API request was too large for the current rate limit. Here are some options:<br><br>
                    • <strong>Wait a moment</strong> and try again (limits reset periodically)<br>
                    • <strong>Shorten your conversation</strong> - start a new chat to reduce token count<br>
                    • <strong>Check your OpenAI account</strong> at https://platform.openai.com/account/rate-limits<br><br>
                    <em>Note: Free tier accounts have lower rate limits than paid accounts.</em>
                `;
            } else if (currentAiMessageElement) {
                currentAiMessageElement.style.color = '#ff8a80';
                currentAiMessageElement.textContent = `Error: ${error.message}. Make sure OPENAI_API_KEY is set.`;
            }
        }
    } finally {
        ui.toggleLoading(false);
        currentAbortController = null;
        currentAiMessageElement = null;
    }
}

function handleCancelClick() {
    if (currentAbortController) {
        currentAbortController.abort();
    }
}

async function submitQuickAction(promptText) {
    if (!promptText) return;
    ui.showChat();
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

async function initializeMCPStatus() {
    try {
        const response = await fetch('/api/mcp-status');
        if (response.ok) {
            const data = await response.json();
            ui.updateMCPStatus(data.available || false);
        } else {
            ui.updateMCPStatus(false);
        }
    } catch (error) {
        console.warn('Failed to get MCP status:', error);
        ui.updateMCPStatus(false);
    }
}

function estimateTokens(text) { return Math.ceil(text.length / 4); }

function updateTotalTokenCount() {
    if (runtimeConfig.max_context_window == null) return;

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
    const maxTokens = runtimeConfig.max_context_window;
    ui.updateTokenUI(tokenCount, maxTokens);
}

async function refreshHistoryList() {
    const chats = await api.getChats();
    ui.renderHistoryList(chats, state.getActiveChatId(), loadChat, deleteChat);
}

// --- NAVIGATION ---

function navigateToChat() {
    ui.showChat();
    startNewChat();
}

function navigateToLanding() {
    ui.showLanding();
}

function navigateToTicket() {
    showTicketView();
}

// --- LANDING PAGE EVENT BINDING ---

function bindLandingPageEvents() {
    // "Message" button → opens chat
    const openChatBtn = document.getElementById('open-chat-btn');
    if (openChatBtn) {
        openChatBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            navigateToChat();
        });
    }

    // Self-service cards → open chat with prompt
    document.querySelectorAll('.service-card').forEach(card => {
        card.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const prompt = card.dataset.prompt;
            if (prompt) {
                navigateToChat();
                submitQuickAction(prompt);
            }
        });
    });

    // Category items → open chat with prompt
    document.querySelectorAll('.category-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const prompt = item.dataset.prompt;
            if (prompt) {
                navigateToChat();
                submitQuickAction(prompt);
            }
        });
    });

    // FAQ items → open chat with prompt
    document.querySelectorAll('.faq-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const prompt = item.dataset.prompt;
            if (prompt) {
                navigateToChat();
                submitQuickAction(prompt);
            }
        });
    });

    // Search bar — submit on Enter
    const searchInput = document.getElementById('landing-search');
    if (searchInput) {
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const query = searchInput.value.trim();
                if (query) {
                    navigateToChat();
                    submitQuickAction(query);
                    searchInput.value = '';
                }
            }
        });
    }
}

// --- INITIALIZATION ---

async function init() {
    // Show landing page first
    ui.showLanding();

    try {
        runtimeConfig = await api.getRuntimeConfig();
    } catch (error) {
        console.warn('Failed to load runtime config:', error);
    }

    state.setCurrentModel(runtimeConfig.default_model);

    // Set initial title
    ui.updateChatTitle(state.getCurrentModel());

    // Initialize wallet status (no auto-connect)
    await initializeWalletStatus();

    // Initialize MCP connection and status display
    await initializeMCPStatus();

    // Attach primary event listeners
    ui.dom.form.addEventListener('submit', handleFormSubmit);
    ui.dom.newChatBtn.addEventListener('click', startNewChat);
    ui.dom.cancelButton.addEventListener('click', handleCancelClick); // Cancel button listener
    ui.bindQuickStartActions(submitQuickAction);

    // Back button: go to landing page
    const toggleBtn = document.getElementById('toggle-sidebar-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', navigateToLanding);
    }

    // Bind landing page events
    bindLandingPageEvents();

    // Bind ticket navigation (floating button)
    const floatingTicketBtn = document.getElementById('floating-ticket-btn');
    if (floatingTicketBtn) {
        floatingTicketBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            navigateToTicket();
        });
    }

    // Start first chat (preloads state)
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

    const chatContainer = document.querySelector('.chat-container');
    const dropZone = document.getElementById('drop-zone');

    let dragCounter = 0;

    if (chatContainer) {
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
        });
    }
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