// This script helps diagnose port connection issues between sidebar and background script
console.log('Diagnosing port connection issues...');

// Function to check port status
function checkPortStatus() {
    // Check if port is defined
    if (typeof port === 'undefined') {
        console.error('ERROR: port is undefined - The port variable is not initialized');
        return false;
    } else {
        console.log('✓ Port variable exists');

        // Check if port has postMessage method
        if (typeof port.postMessage !== 'function') {
            console.error('ERROR: port.postMessage is not a function - The port may be disconnected');
            return false;
        } else {
            console.log('✓ port.postMessage is a function');

            // Try to send a test message
            try {
                port.postMessage({ type: 'ping', timestamp: Date.now() });
                console.log('✓ Successfully sent test message');
                return true;
            } catch (e) {
                console.error('ERROR: Failed to send message through port:', e);
                return false;
            }
        }
    }
}

// Function to check state and timestamps
function checkStateTimestamps() {
    if (typeof state === 'undefined') {
        console.error('ERROR: state is undefined - The state variable is not initialized');
        return;
    }

    console.log('=== STATE TIMESTAMPS ===');
    const now = Date.now();

    // Format time differences
    const formatTimeDiff = (timestamp) => {
        if (!timestamp) return 'never';
        const diffMs = now - timestamp;
        if (diffMs < 1000) return `${diffMs}ms ago`;
        if (diffMs < 60000) return `${Math.floor(diffMs / 1000)}s ago`;
        if (diffMs < 3600000) return `${Math.floor(diffMs / 60000)}m ago`;
        return `${Math.floor(diffMs / 3600000)}h ago`;
    };

    console.log(`Last token check: ${formatTimeDiff(state.lastTokenCheck)}`);
    console.log(`Last projects check: ${formatTimeDiff(state.lastProjectsCheck)}`);
    console.log(`Last tasks check: ${formatTimeDiff(state.lastTasksCheck)}`);

    console.log('\n=== CONNECTION STATE ===');
    console.log(`Authenticated: ${state.isAuthenticated}`);
    console.log(`Server connected: ${state.serverConnected}`);
    console.log(`User ID: ${state.userId}`);
}

// Function to attempt reconnection
async function attemptReconnection() {
    console.log('\n=== ATTEMPTING RECONNECTION ===');
    try {
        // First, try to disconnect the existing port
        if (typeof port !== 'undefined') {
            try {
                port.disconnect();
                console.log('Successfully disconnected existing port');
            } catch (e) {
                console.log('No active port to disconnect or error:', e);
            }
        }

        // Now try to reconnect
        if (typeof connectToBackground === 'function') {
            await connectToBackground();
            console.log('Reconnection function executed - checking new port status...');
            setTimeout(() => {
                const connected = checkPortStatus();
                console.log(`Reconnection ${connected ? 'SUCCESSFUL' : 'FAILED'}`);
            }, 500);
        } else {
            console.error('ERROR: connectToBackground function not found');
        }
    } catch (e) {
        console.error('Failed to reconnect:', e);
    }
}

// Run diagnostics
console.log('=== PORT CONNECTION DIAGNOSTIC ===');
const portOk = checkPortStatus();
checkStateTimestamps();

// Offer reconnection if port is problematic
if (!portOk) {
    console.log('\nPort connection issues detected. Run attemptReconnection() to try fixing it.');
} else {
    console.log('\nPort connection seems OK. If you still have issues, run attemptReconnection().');
}
