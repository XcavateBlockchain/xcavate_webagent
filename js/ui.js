// js/ui.js

// Export DOM elements for easy access
export const dom = {
    form: document.getElementById('chat-form'),
    promptInput: document.getElementById('prompt-input'),
    sendButton: document.getElementById('send-button'),
    cancelButton: document.getElementById('cancel-button'),
    chatLog: document.getElementById('chat-log'),
    newChatBtn: document.getElementById('new-chat-btn'),
    chatHistoryList: document.getElementById('chat-history-list'),
    historySidebar: document.getElementById('history-sidebar'),
    tokenCountText: document.getElementById('token-count-text'),
    tokenProgressBarInner: document.getElementById('token-progress-bar-inner'),
    modelNameSpan: document.getElementById('model-name-span'),
    welcomeState: document.getElementById('welcome-state'),
    quickStartGrid: document.getElementById('quick-start-grid'),
    toggleSidebarBtn: document.getElementById('toggle-sidebar-btn'),
    sidebarControls: document.querySelector('.sidebar-controls'),
    attachmentContainer: document.getElementById('attachment-container'),
    fileInput: document.getElementById('file-input'),
    attachButton: document.getElementById('attach-button'),
    landingPage: document.getElementById('landing-page'),
    chatView: document.getElementById('chat-view'),
    openChatBtn: document.getElementById('open-chat-btn'),
    mcpStatusIndicator: document.getElementById('mcp-status-indicator'),
};

// --- PAGE NAVIGATION ---
export function showLanding() {
    if (dom.landingPage) dom.landingPage.style.display = 'flex';
    if (dom.chatView) dom.chatView.style.display = 'none';
}

export function showChat() {
    if (dom.landingPage) dom.landingPage.style.display = 'none';
    if (dom.chatView) dom.chatView.style.display = 'flex';
}

// Update chat title with model name
export function updateChatTitle(modelName) {
    dom.modelNameSpan.textContent = 'RealXmarket Help';
}

export function setWelcomeState(isVisible) {
    if (!dom.welcomeState) return;
    dom.welcomeState.style.display = isVisible ? 'flex' : 'none';
}

export function bindQuickStartActions(onSelect) {
    if (!dom.quickStartGrid) return;
    dom.quickStartGrid.querySelectorAll('.quick-action-btn').forEach((button) => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            onSelect(button.dataset.prompt || button.textContent || '');
        });
    });
}

export function renderHistoryList(chats, activeChatId, loadChatCallback, deleteChatCallback) {
    dom.chatHistoryList.innerHTML = '';
    chats.forEach(chat => {
        const li = document.createElement('li');
        li.dataset.chatId = chat.id;

        // Container for title and tag
        const infoDiv = document.createElement('div');
        infoDiv.className = 'chat-info';

        const titleSpan = document.createElement('span');
        titleSpan.className = 'chat-title';
        titleSpan.textContent = chat.title;
        infoDiv.appendChild(titleSpan);

        if (chat.model) {
            const modelTag = document.createElement('small');
            modelTag.className = 'model-tag';
            modelTag.textContent = chat.model.split(':')[0]; // Show base model name only
            infoDiv.appendChild(modelTag);
        }
        li.appendChild(infoDiv);

        if (chat.id === activeChatId) li.classList.add('active');
        
        const deleteBtn = document.createElement('span');
        deleteBtn.className = 'delete-btn';
        deleteBtn.innerHTML = '×';
        deleteBtn.onclick = (e) => { e.stopPropagation(); deleteChatCallback(chat.id); };
        li.appendChild(deleteBtn);
        
        li.onclick = () => loadChatCallback(chat.id);
        dom.chatHistoryList.appendChild(li);
    });
}

// Configure marked with custom options
marked.setOptions({
    breaks: false,
    gfm: true
});

export function addMessageToLog(role, content, responseTime) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', role === 'user' ? 'user-message' : 'ai-message');

    if (role === 'assistant') {
        let htmlContent = marked.parse(content).trim();
        // Remove extra whitespace between tags
        htmlContent = htmlContent.replace(/\s*\n\s*/g, ' ').replace(/>\s+</g, '><').trim();
        messageElement.innerHTML = DOMPurify.sanitize(htmlContent);
    } else {
        messageElement.textContent = content;
    }
    if (role === 'assistant' && responseTime) {
        addResponseTime(messageElement, responseTime);
    }
    dom.chatLog.appendChild(messageElement);
    scrollToBottom();
    return messageElement;
}

export function clearInlineQuickReplies() {
    dom.chatLog.querySelectorAll('.inline-quick-replies').forEach((node) => node.remove());
}

export function renderInlineQuickReplies(anchorMessageElement, replies, onSelect) {
    if (!anchorMessageElement || !Array.isArray(replies) || replies.length === 0) return;
    clearInlineQuickReplies();

    const wrapper = document.createElement('div');
    wrapper.className = 'inline-quick-replies';

    replies.forEach((replyText) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'quick-action-btn quick-reply-btn';
        button.textContent = replyText;
        button.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            onSelect(replyText);
        });
        wrapper.appendChild(button);
    });

    anchorMessageElement.insertAdjacentElement('afterend', wrapper);
    scrollToBottom();
}

export function addResponseTime(element, duration) {
    const timeElement = document.createElement('div');
    timeElement.className = 'response-time-info';
    timeElement.textContent = `Response generated in ${duration}s`;
    element.appendChild(timeElement);
}

export function updateTokenUI(tokenCount, maxTokens) {
    const percentage = Math.min(100, (tokenCount / maxTokens) * 100);
    dom.tokenCountText.textContent = `${tokenCount.toLocaleString('it-IT')} / ${maxTokens.toLocaleString('it-IT')} tokens`;
    dom.tokenProgressBarInner.style.width = `${percentage}%`;
    if (percentage < 50) dom.tokenProgressBarInner.style.backgroundColor = 'var(--color-green)';
    else if (percentage < 75) dom.tokenProgressBarInner.style.backgroundColor = 'var(--color-yellow)';
    else if (percentage < 90) dom.tokenProgressBarInner.style.backgroundColor = 'var(--color-orange)';
    else dom.tokenProgressBarInner.style.backgroundColor = 'var(--color-red)';
}

export function toggleLoading(isLoading) {
    dom.sendButton.disabled = isLoading;
    dom.cancelButton.style.display = isLoading ? 'inline-block' : 'none';
    dom.sendButton.style.display = isLoading ? 'none' : 'inline-block';
    dom.historySidebar.classList.toggle('sidebar-disabled', isLoading);
    if (!isLoading) {
        dom.promptInput.focus();
    }
}

export function clearChatLog() {
    dom.chatLog.innerHTML = '';
    clearInlineQuickReplies();
}

export function clearPromptInput() {
    dom.promptInput.value = '';
    // Also reset textarea height
    dom.promptInput.style.height = 'auto';
    dom.promptInput.style.overflowY = 'hidden';
}

export function scrollToBottom() {
    dom.chatLog.scrollTop = dom.chatLog.scrollHeight;
}

export function toggleSidebar() {
    dom.sidebarControls.classList.toggle('collapsed');
}

// --- ATTACHMENT HELPERS ---

export function renderAttachments(attachments, onRemove) {
    const container = dom.attachmentContainer;
    if (!container) return;

    container.innerHTML = ''; // Clear old attachments

    attachments.forEach(file => {
        const item = document.createElement('div');
        item.className = 'attachment-item';
        item.dataset.fileName = file.name;

        // Generic file icon
        const icon = document.createElement('span');
        icon.className = 'file-icon';
        icon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zM6 20V4h7v5h5v11H6z"/></svg>`;

        // File name
        const name = document.createElement('span');
        name.className = 'file-name';
        name.textContent = file.name;
        name.title = file.name;

        // Remove button
        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-attachment-btn';
        removeBtn.innerHTML = '&times;'; // "x" character
        removeBtn.onclick = () => onRemove(file.name);

        item.appendChild(icon);
        item.appendChild(name);
        item.appendChild(removeBtn);

        container.appendChild(item);
    });

    // Show or hide container
    container.style.display = attachments.length > 0 ? 'flex' : 'none';
}

export function clearAttachmentsUI() {
    const container = dom.attachmentContainer;
    if (container) {
        container.innerHTML = '';
        container.style.display = 'none';
    }
}

// Docs Status UI helpers
export function updateMCPStatus(docsConnected) {
    const indicator = document.getElementById('mcp-web-status');
    if (!indicator) return;

    if (docsConnected) {
        indicator.classList.add('mcp-connected');
        indicator.classList.remove('mcp-disconnected');
        indicator.title = 'RealXmarket docs connected';
    } else {
        indicator.classList.add('mcp-disconnected');
        indicator.classList.remove('mcp-connected');
        indicator.title = 'Docs not available';
    }
}

// --- WALLET AUTHENTICATION UI HELPERS ---

let onWalletConnectClick = null;
let onWalletDisconnectClick = null;

export function setWalletClickHandlers(onConnect, onDisconnect) {
    onWalletConnectClick = onConnect;
    onWalletDisconnectClick = onDisconnect;
}

export function renderWalletAuthUI(isConnected, address, formatAddressFn) {
    const walletContainer = document.getElementById('wallet-auth-container');
    if (!walletContainer) return;

    if (isConnected && address) {
        walletContainer.innerHTML = `
            <div class="wallet-auth-connected">
                <span class="wallet-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 12V8H6a2 2 0 0 1-2-2c0-1.1.9-2 2-2h12v4"/><path d="M4 6v12c0 1.1.9 2 2 2h14v-4"/><path d="M18 12a2 2 0 0 0-2 2c0 1.1.9 2 2 2h4v-4h-4z"/></svg>
                </span>
                <span class="wallet-address">${formatAddressFn(address)}</span>
                <button type="button" class="wallet-disconnect-btn">Disconnect</button>
            </div>
        `;
        const disconnectBtn = walletContainer.querySelector('.wallet-disconnect-btn');
        if (disconnectBtn && onWalletDisconnectClick) {
            disconnectBtn.addEventListener('click', onWalletDisconnectClick);
        }
    } else {
        walletContainer.innerHTML = `
            <div class="wallet-auth-disconnected">
                <button type="button" class="wallet-connect-btn">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"/><path d="M3 5v14a2 2 0 0 0 2 2h16v-5"/><path d="M18 12a2 2 0 0 0 0 4h4v-4Z"/></svg>
                    Connect Wallet
                </button>
            </div>
        `;
        const connectBtn = walletContainer.querySelector('.wallet-connect-btn');
        if (connectBtn && onWalletConnectClick) {
            connectBtn.addEventListener('click', onWalletConnectClick);
        }
    }
}

export function showWalletError(message) {
    alert(message);
}

export function updateWalletButtonState(button, isLoading) {
    if (!button) return;
    button.disabled = isLoading;
    button.textContent = isLoading ? 'Connecting...' : 'Connect Polkadot Wallet';
}