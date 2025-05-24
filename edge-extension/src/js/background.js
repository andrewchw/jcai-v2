/**
 * Background service worker for the JIRA Chatbot Assistant
 * Handles authentication, notifications, and communication with the Python server
 */

// Constants
const API_BASE_URL = 'http://localhost:8000/api';
const TOKEN_CHECK_INTERVAL = 5 * 60 * 1000; // 5 minutes (default)
const FAST_TOKEN_CHECK_INTERVAL = 30 * 1000; // 30 seconds (right after auth)
const FAST_CHECK_DURATION = 5 * 60 * 1000; // Use fast checking for 5 minutes after auth
const DEBUG_MODE = true; // Enable for more verbose logging

// Generate a unique user ID for this browser instance
const USER_ID = `edge-${Date.now()}-${Math.random().toString(36).substring(2, 10)}`;

// Token state
let tokenState = {
    isAuthenticated: false,
    tokenData: null,
    lastChecked: null,
    userId: USER_ID,
    userInfo: null, // Added to store user information
    lastAuthTime: null // Track when authentication was completed for smart intervals
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
    console.log('Sidebar connected');    // Verify we have the latest authentication state before sending to sidebar
    try {
        // Ensure the port is valid before posting
        if (!port || typeof port.postMessage !== 'function') {
            console.error('Invalid port object when sending initial auth state');
            return;
        }

        // Send initial token state
        port.postMessage({
            type: 'auth-status',
            payload: {
                isAuthenticated: tokenState.isAuthenticated === true, // Force boolean
                userInfo: tokenState.userInfo, // Send user info
                status: tokenState.isAuthenticated ? 'authenticated' : 'unauthenticated',
                timestamp: Date.now(), // Include timestamp for debugging
                source: 'initial-connection'
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
    }    // Listen for messages from sidebar
    port.onMessage.addListener(async (message) => {
        console.log('Received message from sidebar:', message);

        // Add validation for message
        if (!message || typeof message !== 'object') {
            console.error('Invalid message received from sidebar:', message);
            return;
        }

        try {
            switch (message.type) {
                case 'login':
                    initiateLogin();
                    break; case 'logout':
                    await performLogout();
                    port.postMessage({
                        type: 'auth-status',
                        payload: {
                            isAuthenticated: false,
                            userInfo: null, // Clear user info on logout
                            timestamp: Date.now(),
                            action: 'logout'
                        }
                    });
                    break; case 'check-token':
                    try {
                        console.log('Received check-token request from sidebar');
                        const tokenStatus = await checkOAuthToken(); // This function will be updated to fetch/include user info
                        port.postMessage({
                            type: 'token-status',
                            payload: tokenStatus || { valid: false, status: "unknown", timestamp: new Date().toISOString() }
                        });

                        // Also update auth status since this might be a recovery request
                        if (tokenStatus) {
                            const isAuthenticated = tokenStatus.valid === true ||
                                tokenStatus.status === "active" ||
                                (tokenStatus.expires_in_seconds && tokenStatus.expires_in_seconds > 0);

                            port.postMessage({
                                type: 'auth-status',
                                payload: {
                                    isAuthenticated: isAuthenticated,
                                    source: 'token-check',
                                    timestamp: Date.now(),
                                    userInfo: tokenStatus.user
                                }
                            });
                        }
                    } catch (error) {
                        console.error('Error checking token:', error);
                        port.postMessage({
                            type: 'token-status',
                            payload: {
                                valid: false,
                                status: "error",
                                error: error.message,
                                timestamp: new Date().toISOString()
                            }
                        });
                    }
                    break;

                case 'get-jira-projects':
                    // Only fetch projects if we're properly authenticated
                    if (tokenState.isAuthenticated) {
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
                    } else {
                        port.postMessage({
                            type: 'jira-projects',
                            payload: { error: 'Not authenticated', projects: [] }
                        });
                    }
                    break;

                case 'get-jira-tasks':
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

    // Handle disconnect    // Function to fetch Jira projects
    async function fetchJiraProjects() {
        try {
            // Only fetch if we're authenticated
            if (!tokenState.isAuthenticated) {
                console.log('Not authenticated, skipping project fetch');
                return { error: 'Not authenticated', projects: [] };
            }

            console.log(`Fetching projects for user ID: ${tokenState.userId}`);
            const response = await fetch(`${API_BASE_URL}/jira/v2/projects?user_id=${encodeURIComponent(tokenState.userId)}`);

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`Failed to fetch projects: ${response.status} - ${errorText}`);
                throw new Error(`Failed to fetch projects: ${response.status} - ${errorText}`);
            }

            const data = await response.json();
            console.log('Raw projects API response:', data);

            // Ensure data is formatted correctly before returning
            if (Array.isArray(data)) {
                // If the API returns an array directly, wrap it in the expected format
                console.log(`Returning ${data.length} projects in wrapped format`);
                return { projects: data };
            } else if (data && typeof data === 'object') {
                // If it's already an object, make sure it has a projects array
                if (!data.projects) {
                    console.log('API response is an object but missing projects array, creating empty array');
                    data.projects = [];
                } else if (!Array.isArray(data.projects)) {
                    // If projects exists but isn't an array, fix it
                    console.warn('API returned projects that is not an array:', data.projects);
                    data.projects = Array.isArray(data.projects) ? data.projects : [];
                }
                console.log(`Returning object with ${data.projects.length} projects`);
                return data;
            }

            // Fallback if we received unexpected data
            console.warn('Received unexpected data format from projects API:', data);
            return { error: 'Unexpected data format', projects: [] };
        } catch (error) {
            console.error('Error fetching projects:', error);
            return { error: error.message, projects: [] };
        }
    }    // Function to fetch Jira tasks
    async function fetchJiraTasks(filters = {}) {
        try {
            // Only fetch if we're authenticated
            if (!tokenState.isAuthenticated) {
                console.log('Not authenticated, skipping tasks fetch');
                return { error: 'Not authenticated', tasks: [] };
            }

            // Construct the URL with filters and user_id
            const url = new URL(`${API_BASE_URL}/jira/v2/issues`);
            url.searchParams.append('user_id', encodeURIComponent(tokenState.userId));

            // Always add a limit to prevent unbounded queries
            url.searchParams.append('max_results', filters.maxResults || '50');

            // Handle JQL parameter - this is the most important part for preventing "Unbounded JQL" errors
            if (filters.jql) {
                // Use the JQL directly from the filters if provided
                url.searchParams.append('jql', filters.jql);
                console.log('Using JQL from filters:', filters.jql);
            } else {
                // If no explicit JQL, construct one based on filters
                let jql = '';

                if (filters.project) {
                    jql = `project = ${filters.project}`;

                    if (filters.status) {
                        jql += ` AND status = "${filters.status}"`;
                    }
                } else {
                    // If no project filter, use date restriction
                    jql = 'updated >= -30d';

                    if (filters.status) {
                        jql += ` AND status = "${filters.status}"`;
                    }
                }

                // Always add ordering
                jql += ' ORDER BY updated DESC';

                url.searchParams.append('jql', jql);
                console.log('Constructed JQL:', jql);
            }

            // These individual parameters are used by the server if JQL is not provided
            // Keep them for backward compatibility, but our primary filtering is now via JQL
            if (filters.project) url.searchParams.append('project', filters.project);
            if (filters.status) url.searchParams.append('status', filters.status);

            console.log(`Fetching Jira tasks with filters:`, filters);
            console.log(`Full request URL: ${url.toString()}`);
            const response = await fetch(url);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed to fetch tasks: ${response.status} - ${errorText}`);
            }

            const data = await response.json();

            // Ensure data is formatted correctly before returning
            if (Array.isArray(data)) {
                // If the API returns an array directly, wrap it in the expected format
                return { tasks: data };
            } else if (data && typeof data === 'object') {
                // If it's already an object, make sure it has a tasks array
                if (!data.tasks) {
                    data.tasks = [];
                } else if (!Array.isArray(data.tasks)) {
                    // If tasks exists but isn't an array, fix it
                    console.warn('API returned tasks that is not an array:', data.tasks);
                    data.tasks = Array.isArray(data.tasks) ? data.tasks : [];
                }
                return data;
            }

            // Fallback if we received unexpected data
            console.warn('Received unexpected data format from tasks API:', data);
            return { error: 'Unexpected data format', tasks: [] };
        } catch (error) {
            console.error('Error fetching tasks:', error);
            return { error: error.message, tasks: [] };
        }
    }
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
                        handleSuccessfulLogin();                        // Close the auth tab after a shorter delay for better user experience
                        setTimeout(() => {
                            chrome.tabs.remove(tabId);
                        }, 1000); // Reduced from 2000ms to 1000ms
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
                        });                        // Close the auth tab
                        setTimeout(() => {
                            chrome.tabs.remove(tabId);
                        }, 1000); // Optimized to 1 second for better UX
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
        lastAuthTime: Date.now(), // Track authentication time for smart intervals
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
 * Notify all sidebars about user ID changes
 * @param {string} userId - The user ID to notify about
 */
async function notifySidebarsAboutUserId(userId) {
    console.log('Notifying all sidebars about user ID:', userId);

    // Method 1: Use runtime messaging (works for non-connected panels)
    try {
        chrome.runtime.sendMessage({
            type: 'user-id-update',
            payload: {
                userId: userId,
                timestamp: Date.now()
            }
        });
        console.log('Sent user ID update via runtime.sendMessage');
    } catch (err) {
        console.warn('Failed to send user ID via runtime.sendMessage:', err);
    }

    // Method 2: Use connected sidebars
    for (const connection of sidebarConnections) {
        try {
            connection.postMessage({
                type: 'user-id-update',
                payload: {
                    userId: userId,
                    timestamp: Date.now()
                }
            });
            console.log('Sent user ID update via sidebar connection');
        } catch (err) {
            console.warn('Failed to send user ID via sidebar connection:', err);
        }
    }
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
        }        // Ensure we have a valid user ID before making the request
        if (!tokenState.userId) {
            console.warn('Missing user ID when checking token status, generating temporary ID');
            // Generate a random user ID if none exists
            tokenState.userId = 'temp-' + crypto.randomUUID();
            await chrome.storage.local.set({ tokenState });
        }

        console.log(`Checking token status for user ID: ${tokenState.userId}`);

        // Create a promise that rejects after timeout to prevent long hanging requests
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error(`Token check timed out after ${timeoutMs}ms`)), timeoutMs);
        });        // Create the actual fetch promise with all required parameters
        const tokenStatusUrl = new URL(`${API_BASE_URL}/auth/oauth/v2/token/status`);

        // CRITICAL FIX: user_id is a required parameter for the multi-user endpoint
        // Ensure it's always included and properly encoded
        if (!tokenState.userId) {
            console.warn('Missing user ID when checking token status, generating temporary ID');
            tokenState.userId = 'temp-' + crypto.randomUUID();
            // Save immediately to ensure consistency throughout the app
            await chrome.storage.local.set({ tokenState });
            // Also notify sidebars about the new user ID
            notifySidebarsAboutUserId(tokenState.userId);
        }

        // Add user_id as a query parameter (required by the API)
        tokenStatusUrl.searchParams.append('user_id', tokenState.userId);
        console.log(`Token status request including user_id: ${tokenState.userId}`);

        // Add additional validation parameters if needed
        if (tokenState.tokenData && tokenState.tokenData.access_token) {
            // Only include access_token reference if we have one (not the full token for security)
            tokenStatusUrl.searchParams.append('has_token', 'true');
        }

        console.log(`Requesting token status from: ${tokenStatusUrl.toString()}`);
        const fetchPromise = fetch(tokenStatusUrl.toString(), {
            headers: {
                'Accept': 'application/json',
                'X-Client-Version': chrome.runtime.getManifest().version || '1.0.0',
                'X-Client-ID': tokenState.userId
            }
        });// Race the fetch against the timeout
        const response = await Promise.race([fetchPromise, timeoutPromise]);

        if (!response.ok) {
            console.error(`Token status check failed with status: ${response.status}`);
            let errorData = null;

            // Try to get more detailed error information
            try {
                errorData = await response.json();
                console.error('Error details:', errorData);
            } catch (e) {
                console.error('Could not parse error response:', e);
            }            // Handle specific error codes
            if (response.status === 422) {
                console.warn('Validation error when checking token status. The server might be expecting different parameters.');
                console.log('Request URL was:', tokenStatusUrl.toString());
                console.log('User ID value:', tokenState.userId);

                // Attempt to recreate a valid user ID and try again (only once)
                if (options.retryAfterValidationError !== true) {
                    console.log('Attempting to fix validation error by regenerating user ID and retrying...');
                    tokenState.userId = 'temp-' + crypto.randomUUID();
                    await chrome.storage.local.set({ tokenState });

                    // Recursive call with retry flag to prevent infinite loop
                    return checkOAuthToken({
                        ...options,
                        retryAfterValidationError: true,
                        forceCheck: true
                    });
                }

                // Return an error response if we've already tried to fix the validation issues
                return {
                    valid: false,
                    status: "unknown",
                    error: "validation_error",
                    message: errorData?.detail || "Validation error when checking token",
                    timestamp: new Date().toISOString()
                };
            }
            // In case of a 401/403 Unauthorized response, mark as not authenticated
            else if (response.status === 401 || response.status === 403) {
                console.log('Received unauthorized response, marking as not authenticated');
                tokenState.isAuthenticated = false;
                tokenState.userInfo = null; // Clear user info on auth failure
                await chrome.storage.local.set({ tokenState });
                await notifySidebarsAboutAuth(false);

                return {
                    valid: false,
                    status: "unauthorized",
                    error: "unauthorized",
                    message: "Authentication required",
                    timestamp: new Date().toISOString()
                };
            } else {
                // For other errors, we might not invalidate auth immediately,
                // but we won't have new token data.
                // However, if token is invalid, clear user info.
                tokenState.userInfo = null; // Clear user info on error
                await chrome.storage.local.set({ tokenState }); // Save updated state
                await notifySidebarsAboutAuth(tokenState.isAuthenticated, null); // Notify UI, keep current auth state if not 401/403

                return {
                    valid: false,
                    status: "error",
                    error: `http_${response.status}`,
                    message: `HTTP error: ${response.status} ${response.statusText}`,
                    timestamp: new Date().toISOString()
                };
            }
        } const data = await response.json();
        console.log('Token status (detailed from /token/status):', JSON.stringify(data, null, 2));

        // Explicit check for true/false to avoid truthy values
        const isActive = data && (
            data.status === "active" ||
            data.valid === true ||
            (data.expires_in_seconds && data.expires_in_seconds > 0) ||
            (data.expires_at && new Date(data.expires_at).getTime() > Date.now())
        );
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
 * Start periodic token checking with enhanced protection against multiple instances
 */
function startTokenChecking() {
    // Use a timestamp to track when the function was called
    const startTime = Date.now();

    // Store the last start time in a global variable to prevent rapid repeated calls
    // If another call happened within the last 10 seconds, ignore this one
    if (self.lastTokenCheckStart && (startTime - self.lastTokenCheckStart) < 10000) {
        console.log(`Ignoring repeated token check start request (${Math.round((startTime - self.lastTokenCheckStart) / 1000)}s since last attempt)`);
        return;
    }

    // Update the last start time
    self.lastTokenCheckStart = startTime;

    if (DEBUG_MODE) {
        console.log('Starting periodic token checking...');
        console.log('Current interval ID:', self.tokenCheckIntervalId);
    } else {
        console.log('Starting periodic token checking');
    }

    // Guard against multiple token checking services running
    if (self.tokenCheckIntervalId) {
        if (DEBUG_MODE) {
            console.log('Found existing token check interval (ID: ' + self.tokenCheckIntervalId + '), not starting a new one');
        } else {
            console.log('Token checking already active, not starting another instance');
        }

        // Add a protection: verify the interval is still valid by checking if it fires
        // This handles potential edge cases where the interval ID exists but the interval itself is broken
        try {
            clearTimeout(self.tokenCheckIntervalId);
            self.tokenCheckIntervalId = null;
            console.log('Cleared potentially stale interval, will create a new one');
        } catch (err) {
            console.warn('Error clearing existing interval:', err);
            return; // Exit early if we can't clear the interval
        }
    }    // Set new interval with smart timing based on recent authentication
    try {
        // Determine the interval based on how recently authentication occurred
        const now = Date.now();
        const timeSinceAuth = tokenState.lastAuthTime ? (now - tokenState.lastAuthTime) : Infinity;
        const shouldUseFastInterval = timeSinceAuth < FAST_CHECK_DURATION;
        const intervalToUse = shouldUseFastInterval ? FAST_TOKEN_CHECK_INTERVAL : TOKEN_CHECK_INTERVAL;

        if (DEBUG_MODE) {
            console.log(`Using ${shouldUseFastInterval ? 'fast' : 'normal'} token check interval: ${intervalToUse / 1000}s (auth was ${Math.round(timeSinceAuth / 1000)}s ago)`);
        }

        self.tokenCheckIntervalId = setInterval(async () => {
            if (DEBUG_MODE) {
                console.log(`Running periodic token check (interval ID: ${self.tokenCheckIntervalId})`);
            } else {
                console.log('Checking token status...');
            }

            try {
                const tokenStatus = await checkOAuthToken();

                if (tokenStatus && (tokenStatus.valid === true || tokenStatus.status === "active")) {
                    // Update token state - explicitly check for true to avoid truthy values
                    tokenState = {
                        ...tokenState,
                        isAuthenticated: true, // Explicitly set to true when token is valid
                        tokenData: tokenStatus,
                        lastChecked: new Date().toISOString()
                    };

                    // Save to storage
                    await chrome.storage.local.set({ tokenState });

                    // Notify any open sidebars
                    try {
                        chrome.runtime.sendMessage({
                            type: 'token-status',
                            payload: tokenStatus
                        });
                    } catch (msgErr) {
                        console.warn('Error sending token status message:', msgErr);
                    }

                    // Also ensure auth-status is consistent
                    await notifySidebarsAboutAuth(true, tokenState.userInfo);
                } else {
                    // Token is no longer valid
                    if (DEBUG_MODE) {
                        console.log('Token is no longer valid, tokenStatus:', tokenStatus);
                    } else {
                        console.log('Token is no longer valid');
                    }
                    tokenState.isAuthenticated = false; // Explicitly set to false
                    await chrome.storage.local.set({ tokenState });
                    await performLogout();
                }
            } catch (err) {
                console.error('Error in periodic token check:', err);
            }
        }, intervalToUse); // Use smart interval timing

        if (DEBUG_MODE) {
            console.log(`Token checking started with interval ID: ${self.tokenCheckIntervalId} (${intervalToUse / 1000}s interval)`);
        }

        // If using fast interval, set up a timer to switch to normal interval later
        if (shouldUseFastInterval) {
            const timeUntilSlowdown = FAST_CHECK_DURATION - timeSinceAuth;
            setTimeout(() => {
                if (DEBUG_MODE) {
                    console.log('Switching from fast to normal token checking interval');
                }
                stopTokenChecking();
                startTokenChecking(); // This will now use the normal interval
            }, timeUntilSlowdown);

            if (DEBUG_MODE) {
                console.log(`Will switch to normal interval in ${Math.round(timeUntilSlowdown / 1000)}s`);
            }
        }
    } catch (err) {
        console.error('Failed to start token checking interval:', err);
        // Make sure we clean up any existing interval ID to avoid leaking resources
        if (self.tokenCheckIntervalId) {
            try {
                clearInterval(self.tokenCheckIntervalId);
            } catch (clearErr) {
                console.warn('Error clearing interval during error handling:', clearErr);
            }
            self.tokenCheckIntervalId = null;
        }
    }
}

/**
 * Stop periodic token checking
 */
function stopTokenChecking() {
    if (DEBUG_MODE) {
        console.log('Stopping periodic token checking...');
        console.log('Previous interval ID:', self.tokenCheckIntervalId);
    } else {
        console.log('Stopping periodic token checking');
    }

    if (self.tokenCheckIntervalId) {
        clearInterval(self.tokenCheckIntervalId);
        self.tokenCheckIntervalId = null;

        if (DEBUG_MODE) {
            console.log('Token checking stopped successfully, interval cleared');
        }
    } else if (DEBUG_MODE) {
        console.log('No token check interval was running');
    }
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
