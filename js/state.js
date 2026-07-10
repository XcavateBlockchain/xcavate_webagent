// js/state.js
import { DEFAULT_MODEL } from './config.js';

let state = {
    activeChatId: null,
    currentChat: { id: null, title: '', history: [] },
    currentModel: DEFAULT_MODEL,
    modelContextWindows: {}, // New: map of models and their context windows
};


export function getActiveChatId() {
    return state.activeChatId;
}

export function getCurrentChat() {
    return state.currentChat;
}

export function updateCurrentChat(newChatData) {
    state.currentChat = { ...state.currentChat, ...newChatData };
}

export function pushToHistory(turn) {
    state.currentChat.history.push(turn);
}

export function setActiveChat(chatId, chatData) {
    state.activeChatId = chatId;
    state.currentChat = chatData;
}

export function resetState() {
    state.activeChatId = null;
    state.currentChat = { id: null, title: '', history: [] };
}


// MODEL MANAGEMENT FUNCTIONS
export function getCurrentModel() {
    return state.currentModel;
}

export function setCurrentModel(modelName) {
    state.currentModel = modelName;
}

// FUNCTIONS TO HANDLE MODEL CONTEXT WINDOWS
export function setModelContextWindows(models) {
    state.modelContextWindows = models.reduce((acc, model) => {
        acc[model.name] = model.context_window;
        return acc;
    }, {});
    console.log("Updated modelContextWindows:", JSON.stringify(state.modelContextWindows, null, 2));
}

export function getContextWindowForModel(modelName) {
    return state.modelContextWindows[modelName];
}

// WALLET AUTHENTICATION STATE
let walletState = {
    address: null,
    signature: null,
    account: null,
    isConnected: false
};

export function getWalletAddress() { return walletState.address; }
export function getWalletSignature() { return walletState.signature; }
export function getWalletAccount() { return walletState.account; }
export function getIsWalletConnected() { return walletState.isConnected; }

export function setWalletAuth(address, signature, account) {
    walletState = { address, signature, account, isConnected: true };
}

export function clearWalletAuth() {
    walletState = { address: null, signature: null, account: null, isConnected: false };
}

let attachments = []; // Attachment list

export function getAttachments() { return attachments; }
export function addAttachment(file) {
    if (!attachments.some(existingFile => existingFile.name === file.name)) {
        attachments.push(file);
    }
}
export function removeAttachment(fileName) {
    attachments = attachments.filter(file => file.name !== fileName);
}
export function clearAttachments() { attachments = []; }