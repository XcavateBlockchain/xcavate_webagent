// js/polkadot-auth.js - Polkadot extension wallet authentication module
// Uses the injected extension API directly (window.injectedWeb3)

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
        return false;
    }
}

/**
 * Get list of available accounts from Polkadot extension
 * Returns array of account objects with { address, name }
 */
export async function getAvailableAccounts() {
    const ext = await getInjectedExtension();
    if (!ext) {
        throw new Error('Polkadot extension not found');
    }

    return new Promise((resolve) => {
        ext.accounts.subscribe((accounts) => {
            if (accounts) {
                resolve(accounts.map(acc => ({
                    address: acc.address,
                    name: acc.meta?.name || acc.address.slice(0, 8) + '...'
                })));
            } else {
                resolve([]);
            }
        });
    });
}

/**
 * Connect wallet and request signature for authentication
 */
export async function connectWallet(accountAddress) {
    const ext = await getInjectedExtension();
    if (!ext) {
        throw new Error('Polkadot extension not installed');
    }

    const challengeMessage = `Authenticate with xCavate WebAgent\nTimestamp: ${Date.now()}\nAddress: ${accountAddress}`;

    let injector;
    if (window.web3FromAddress) {
        injector = await window.web3FromAddress(accountAddress);
    } else if (ext.signer) {
        injector = ext;
    } else {
        throw new Error('No signer available');
    }

    const result = await injector.signer.signRaw({
        address: accountAddress,
        type: 'bytes',
        data: challengeMessage
    });

    connectedAccount = {
        address: accountAddress,
        signature: result.signature,
        message: challengeMessage
    };
    return connectedAccount;
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
 */
export async function signMessage(message) {
    if (!connectedAccount) {
        throw new Error('No wallet connected');
    }

    const injector = await window.web3FromAddress?.(connectedAccount.address) || getInjectedExtension();
    const result = await injector.signer.signRaw({
        address: connectedAccount.address,
        type: 'bytes',
        data: message
    });
    return result.signature;
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

/**
 * Connect wallet for ticket creation (user-initiated)
 * Returns the connected address or null if cancelled/failed
 */
export async function connectWalletForTicket() {
    try {
        const isInstalled = await isPolkadotExtensionInstalled();
        if (!isInstalled) {
            alert('Polkadot extension not found. Please install it to create tickets.');
            return null;
        }

        const accounts = await getAvailableAccounts();
        if (!accounts || accounts.length === 0) {
            alert('No accounts found in your Polkadot extension.');
            return null;
        }

        const selectedAccount = accounts[0];
        const authData = await connectWallet(selectedAccount.address);
        return authData.address;

    } catch (error) {
        console.error('[Wallet] Connection failed:', error.message);
        alert('Failed to connect wallet: ' + error.message);
        return null;
    }
}
