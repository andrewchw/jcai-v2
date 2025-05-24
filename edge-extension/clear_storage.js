// This script helps diagnose and clear the extension's storage to resolve issues
// Run this in the browser console while the extension is open

async function displayStorage() {
    const data = await chrome.storage.local.get(null);
    console.log('CURRENT STORAGE CONTENTS:');
    console.log(JSON.stringify(data, null, 2));
    return data;
}

async function clearAllStorage() {
    console.log('Attempting to clear all extension storage...');
    await chrome.storage.local.clear();
    console.log('Storage cleared successfully');
    console.log('Please reload the extension now');
}

async function clearTokenState() {
    console.log('Attempting to reset authentication state...');
    // Preserve user ID but reset auth state
    const data = await chrome.storage.local.get('tokenState');
    if (data && data.tokenState) {
        const userId = data.tokenState.userId;
        await chrome.storage.local.set({
            tokenState: {
                isAuthenticated: false,
                tokenData: null,
                lastChecked: new Date().toISOString(),
                userId: userId
            }
        });
        console.log('Auth state reset but preserved user ID:', userId);
    } else {
        console.log('No token state found to reset');
    }
}

async function fixTokenStateIssues() {
    console.log('Attempting to fix token state issues...');
    const data = await chrome.storage.local.get('tokenState');
    if (data && data.tokenState) {
        // Fix common issues
        if (!data.tokenState.userId) {
            data.tokenState.userId = 'fixed-' + Date.now().toString(36);
            console.log('Added missing user ID:', data.tokenState.userId);
        }

        // Set explicit auth state and clear problematic fields
        data.tokenState.isAuthenticated = false;
        data.tokenState.lastChecked = new Date().toISOString();

        await chrome.storage.local.set({ tokenState: data.tokenState });
        console.log('Token state fixed');
    } else {
        console.log('No token state found to fix');
    }
}

// Display options
console.log('JIRA Chatbot Extension Storage Utility');
console.log('Available commands:');
console.log('1. displayStorage() - Show current storage contents');
console.log('2. clearAllStorage() - Clear all storage (requires reload)');
console.log('3. clearTokenState() - Reset authentication state only');
console.log('4. fixTokenStateIssues() - Attempt to fix token state issues');

// Display current storage by default
displayStorage();
