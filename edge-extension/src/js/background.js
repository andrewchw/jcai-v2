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
    userId: USER_ID,
    userInfo: null // Added to store user information
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
                isAuthenticated: tokenState.isAuthenticated,
                userInfo: tokenState.userInfo // Send user info
            }
        });

        // Also send token data if we have it
        if (tokenState.tokenData) {
            port.postMessage({
                type: 'token-status',
                payload: tokenState.tokenData // This might also contain user info
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
                            isAuthenticated: false,
                            userInfo: null // Clear user info on logout
                        }
                    });
                    break;

                case 'check-token':
                    const tokenStatus = await checkOAuthToken(); // This function will be updated to fetch/include user info
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

    const currentUserId = tokenState.userId || USER_ID;

    // Ensure we have a valid user ID
    if (!tokenState.userId) {
        console.error('No user ID found during login completion! Using fallback USER_ID');
        tokenState.userId = USER_ID;
        // Save immediately to ensure consistency
        await chrome.storage.local.set({ tokenState });
    }

    // We've already set isAuthenticated=true in the callback for immediate UI feedback
    tokenState.isAuthenticated = true;

    // 1. Fetch user information (especially displayName)
    // This is the primary source for the user's display name.
    let fetchedUserInfo = await fetchUserInfo(currentUserId);

    // 2. Check/refresh OAuth token details (like expiry, scope, etc.)
    // Pass forceCheck true to ensure we get fresh data after login.
    // The updated checkOAuthToken will preserve displayName if the /token/status response doesn't have it.
    const tokenStatus = await checkOAuthToken({ forceCheck: true });

    // 3. Consolidate userInfo
    // Prioritize userInfo with displayName from fetchUserInfo.
    // If fetchUserInfo failed or didn't return displayName,
    // and if tokenStatus has a 'user' object, use that as a fallback.
    // Otherwise, userInfo remains null.
    if (fetchedUserInfo && fetchedUserInfo.displayName) {
        tokenState.userInfo = fetchedUserInfo;
    } else if (tokenStatus && tokenStatus.user && tokenStatus.user.displayName) {
        // If token/status unexpectedly provides a full user object with displayName
        tokenState.userInfo = tokenStatus.user;
    } else if (tokenStatus && tokenStatus.user && !tokenState.userInfo) {
        // If fetchUserInfo failed AND tokenState.userInfo is still null,
        // use tokenStatus.user as a last resort (might lack displayName).
        tokenState.userInfo = tokenStatus.user;
    } else if (!fetchedUserInfo) {
        // If fetchUserInfo failed and no other source, ensure it's null or keep existing if any.
        // If tokenState.userInfo was already populated by a previous valid fetch,
        // and this fetchUserInfo failed, we might want to keep the old one.
        // For now, if fetchUserInfo returns null, we reflect that, unless checkOAuthToken provided one.
        // The logic in checkOAuthToken will handle preserving existing tokenState.userInfo if its call is the one without displayName.
        // This specific spot: if fetchUserInfo is null, tokenState.userInfo is what checkOAuthToken left it as, or null.
    }


    // Update tokenState with all information
    tokenState = {
        isAuthenticated: true,
        tokenData: tokenStatus || { status: "active", valid: true }, // Use fresh token data
        lastChecked: new Date().toISOString(),
        userId: currentUserId,
        userInfo: tokenState.userInfo // Persist the consolidated user info
    };

    // Log what we're saving to storage
    console.log('Saving authenticated state with user ID:', tokenState.userId, 'and user info:', tokenState.userInfo);
    await chrome.storage.local.set({ tokenState });

    // Notify sidebars with the updated auth status including the best available user info
    await notifySidebarsAboutAuth(true, tokenState.userInfo);

    // Send detailed token data to UI if available (sidebar might use it for more than just auth status)
    if (tokenStatus) {
        try {
            chrome.runtime.sendMessage({
                type: 'token-status',
                payload: tokenState.tokenData
            });
            console.log('Sent detailed token status via runtime.sendMessage after login');
        } catch (err) {
            console.error('Error sending token status message post-login:', err);
        }
    }

    // Start periodic token checking if not already running or if stopped
    startTokenChecking();

    console.log('Authentication process completed successfully with user info.');
}

/**
 * Notify all sidebars about authentication status 
 * @param {boolean} isAuthenticated - The current authentication status
 * @param {object} userInfo - Optional user information
 */
async function notifySidebarsAboutAuth(isAuthenticated, userInfo = null) {
    console.log('Notifying all sidebars about auth status:', isAuthenticated, 'User Info:', userInfo);

    // PERFORMANCE OPTIMIZATION: Use all available notification methods in parallel
    // to ensure at least one reaches the UI as quickly as possible

    // Method 1: Use runtime messaging (works for non-connected panels)
    const runtimePromise = new Promise(resolve => {
        try {
            chrome.runtime.sendMessage({
                type: 'auth-status',
                payload: {
                    isAuthenticated: isAuthenticated,
                    userInfo: isAuthenticated ? (userInfo || tokenState.userInfo) : null, // Include user info
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
                                    userInfo: isAuthenticated ? (userInfo || tokenState.userInfo) : null, // Include user info
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
                    userInfo: isAuthenticated ? (userInfo || tokenState.userInfo) : null, // Include user info
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
                tokenState.userInfo = null; // Clear user info on auth failure
                await chrome.storage.local.set({ tokenState });
                await notifySidebarsAboutAuth(false);
            } else {
                // For other errors, we might not invalidate auth immediately,
                // but we won't have new token data.
                // However, if token is invalid, clear user info.
                tokenState.userInfo = null; // Clear user info on error
                await chrome.storage.local.set({ tokenState }); // Save updated state
                await notifySidebarsAboutAuth(tokenState.isAuthenticated, null); // Notify UI, keep current auth state if not 401/403
            }
            throw new Error(`Failed to check token status: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        console.log('Token status (detailed from /token/status):', JSON.stringify(data, null, 2));

        const isActive = data && (data.status === "active" || data.valid === true || data.expires_in_seconds > 0);
        let newPotentialUserInfo = null;

        if (isActive) {
            if (data.user && data.user.displayName) {
                // If /token/status provides a user object with displayName, use it.
                newPotentialUserInfo = data.user;
            } else if (data.user && !data.user.displayName && tokenState.userInfo && tokenState.userInfo.displayName) {
                // If /token/status provides a user object WITHOUT displayName,
                // but we already have a userInfo with displayName, keep the existing one.
                newPotentialUserInfo = tokenState.userInfo;
            } else if (data.user) {
                // If /token/status provides a user object without displayName, and we don't have a better one.
                newPotentialUserInfo = data.user;
            }
            else {
                // If /token/status provides no user object, preserve existing userInfo.
                newPotentialUserInfo = tokenState.userInfo;
            }
        } else {
            // Token is not active, clear user info.
            newPotentialUserInfo = null;
        }

        // Check if authentication state or user info actually changed
        const authChanged = tokenState.isAuthenticated !== isActive;
        const userInfoChanged = JSON.stringify(tokenState.userInfo) !== JSON.stringify(newPotentialUserInfo);

        if (authChanged || userInfoChanged) {
            console.log(`Auth state or user info changed. Auth: ${tokenState.isAuthenticated} -> ${isActive}. UserInfo changed: ${userInfoChanged}`);
            tokenState.isAuthenticated = isActive;
            tokenState.userInfo = newPotentialUserInfo;
            await notifySidebarsAboutAuth(isActive, tokenState.userInfo);
        } else {
            // Ensure internal state is consistent even if no notification needed
            tokenState.isAuthenticated = isActive;
            tokenState.userInfo = newPotentialUserInfo;
        }

        tokenState.tokenData = data; // Store the full response from /token/status
        tokenState.lastChecked = new Date().toISOString();
        await chrome.storage.local.set({ tokenState });

        return tokenState.tokenData;

    } catch (error) {
        console.error('Error checking OAuth token:', error);
        // On error, assume token might be invalid, but preserve user ID.
        // Critical: if checkOAuthToken fails, what happens to isAuthenticated?
        // If it was a network error, not an auth error, we might want to keep isAuthenticated true but flag data as stale.
        // For now, the logic above handles 401/403 by setting isAuthenticated = false.
        // For other errors, isAuthenticated might remain true from a previous successful check.
        // Let's ensure userInfo is cleared if we can't confirm token validity.
        const previousAuthStatus = tokenState.isAuthenticated;
        tokenState.isAuthenticated = false; // Safer to assume false if check fails badly
        tokenState.tokenData = null;
        tokenState.userInfo = null;
        tokenState.lastChecked = new Date().toISOString();
        await chrome.storage.local.set({ tokenState });
        if (previousAuthStatus) { // Only notify if it was previously true
            await notifySidebarsAboutAuth(false); // Notify UI about failure
        }
        return { valid: false, status: "error", error: error.message, user: null };
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
    console.log('Performing logout for user ID:', tokenState.userId);
    try {
        // Call the server endpoint to invalidate the token, if applicable
        if (tokenState.userId) {
            await fetch(`${API_BASE_URL}/auth/oauth/v2/logout?user_id=${encodeURIComponent(tokenState.userId)}`, {
                method: 'POST', // Or GET, depending on your API
            });
        }
    } catch (error) {
        console.error('Error during server-side logout:', error);
        // Continue with client-side logout even if server call fails
    }

    // Clear local token state
    tokenState.isAuthenticated = false;
    tokenState.tokenData = null;
    tokenState.lastChecked = new Date().toISOString();
    tokenState.userInfo = null; // Clear user info

    // Remove from storage
    await chrome.storage.local.remove(['tokenState', 'lastAuthStatus']);
    // For safety, also set a default empty state back
    await chrome.storage.local.set({
        tokenState: {
            isAuthenticated: false,
            tokenData: null,
            lastChecked: null,
            userId: tokenState.userId, // Keep userId for potential re-login
            userInfo: null
        }
    });


    // Stop periodic token checking
    stopTokenChecking();

    // Notify sidebars
    await notifySidebarsAboutAuth(false);

    console.log('Logout complete.');
}

// Placeholder function for fetching user info - replace with your actual implementation
async function fetchUserInfo(userId) {
    if (!userId) {
        console.warn('fetchUserInfo called without userId');
        return null;
    }
    console.log('Fetching user info for user ID:', userId);
    try {
        const response = await fetch(`${API_BASE_URL}/user/profile?user_id=${encodeURIComponent(userId)}`);
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Failed to fetch user profile for ${userId}. Status: ${response.status}. Body: ${errorText}`);
            throw new Error(`Failed to fetch user profile: ${response.status}`);
        }
        const userData = await response.json();
        console.log('User data received:', userData);

        if (userData && userData.displayName) {
            return {
                displayName: userData.displayName,
                // Include other fields if your sidebar needs them, e.g., accountId, avatarUrls
                // accountId: userData.accountId, 
                // emailAddress: userData.emailAddress 
            };
        } else {
            console.warn('User data from /user/profile does not contain displayName:', userData);
            return null;
        }
    } catch (error) {
        console.error('Error fetching user info:', error);
        return null;
    }
}

// Initialize the extension
initialize();
