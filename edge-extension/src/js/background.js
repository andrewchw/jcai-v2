/**
 * Background service worker for the JIRA Chatbot Assistant
 * Handles authentication, notifications, and communication with the Python server
 */

// Constants
const API_BASE_URL = 'http://localhost:8000/api';
const TOKEN_CHECK_INTERVAL = 5 * 60 * 1000; // 5 minutes

// Generate a unique user ID for this browser instance
const USER_ID = `edge-${Date.now()}-${Math.random().toString(36).substring(2, 10)}`;

// Token state
let tokenState = {
    isAuthenticated: false,
    tokenData: null,
    lastChecked: null,
    userId: USER_ID
};

// Initialize the extension
async function initialize() {
    console.log('JIRA Chatbot Assistant background service worker initialized');

    // Load token state from storage
    const storedState = await chrome.storage.local.get(['tokenState']);
    if (storedState.tokenState) {
        // Preserve the generated user ID if not already saved
        const savedUserId = storedState.tokenState.userId;
        tokenState = storedState.tokenState;

        // Make sure we have a user ID (might be missing in older versions)
        if (!tokenState.userId) {
            tokenState.userId = USER_ID;
            // Save the updated token state with the user ID
            await chrome.storage.local.set({ tokenState });
        }

        console.log('Loaded token state from storage:', tokenState.isAuthenticated ? 'Authenticated' : 'Not authenticated');
        console.log('Using user ID:', tokenState.userId);
    } else {
        // No saved state, save the initial state with user ID
        await chrome.storage.local.set({ tokenState });
        console.log('Created new state with user ID:', tokenState.userId);
    }

    // Start periodic token checking
    if (tokenState.isAuthenticated) {
        startTokenChecking();
    }

    // Listen for side panel connection
    chrome.runtime.onConnect.addListener(port => {
        if (port.name === 'sidebar') {
            handleSidebarConnection(port);
        }
    });
}

/**
 * Handle connection with the sidebar
 * @param {*} port - The connection port
 */
function handleSidebarConnection(port) {
    console.log('Sidebar connected');

    // Verify we have the latest authentication state before sending to sidebar
    try {
        // Send initial token state
        port.postMessage({
            type: 'auth-status',
            payload: {
                isAuthenticated: tokenState.isAuthenticated
            }
        });

        // Also send token data if we have it
        if (tokenState.tokenData) {
            port.postMessage({
                type: 'token-status',
                payload: tokenState.tokenData
            });
        }

        console.log('Sent initial token state to sidebar:', tokenState.isAuthenticated);
    } catch (err) {
        console.error('Error sending initial token state to sidebar:', err);
    }

    // Listen for messages from sidebar
    port.onMessage.addListener(async (message) => {
        console.log('Received message from sidebar:', message);

        try {
            switch (message.type) {
                case 'login':
                    initiateLogin();
                    break;

                case 'logout':
                    await performLogout();
                    port.postMessage({
                        type: 'auth-status',
                        payload: {
                            isAuthenticated: false
                        }
                    });
                    break;

                case 'check-token':
                    const tokenStatus = await checkOAuthToken();
                    port.postMessage({
                        type: 'token-status',
                        payload: tokenStatus || { valid: false, status: "unknown" }
                    });
                    break; case 'get-jira-projects':
                    const projects = await fetchJiraProjects();
                    port.postMessage({
                        type: 'jira-projects',
                        payload: projects
                    });

                    // If there was an error but we're still authenticated, explain this to the UI
                    if (projects.error && tokenState.isAuthenticated) {
                        port.postMessage({
                            type: 'jira-api-status',
                            payload: {
                                isAuthenticated: true,
                                jiraApiAccessible: false,
                                error: projects.error
                            }
                        });
                    }
                    break; case 'get-jira-tasks':
                    const tasks = await fetchJiraTasks(message.payload);
                    port.postMessage({
                        type: 'jira-tasks',
                        payload: tasks
                    });

                    // Similarly, notify about Jira API status if there was an error but we're authenticated
                    if (tasks.error && tokenState.isAuthenticated) {
                        port.postMessage({
                            type: 'jira-api-status',
                            payload: {
                                isAuthenticated: true,
                                jiraApiAccessible: false,
                                error: tasks.error
                            }
                        });
                    }
                    break;

                case 'update-user-id':
                    if (message.payload && message.payload.userId) {
                        // Update user ID if it's different
                        if (message.payload.userId !== tokenState.userId) {
                            console.log(`Updating user ID from sidebar: ${message.payload.userId}`);
                            tokenState.userId = message.payload.userId;
                            await chrome.storage.local.set({ tokenState });

                            // Re-check token with new user ID
                            const newTokenStatus = await checkOAuthToken();
                            port.postMessage({
                                type: 'token-status',
                                payload: newTokenStatus || { valid: false, status: "unknown" }
                            });
                        } else {
                            console.log('User ID from sidebar matches current user ID');
                        }
                    }
                    break;
            }
        } catch (error) {
            console.error('Error handling sidebar message:', error);
            port.postMessage({
                type: 'error',
                payload: { message: 'Error processing your request' }
            });
        }
    });

    // Handle disconnect
    port.onDisconnect.addListener(() => {
        console.log('Sidebar disconnected');
    });
}

/**
 * Initiate OAuth login process
 */
function initiateLogin() {
    console.log('Initiating login process');

    // Make sure the user ID is defined and properly saved before proceeding
    if (!tokenState.userId) {
        tokenState.userId = USER_ID;
    }

    // IMPORTANT: Save to storage and wait for it to complete before creating the auth URL
    // This ensures the user ID is consistent between storage and memory
    chrome.storage.local.set({ tokenState }, () => {
        console.log('User ID confirmed in storage:', tokenState.userId);

        // Use the multi-user OAuth v2 endpoint with explicit user ID from tokenState
        const authUrl = `${API_BASE_URL}/auth/oauth/v2/login?user_id=${encodeURIComponent(tokenState.userId)}`;

        console.log('Login URL created with user ID:', tokenState.userId);

        chrome.tabs.create({ url: authUrl }, (tab) => {
            // Track this tab for the OAuth callback
            chrome.tabs.onUpdated.addListener(function listener(tabId, changeInfo, tab) {                // Check if this is our auth tab and if it's on the callback URL
                if (tabId === tab.id && changeInfo.url && changeInfo.url.includes(`/callback`)) {
                    console.log('OAuth callback detected:', changeInfo.url);

                    // Extract success status from URL (e.g., ?success=true)
                    const url = new URL(changeInfo.url);
                    const success = url.searchParams.get('success') === 'true';
                    const isSetupExample = url.searchParams.get('setup_example') === 'true';

                    // Look for user ID in the callback URL
                    let callbackUserId = url.searchParams.get('user_id');

                    // If no user ID in URL params but it's in the state parameter
                    if (!callbackUserId && url.searchParams.has('state')) {
                        const state = url.searchParams.get('state');
                        console.log('Found state parameter:', state);

                        // Extract user ID from state if it's in the format "user_id:XXX"
                        if (state && state.includes('user_id:')) {
                            callbackUserId = state.split('user_id:')[1];
                            console.log('Extracted user ID from state:', callbackUserId);
                        }
                    }

                    // If we found a user ID in the callback, make sure it's consistent
                    if (callbackUserId) {
                        console.log('Callback contains user ID:', callbackUserId);

                        // Update user ID if it's different than what we have
                        if (callbackUserId !== tokenState.userId) {
                            console.log('Updating user ID to match callback:', callbackUserId);
                            tokenState.userId = callbackUserId;
                            chrome.storage.local.set({ tokenState });
                        }
                    }                    // Look for additional indicators of success in the URL
                    const hasCode = url.searchParams.has('code');
                    const isCallback = changeInfo.url.includes('/callback');                    // Consider it a success if:
                    // 1. URL has explicit success=true parameter, OR
                    // 2. URL has an authorization code (OAuth standard), OR
                    // 3. The URL is the callback URL and doesn't have an explicit error parameter
                    const hasError = url.searchParams.has('error') || url.searchParams.has('error_description');
                    const implicitSuccess = (hasCode && isCallback) && !hasError;
                    const explicitSuccess = (success === true) || implicitSuccess;

                    console.log(`Auth callback analyzed: explicit success=${success}, hasCode=${hasCode}, isCallback=${isCallback}, hasError=${hasError}, implicitSuccess=${implicitSuccess}`);

                    // Only process complete auth flow once
                    if (explicitSuccess) {
                        console.log('Authentication successful');
                        chrome.tabs.onUpdated.removeListener(listener);

                        // PERFORMANCE IMPROVEMENT: Update state immediately before async processing
                        // This ensures UI updates happen quickly even if token check takes time
                        tokenState.isAuthenticated = true;
                        chrome.storage.local.set({ tokenState });

                        // Send an immediate notification to update UI
                        notifySidebarsAboutAuth(true);

                        // Then start full async processing
                        handleSuccessfulLogin();

                        // Close the auth tab after a short delay
                        setTimeout(() => {
                            chrome.tabs.remove(tabId);
                        }, 2000);
                    } else if (isSetupExample) {
                        // This is the setup example flow, wait for the success parameter to be added
                        console.log('Setup example flow detected, waiting for completion');
                        // Don't remove the listener yet, as the auth page may redirect with success=true
                    } else {
                        // This is a failure callback
                        console.error('Authentication failed');
                        chrome.tabs.onUpdated.removeListener(listener);

                        // Notify any open sidebars
                        chrome.runtime.sendMessage({
                            type: 'auth-failed',
                            payload: {
                                message: 'Authentication failed. Please try again.'
                            }
                        });

                        // Close the auth tab
                        setTimeout(() => {
                            chrome.tabs.remove(tabId);
                        }, 2000);
                    }
                }
            });
        });
    });
}

/**
 * Handle successful login
 */
async function handleSuccessfulLogin() {
    // Log the current state for debugging
    console.log('Handling successful login with user ID:', tokenState.userId);

    // Store the current user ID first to ensure we don't lose it
    const currentUserId = tokenState.userId || USER_ID;

    // Ensure we have a valid user ID
    if (!tokenState.userId) {
        console.error('No user ID found during login completion! Using fallback USER_ID');
        tokenState.userId = USER_ID;
        // Save immediately to ensure consistency
        await chrome.storage.local.set({ tokenState });
    }

    // We've already set isAuthenticated=true in the callback for immediate UI feedback
    // so no need to update it here again, but we'll ensure storage is updated

    // Start periodic token checking right away to get token info quickly
    startTokenChecking();

    console.log('Immediately requesting token status to update UI quickly...');

    // Now check the token with the confirmed user ID to get complete token info
    const tokenStatus = await checkOAuthToken();

    // Even if token check fails, we should remain authenticated at this point
    // as the login was already successful

    // Update tokenState with complete info
    tokenState = {
        isAuthenticated: true,  // Always set to true on successful login
        tokenData: tokenStatus || { status: "active", valid: true },
        lastChecked: new Date().toISOString(),
        userId: currentUserId // Use saved ID from before
    };

    // Log what we're saving to storage
    console.log('Saving authenticated state with user ID:', tokenState.userId);

    // Save to storage
    await chrome.storage.local.set({ tokenState });

    // Send detailed token data to UI if available
    if (tokenStatus) {
        try {
            chrome.runtime.sendMessage({
                type: 'token-status',
                payload: tokenStatus
            });
            console.log('Sent detailed token status via runtime.sendMessage');
        } catch (err) {
            console.error('Error sending token status message:', err);
        }
    }

    console.log('Authentication process completed successfully');
}

/**
 * Notify all sidebars about authentication status 
 * @param {boolean} isAuthenticated - The current authentication status
 */
async function notifySidebarsAboutAuth(isAuthenticated) {
    console.log('Notifying all sidebars about auth status:', isAuthenticated);

    // PERFORMANCE OPTIMIZATION: Use all available notification methods in parallel
    // to ensure at least one reaches the UI as quickly as possible

    // Method 1: Use runtime messaging (works for non-connected panels)
    const runtimePromise = new Promise(resolve => {
        try {
            chrome.runtime.sendMessage({
                type: 'auth-status',
                payload: {
                    isAuthenticated: isAuthenticated,
                    timestamp: Date.now() // Include timestamp for freshness check
                }
            });
            console.log('Sent auth status via runtime.sendMessage');
            resolve(true);
        } catch (err) {
            console.error('Error sending runtime message:', err);
            resolve(false);
        }
    });

    // Method 2: Use direct port connections (more reliable for connected panels)
    const portsPromise = new Promise(resolve => {
        try {
            // Chrome Extensions API changed over time, handle multiple cases
            const ports = chrome.extension?.getConnections ?
                chrome.extension.getConnections() :
                (chrome.runtime?.connections || []);

            console.log(`Attempting to notify ${ports.length} direct connections`);

            // Send to each connected port
            if (ports && ports.length > 0) {
                ports.forEach(port => {
                    if (port.name === 'sidebar') {
                        try {
                            port.postMessage({
                                type: 'auth-status',
                                payload: {
                                    isAuthenticated: isAuthenticated,
                                    timestamp: Date.now()
                                }
                            });
                            console.log('Directly notified sidebar port');
                        } catch (err) {
                            console.error('Error sending to port:', err);
                        }
                    }
                });
                resolve(true);
            } else {
                console.log('No direct ports found to communicate with sidebar');
                resolve(false);
            }
        } catch (err) {
            console.error('Error accessing extension ports:', err);
            resolve(false);
        }
    });

    // Method 3: Store in local storage as a fallback mechanism
    // This helps when the sidebar is opened after authentication
    const storagePromise = new Promise(resolve => {
        try {
            chrome.storage.local.set({
                lastAuthStatus: {
                    isAuthenticated: isAuthenticated,
                    timestamp: Date.now()
                }
            });
            console.log('Saved auth status to local storage as fallback');
            resolve(true);
        } catch (err) {
            console.error('Error saving auth status to storage:', err);
            resolve(false);
        }
    });

    // Wait for all notification methods to complete
    const [runtimeResult, portsResult, storageResult] = await Promise.all([
        runtimePromise, portsPromise, storagePromise
    ]);

    console.log(`Notification results - Runtime: ${runtimeResult}, Ports: ${portsResult}, Storage: ${storageResult}`);
    return runtimeResult || portsResult || storageResult;
}

/**
 * Check OAuth token status
 * @param {Object} options - Options for token check
 * @param {boolean} options.forceCheck - Force a check even if recently checked
 * @param {boolean} options.timeoutMs - Timeout in milliseconds
 * @returns {Promise<Object>} Token status data
 */
async function checkOAuthToken(options = {}) {
    const { forceCheck = false, timeoutMs = 5000 } = options;

    try {
        // Skip check if we've checked recently (within last 30 seconds) unless forced
        const now = Date.now();
        const lastCheckedTimestamp = tokenState.lastChecked ? new Date(tokenState.lastChecked).getTime() : 0;
        const timeSinceLastCheck = now - lastCheckedTimestamp;

        if (!forceCheck && tokenState.tokenData && timeSinceLastCheck < 30000) {
            console.log(`Using cached token status, last checked ${timeSinceLastCheck}ms ago`);
            return tokenState.tokenData;
        }

        // Ensure we have a valid user ID before making the request
        if (!tokenState.userId) {
            console.error('Missing user ID when checking token status, setting default');
            tokenState.userId = USER_ID;
            await chrome.storage.local.set({ tokenState });
        }

        console.log(`Checking token status for user ID: ${tokenState.userId}`);

        // Create a promise that rejects after timeout to prevent long hanging requests
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error(`Token check timed out after ${timeoutMs}ms`)), timeoutMs);
        });

        // Create the actual fetch promise
        const fetchPromise = fetch(`${API_BASE_URL}/auth/oauth/v2/token/status?user_id=${encodeURIComponent(tokenState.userId)}`);

        // Race the fetch against the timeout
        const response = await Promise.race([fetchPromise, timeoutPromise]);

        if (!response.ok) {
            console.error(`Token status check failed with status: ${response.status}`);

            // In case of a 401/403 Unauthorized response, mark as not authenticated
            if (response.status === 401 || response.status === 403) {
                console.log('Received unauthorized response, marking as not authenticated');
                tokenState.isAuthenticated = false;
                await chrome.storage.local.set({ tokenState });

                // Notify sidebars that authentication is now invalid
                await notifySidebarsAboutAuth(false);
            }

            throw new Error('Failed to check token status');
        }

        const data = await response.json();
        console.log('Token status (detailed):', JSON.stringify(data, null, 2));

        // Update auth state based on token status
        // Server might return different formats, check all possible fields
        const isActive = data &&
            (data.status === "active" ||
                data.valid === true ||
                data.expires_in_seconds > 0);

        console.log('Token active state determined:', isActive);

        // If authentication state changed, update UI
        if (tokenState.isAuthenticated !== isActive) {
            console.log(`Authentication state changed from ${tokenState.isAuthenticated} to ${isActive}`);

            // Always update isAuthenticated based on token status
            tokenState.isAuthenticated = isActive;

            // Notify sidebars about the change
            await notifySidebarsAboutAuth(isActive);
        } else {
            // Always update isAuthenticated based on token status
            tokenState.isAuthenticated = isActive;
        }

        // Update token data
        tokenState.tokenData = data;
        tokenState.tokenData.user_id = tokenState.userId; // Ensure user ID is in token data
        tokenState.lastChecked = new Date().toISOString();

        // Save to storage
        await chrome.storage.local.set({ tokenState });

        // Always send token status update, even if auth state didn't change
        try {
            chrome.runtime.sendMessage({
                type: 'token-status',
                payload: data
            });
        } catch (error) {
            console.error('Error sending token status update:', error);
        }

        return data;
    } catch (error) {
        console.error('Error checking token:', error);
        return null;
    }
}

/**
 * Start periodic token checking
 */
function startTokenChecking() {
    console.log('Starting periodic token checking');

    // Clear any existing interval
    if (self.tokenCheckIntervalId) {
        clearInterval(self.tokenCheckIntervalId);
    }

    // Set new interval
    self.tokenCheckIntervalId = setInterval(async () => {
        console.log('Checking token status...');
        const tokenStatus = await checkOAuthToken();

        if (tokenStatus && (tokenStatus.valid || tokenStatus.status === "active")) {
            // Update token state
            tokenState = {
                ...tokenState,
                tokenData: tokenStatus,
                lastChecked: new Date().toISOString()
            };

            // Save to storage
            await chrome.storage.local.set({ tokenState });

            // Notify any open sidebars
            chrome.runtime.sendMessage({
                type: 'token-status',
                payload: tokenStatus
            });
        } else {
            // Token is no longer valid
            console.log('Token is no longer valid');
            await performLogout();
        }
    }, TOKEN_CHECK_INTERVAL);
}

/**
 * Perform logout
 */
async function performLogout() {
    try {
        // Call logout API - use the multi-user v2 endpoint with user ID
        await fetch(`${API_BASE_URL}/auth/oauth/v2/logout?user_id=${encodeURIComponent(tokenState.userId)}`);

        // Reset token state but preserve user ID
        const userId = tokenState.userId;
        tokenState = {
            isAuthenticated: false,
            tokenData: null,
            lastChecked: null,
            userId: userId // Preserve the user ID
        };        // Clear from storage
        await chrome.storage.local.set({ tokenState });

        // Stop token checking
        if (self.tokenCheckIntervalId) {
            clearInterval(self.tokenCheckIntervalId);
            self.tokenCheckIntervalId = null;
        }

        console.log('Logout successful');
        return true;
    } catch (error) {
        console.error('Error during logout:', error);
        return false;
    }
}

/**
 * Fetch Jira projects
 */
async function fetchJiraProjects() {
    try {
        console.log(`Fetching Jira projects for user ${tokenState.userId}`);

        // First check if the token is actually valid by doing a status check
        const tokenStatus = await checkOAuthToken();
        if (!tokenStatus || !tokenStatus.valid) {
            console.error('Token invalid or expired, cannot fetch projects');
            // Update UI state to reflect the authentication issue
            await notifySidebarsAboutAuth(false);
            throw new Error('Authentication token invalid or expired');
        }

        const response = await fetch(`${API_BASE_URL}/jira/v2/projects?user_id=${encodeURIComponent(tokenState.userId)}`);

        // Get detailed error info if available
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Server responded with ${response.status} ${response.statusText}: ${errorText}`);
            throw new Error(`Failed to fetch projects (${response.status}: ${response.statusText})`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching projects:', error);
        // Return empty array but with error info that can be displayed
        return { items: [], error: error.message };
    }
}

/**
 * Fetch Jira tasks
 */
async function fetchJiraTasks(filters = {}) {
    try {
        console.log(`Fetching Jira tasks for user ${tokenState.userId} with filters:`, filters);

        // First check if the token is actually valid
        const tokenStatus = await checkOAuthToken();
        if (!tokenStatus || !tokenStatus.valid) {
            console.error('Token invalid or expired, cannot fetch tasks');
            // Update UI state to reflect the authentication issue
            await notifySidebarsAboutAuth(false);
            throw new Error('Authentication token invalid or expired');
        }

        const url = new URL(`${API_BASE_URL}/jira/v2/issues`);

        // Add user ID for multi-user support
        url.searchParams.append('user_id', tokenState.userId);

        // Add filters to query params
        if (filters.project) url.searchParams.append('project', filters.project);
        if (filters.status) url.searchParams.append('status', filters.status);

        console.log(`Sending request to ${url.toString()}`);
        const response = await fetch(url);

        // Get detailed error info if available
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Server responded with ${response.status} ${response.statusText}: ${errorText}`);
            throw new Error(`Failed to fetch tasks (${response.status}: ${response.statusText})`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching tasks:', error);
        // Return empty array but with error info that can be displayed
        return { items: [], error: error.message };
    }
}

// Initialize on service worker activation
initialize();
