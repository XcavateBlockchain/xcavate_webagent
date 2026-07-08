// js/polkadot-auth.js - Polkadot extension wallet authentication module

let connectedAccount = null;
let injectedExtension = null;

/**
 * Get the Polkadot injected extension
 * Returns the extension or null if not available
 */
async function getInjectedExtension() {
    if (injectedExtension) {
        return injectedExtension;
    }

    // Wait for extension to be injected (it may take a moment on page load)
    const maxWaitTime = 5000;
    const checkInterval = 100;
    const startTime = Date.now();

    while (!window.injectedWeb3 && Date.now() - startTime < maxWaitTime) {
        await new Promise(resolve => setTimeout(resolve, checkInterval));
    }

    if (window.injectedWeb3 && window.injectedWeb3['polkadot-js'] && window.injectedWeb3['polkadot-js'].enable) {
        injectedExtension = await window.injectedWeb3['polkadot-js'].enable('xCavate WebAgent');
        return injectedExtension;
    }

    return null;
}

/**
 * Check if Polkadot.js extension is installed
 */
export async function isPolkadotExtensionInstalled() {
    try {
        const ext = await getInjectedExtension();
        return ext !== null;
    } catch (error) {
        console.error('Polkadot extension check failed:', error);
        return false;
    }
}

/**
 * Get list of available accounts from Polkadot extension
 * Returns array of account objects with { address, name }
 */
export async function getAvailableAccounts() {
    try {
        const ext = await getInjectedExtension();
        if (!ext) {
            throw new Error('Polkadot extension not found');
        }

        // Subscribe to accounts
        return new Promise((resolve, reject) => {
            window.web3AccountsSubscribe((accounts) => {
                if (accounts) {
                    resolve(accounts.map(acc => ({
                        address: acc.address,
                        name: acc.meta?.name || acc.address.slice(0, 8) + '...'
                    })));
                } else {
                    resolve([]);
                }
            }, (error) => {
                console.error('Account subscription error:', error);
                resolve([]);
            });
        });
    } catch (error) {
        console.error('Failed to get accounts:', error);
        throw error;
    }
}

/**
 * Connect wallet and request signature for authentication
 * @param {string} accountAddress - The Polkadot address to connect
 * @returns {Promise<{address: string, signature: string, account: object}>}
 */
export async function connectWallet(accountAddress) {
    try {
        const ext = await getInjectedExtension();
        if (!ext) {
            throw new Error('Polkadot extension not installed');
        }

        // Create a challenge message to sign
        const challengeMessage = `Authenticate with xCavate WebAgent\nTimestamp: ${Date.now()}\nAddress: ${accountAddress}`;

        // Sign the message using the extension
        const { signature } = await ext.signRaw({
            address: accountAddress,
            data: challengeMessage,
            type: 'bytes'
        });

        connectedAccount = {
            address: accountAddress,
            signature: signature,
            message: challengeMessage
        };

        return connectedAccount;
    } catch (error) {
        console.error('Wallet connection failed:', error);
        if (error.message && error.message.toLowerCase().includes('cancelled')) {
            throw new Error('Connection cancelled by user');
        }
        throw error;
    }
}

/**
 * Disconnect wallet and clear auth state
 */
export function disconnectWallet() {
    connectedAccount = null;
    return true;
}

/**
 * Sign an arbitrary message with the connected account
 * @param {string} message - Message to sign
 * @returns {Promise<string>} Signature hex string
 */
export async function signMessage(message) {
    try {
        if (!connectedAccount) {
            throw new Error('No wallet connected');
        }

        const ext = await getInjectedExtension();
        if (!ext) {
            throw new Error('Polkadot extension not available');
        }

        const { signature } = await ext.signRaw({
            address: connectedAccount.address,
            data: message,
            type: 'bytes'
        });

        return signature;
    } catch (error) {
        console.error('Message signing failed:', error);
        throw error;
    }
}

/**
 * Get currently connected account info
 * @returns {object|null} Account object or null if not connected
 */
export function getConnectedAccount() {
    return connectedAccount;
}

/**
 * Check if wallet is currently connected
 * @returns {boolean}
 */
export function isConnected() {
    return connectedAccount !== null;
}

/**
 * Format Polkadot address for display (shortened)
 * @param {string} address - Full Polkadot address
 * @returns {string} Shortened address like '5Grw...34ef'
 */
export function formatAddress(address) {
    if (!address) return '';
    if (address.length < 12) return address;
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

/**
 * Get install URL for Polkadot.js extension
 */
export function getExtensionInstallUrl() {
    return 'https://polkadot.js.org/extension/';
}
