// js/polkadot-auth.js - Polkadot extension wallet authentication module
// Works in both standalone and iframe/injected contexts

let connectedAccount = null;
let enabledInjector = null;

/**
 * Check if Polkadot extension is available in current window
 */
function isPolkadotAvailable() {
    return !!(window.injectedWeb3?.['polkadot-js'] || window.web3FromAddress);
}

/**
 * Get the Polkadot injected extension
 * Enables the extension and returns the injector
 */
async function getInjectedExtension() {
    if (enabledInjector) {
        return enabledInjector;
    }

    console.log('[PolkadotAuth] Checking for Polkadot extension...');
    console.log('[PolkadotAuth] window.injectedWeb3:', !!window.injectedWeb3);
    console.log('[PolkadotAuth] window.injectedWeb3.polkadot-js:', !!window.injectedWeb3?.['polkadot-js']);
    console.log('[PolkadotAuth] window.web3FromAddress:', !!window.web3FromAddress);
    console.log('[PolkadotAuth] Is in iframe:', window !== window.top);

    // Wait for extension to be injected (may take longer in iframes)
    const maxWaitTime = 10000;
    const checkInterval = 200;
    const startTime = Date.now();

    while (!isPolkadotAvailable() && Date.now() - startTime < maxWaitTime) {
        console.log(`[PolkadotAuth] Waiting for extension... (${Date.now() - startTime}ms)`);
        await new Promise(resolve => setTimeout(resolve, checkInterval));
    }

    console.log('[PolkadotAuth] After wait - available:', isPolkadotAvailable());

    try {
        // Try legacy API first (polkadot-js.enable)
        if (window.injectedWeb3?.['polkadot-js']?.enable) {
            console.log('[PolkadotAuth] Enabling via polkadot-js.enable...');
            enabledInjector = await window.injectedWeb3['polkadot-js'].enable('xCavate WebAgent');
            console.log('[PolkadotAuth] Got injector:', !!enabledInjector);
            return enabledInjector;
        }

        // Modern API requires explicit enable via web3Enable
        if (window.web3Enable || window.web3FromAddress) {
            console.log('[PolkadotAuth] Using modern Polkadot.js API (web3Enable)...');

            // Wait for web3Enable to be available (other extensions may load first)
            if (!window.web3Enable) {
                console.log('[PolkadotAuth] Waiting for web3Enable to be injected...');
                const waitStart = Date.now();
                while (!window.web3Enable && Date.now() - waitStart < 3000) {
                    await new Promise(resolve => setTimeout(resolve, 100));
                }
                if (!window.web3Enable) {
                    console.error('[PolkadotAuth] web3Enable not found after waiting');
                    return null;
                }
            }

            // Enable the extension (this triggers the popup if needed)
            // Note: web3Enable enables ALL Polkadot extensions, we filter for polkadot-js
            const enabled = await window.web3Enable('xCavate WebAgent');
            console.log('[PolkadotAuth] web3Enable result:', enabled?.map(e => e.name || e.source));

            if (!enabled || enabled.length === 0) {
                console.log('[PolkadotAuth] No extensions enabled');
                return null;
            }

            // Prefer polkadot-js extension if available among enabled extensions
            const polkadotJsExt = enabled.find(ext =>
                ext.name === 'polkadot-js' || ext.source === 'polkadot-js'
            );
            enabledInjector = polkadotJsExt || enabled[0];
            console.log('[PolkadotAuth] Selected injector:', enabledInjector.name || enabledInjector.source);
            return enabledInjector;
        }

        console.log('[PolkadotAuth] No compatible Polkadot API found');
        return null;

    } catch (error) {
        console.error('[PolkadotAuth] Error enabling extension:', error);
        return null;
    }
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
    // Ensure extension is enabled first
    const ext = await getInjectedExtension();
    if (!ext) {
        throw new Error('Polkadot extension not found');
    }

    // Try to use web3Accounts if available (modern API)
    if (window.web3Accounts) {
        console.log('[PolkadotAuth] Getting accounts via web3Accounts...');
        try {
            const accounts = await window.web3Accounts();
            console.log('[PolkadotAuth] Got accounts:', accounts.length);
            return accounts.map(acc => ({
                address: acc.address,
                name: acc.meta?.name || acc.address.slice(0, 8) + '...'
            }));
        } catch (error) {
            console.error('[PolkadotAuth] Error getting accounts via web3Accounts:', error);
        }
    }

    // Fallback to ext.accounts.subscribe
    if (ext.accounts && ext.accounts.subscribe) {
        console.log('[PolkadotAuth] Getting accounts via ext.accounts.subscribe...');
        return new Promise((resolve) => {
            ext.accounts.subscribe((accounts) => {
                if (accounts) {
                    console.log('[PolkadotAuth] Received accounts via subscribe:', accounts.length);
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

    throw new Error('No accounts method available');
}

/**
 * Connect wallet and request signature for authentication
 */
export async function connectWallet(accountAddress) {
    // Ensure extension is enabled
    const ext = await getInjectedExtension();
    if (!ext) {
        throw new Error('Polkadot extension not installed');
    }

    const challengeMessage = `Authenticate with xCavate WebAgent\nTimestamp: ${Date.now()}\nAddress: ${accountAddress}`;

    let injector;
    // Use web3FromAddress for modern API (works in both standalone and iframe)
    if (window.web3FromAddress) {
        console.log('[PolkadotAuth] Getting injector via web3FromAddress...');
        injector = await window.web3FromAddress(accountAddress);
        console.log('[PolkadotAuth] Got injector:', !!injector);
    } else if (ext.signer) {
        console.log('[PolkadotAuth] Using ext.signer directly');
        injector = ext;
    } else {
        throw new Error('No signer available');
    }

    if (!injector?.signer) {
        throw new Error('Injector has no signer capability');
    }

    console.log('[PolkadotAuth] Signing with address:', accountAddress);

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

    let injector;
    if (window.web3FromAddress) {
        injector = await window.web3FromAddress(connectedAccount.address);
    } else {
        const ext = await getInjectedExtension();
        if (!ext?.signer) {
            throw new Error('No signer available');
        }
        injector = ext;
    }

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
