// js/ticket-form.js - Ticket form handling

import * as polkadotAuth from './polkadot-auth.js';

let currentTicketNumber = null;

// DOM references
const dom = {
    ticketView: document.getElementById('ticket-view'),
    ticketForm: document.getElementById('ticket-form'),
    ticketBackBtn: document.getElementById('ticket-back-btn'),
    ticketTitle: document.getElementById('ticket-title'),
    ticketCategory: document.getElementById('ticket-category'),
    ticketPriority: document.getElementById('ticket-priority'),
    ticketDescription: document.getElementById('ticket-description'),
    ticketWalletIndicator: document.getElementById('ticket-wallet-indicator'),
    ticketWalletAddress: document.getElementById('ticket-wallet-address'),
    ticketSubmitBtn: document.getElementById('ticket-submit-btn'),
    ticketSuccess: document.getElementById('ticket-success'),
    submittedTicketNumber: document.getElementById('submitted-ticket-number'),
    ticketNewTicketBtn: document.getElementById('ticket-new-ticket-btn'),
    ticketHomeBtn: document.getElementById('ticket-home-btn')
};

// Generate unique ticket number
function generateTicketNumber() {
    const timestamp = Date.now().toString(36).toUpperCase();
    const random = Math.random().toString(36).substring(2, 6).toUpperCase();
    return `TICKET-${timestamp}-${random}`;
}

// Check wallet connection
async function checkWalletConnection() {
    const storedAddress = localStorage.getItem('walletAddress');
    if (!storedAddress) {
        return null;
    }
    return storedAddress;
}

// Display wallet address in form
function displayWalletAddress(address) {
    if (dom.ticketWalletAddress) {
        dom.ticketWalletAddress.textContent = address.slice(0, 8) + '...' + address.slice(-6);
    }
    if (dom.ticketWalletIndicator) {
        dom.ticketWalletIndicator.style.display = 'block';
    }
}

// Show error message
function showError(message) {
    alert(message);
}

// Submit ticket via API
async function submitTicket(ticketData) {
    try {
        const response = await fetch('/api/tickets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(ticketData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to submit ticket');
        }

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Ticket submission error:', error);
        throw error;
    }
}

// Show success state
function showSuccess(ticketNumber) {
    currentTicketNumber = ticketNumber;
    if (dom.submittedTicketNumber) {
        dom.submittedTicketNumber.textContent = ticketNumber;
    }
    if (dom.ticketForm) {
        dom.ticketForm.style.display = 'none';
    }
    if (dom.ticketSuccess) {
        dom.ticketSuccess.style.display = 'flex';
    }
}

// Reset form
function resetForm() {
    if (dom.ticketForm) {
        dom.ticketForm.reset();
        dom.ticketForm.style.display = 'block';
    }
    if (dom.ticketSuccess) {
        dom.ticketSuccess.style.display = 'none';
    }
    // Restore submit button state
    if (dom.ticketSubmitBtn) {
        dom.ticketSubmitBtn.disabled = false;
        dom.ticketSubmitBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg><span>Submit Ticket</span>`;
    }
    currentTicketNumber = null;
}

// Navigate to home (landing page)
function navigateToHome() {
    const landingPage = document.getElementById('landing-page');
    const chatView = document.getElementById('chat-view');

    if (landingPage) landingPage.style.display = 'flex';
    if (chatView) chatView.style.display = 'none';
    if (dom.ticketView) dom.ticketView.style.display = 'none';
}

// Initialize ticket form
export async function initTicketForm() {
    // Check wallet connection on load
    const walletAddress = await checkWalletConnection();

    if (!walletAddress) {
        showError('Please connect your wallet before submitting a ticket.');
        // Navigate back to landing page
        navigateToHome();
        return false;
    }

    displayWalletAddress(walletAddress);

    // Bind events
    if (dom.ticketBackBtn) {
        dom.ticketBackBtn.addEventListener('click', navigateToHome);
    }

    if (dom.ticketNewTicketBtn) {
        dom.ticketNewTicketBtn.addEventListener('click', () => {
            resetForm();
        });
    }

    if (dom.ticketHomeBtn) {
        dom.ticketHomeBtn.addEventListener('click', navigateToHome);
    }

    if (dom.ticketForm) {
        dom.ticketForm.addEventListener('submit', async (event) => {
            event.preventDefault();

            // Validate wallet still connected
            const walletAddress = await checkWalletConnection();
            if (!walletAddress) {
                showError('Your wallet disconnected. Please reconnect and try again.');
                navigateToHome();
                return;
            }

            // Gather form data
            const title = dom.ticketTitle.value.trim();
            const category = dom.ticketCategory.value;
            const priority = dom.ticketPriority.value;
            const description = dom.ticketDescription.value.trim();

            // Basic validation
            if (!title || !category || !priority || !description) {
                showError('Please fill in all required fields.');
                return;
            }

            // Disable submit button
            if (dom.ticketSubmitBtn) {
                dom.ticketSubmitBtn.disabled = true;
                dom.ticketSubmitBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg><span>Submitting...</span>`;
            }

            try {
                const ticketNumber = generateTicketNumber();

                const ticketData = {
                    ticket_id: ticketNumber,
                    wallet_address: walletAddress,
                    title: title,
                    category: category,
                    priority: priority,
                    description: description,
                    status: 'open'
                };

                await submitTicket(ticketData);
                showSuccess(ticketNumber);

            } catch (error) {
                showError('Failed to submit ticket: ' + error.message);
                if (dom.ticketSubmitBtn) {
                    dom.ticketSubmitBtn.disabled = false;
                    dom.ticketSubmitBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg><span>Submit Ticket</span>`;
                }
            }
        });
    }

    return true;
}

// Show ticket view
export function showTicketView() {
    const landingPage = document.getElementById('landing-page');
    const chatView = document.getElementById('chat-view');

    if (landingPage) landingPage.style.display = 'none';
    if (chatView) chatView.style.display = 'none';
    if (dom.ticketView) dom.ticketView.style.display = 'flex';

    // Reset form when showing view
    resetForm();
}

// Export DOM for external access
export { dom };
