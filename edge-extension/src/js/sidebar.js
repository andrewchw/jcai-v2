/**
 * Sidebar.js - Handles UI interactions in the sidebar
 */

// DOM Elements
const elements = {
    // Tabs
    tabButtons: document.querySelectorAll('.tab-button'),
    tabContents: document.querySelectorAll('.tab-content'),

    // Chat
    messagesContainer: document.getElementById('messages-container'),
    userInput: document.getElementById('user-input'),
    sendButton: document.getElementById('send-button'),
    clearButton: document.getElementById('clear-button'),
    helpButton: document.getElementById('help-button'),// Tasks
    projectFilter: document.getElementById('project-filter'),
    statusFilter: document.getElementById('status-filter'),
    tasksList: document.getElementById('tasks-list'),
    tasksCountText: document.getElementById('tasks-count-text'),
    refreshTasksButton: document.getElementById('refresh-tasks'),
    createTaskButton: document.getElementById('create-task'),

    // Settings
    serverUrl: document.getElementById('server-url'),
    oauthStatus: document.getElementById('oauth-status'),
    loginButton: document.getElementById('login-button'),
    logoutButton: document.getElementById('logout-button'),
    enableNotifications: document.getElementById('enable-notifications'),
    notificationTime: document.getElementById('notification-time'),

    // Status indicators
    statusIndicator: document.getElementById('status-indicator'),
    statusText: document.getElementById('status-text'),
    tokenStatus: document.getElementById('token-status'),
    userDisplay: document.getElementById('user-display') // Added for username
};

// Connection to background script
let port;

// App state
const state = {
    serverUrl: 'http://localhost:8000',
    isAuthenticated: false,
    serverConnected: false,
    userId: null, // Add user ID to state for API requests
    projects: [],
    tasks: [],
    lastTokenCheck: 0, // Track last token check time to prevent rapid requests
    lastProjectsCheck: 0, // Track last projects check time
    lastTasksCheck: 0, // Track last tasks check time
    lastAuthTime: 0 // Track when authentication last completed for smart debouncing
};

/**
 * Initialize the sidebar
 */
function initialize() {
    console.log('Initializing sidebar');    // Load settings before connecting to background script
    loadSettings().then(() => {
        // Check if we have a saved user ID in storage
        chrome.storage.local.get(['savedUserId', 'tokenState', 'lastAuthStatus'], (result) => {
            let shouldUpdateAuthOnStartup = false;

            // Restore saved user ID if available
            if (result.savedUserId) {
                state.userId = result.savedUserId;
                console.log('Restored user ID from storage:', state.userId);
            }

            try {
                if (result && result.tokenState) {
                    if (result.tokenState.isAuthenticated === true) { // Explicitly check for true
                        console.log('Found authenticated state in storage');

                        // Check if the token is still valid before assuming we're authenticated
                        const tokenData = result.tokenState.tokenData;
                        if (tokenData) {
                            const isValid = tokenData.valid === true ||
                                tokenData.status === 'active' ||
                                (typeof tokenData.expires_in_seconds === 'number' && tokenData.expires_in_seconds > 0);

                            if (isValid) {
                                console.log('Token appears to be valid, setting authenticated state');
                                // Use a properly formatted payload
                                handleAuthStatusUpdate({
                                    isAuthenticated: true,
                                    source: 'storage-init',
                                    timestamp: Date.now()
                                });
                                handleTokenStatusUpdate(tokenData);
                                shouldUpdateAuthOnStartup = true;
                            } else {
                                console.warn('Found authenticated state but token appears invalid, will request fresh status');
                                // Don't set authenticated state yet - we'll let background.js verify it
                                state.isAuthenticated = false;
                            }
                        } else {
                            console.warn('Found authenticated state but no token data, will request fresh status');
                            // Don't assume authenticated without token data
                            state.isAuthenticated = false;
                        }
                    } else {
                        console.log('Found unauthenticated state in storage');
                        state.isAuthenticated = false;
                    }
                } else {
                    console.log('No token state found in storage');
                    state.isAuthenticated = false;
                }
            } catch (error) {
                console.error('Error processing token state:', error);
                state.isAuthenticated = false;
            }
            if (result.lastAuthStatus && result.lastAuthStatus.isAuthenticated) {
                console.log('Found auth status backup in storage:', result.lastAuthStatus);
                // Only trust this as fallback if it's recent (within last hour)
                const timeSinceUpdate = Date.now() - (result.lastAuthStatus.timestamp || 0);
                if (timeSinceUpdate < 3600000) { // 1 hour
                    handleAuthStatusUpdate({ isAuthenticated: result.lastAuthStatus.isAuthenticated });
                    shouldUpdateAuthOnStartup = true;
                } else {
                    console.warn('Auth status backup is too old, requesting fresh status');
                    state.isAuthenticated = false;
                }
            }

            // Connect to background script after checking storage
            connectToBackground();
        });
    });

    // Display initial connection status
    updateConnectionStatus(false, 'Initializing...');
}

/**
 * Connect to the background script
 */
function connectToBackground() {
    // Connect to background script
    try {
        // First disconnect any existing port
        if (port) {
            try {
                port.disconnect();
            } catch (e) {
                console.log('Error disconnecting existing port:', e);
            }
        } port = chrome.runtime.connect({ name: 'sidebar' });
        console.log('Connected to background script'); setupPortListeners();

        // Always set up event listeners to ensure they work after extension reload
        setupEventListeners();

        // Check connectivity to server
        checkServerConnectivity();
    } catch (error) {
        console.error('Failed to connect to background script:', error);
        updateConnectionStatus(false, 'Background connection failed');

        // Retry connection after delay
        setTimeout(connectToBackground, 2000);
    }
}

/**
 * Set up listeners for port communication
 */
function setupPortListeners() {
    port.onMessage.addListener((message) => {
        console.log('Received message from background:', message);

        // Enhanced message validation
        if (!message) {
            console.error('Received null or undefined message from background');
            return;
        }

        if (typeof message !== 'object') {
            console.error('Received non-object message from background:', message);
            return;
        }

        if (typeof message.type !== 'string') {
            console.error('Received message without string type from background:', message);
            return;
        } try {
            switch (message.type) {
                case 'auth-status':
                    // Add extra safeguard for auth status messages
                    if (message.payload !== undefined) {
                        handleAuthStatusUpdate(message.payload);
                    } else {
                        console.error('Auth status message received with undefined payload');
                    }
                    break; case 'token-status':
                    handleTokenStatusUpdate(message.payload);
                    break;

                case 'jira-projects':
                    handleProjectsUpdate(message.payload);
                    break;

                case 'jira-tasks':
                    handleTasksUpdate(message.payload);
                    break;

                case 'user-id-update':
                    handleUserIdUpdate(message.payload);
                    break;

                case 'error': // Add a specific case for 'error' type messages
                    console.error('Received error message from background:', message.payload);
                    // Optionally, display a generic error to the user in the UI
                    // elements.statusText.textContent = 'An error occurred. Check console.';
                    break;
                default:
                    console.warn('Unhandled message type:', message.type, 'Full message:', message);
            }
        } catch (error) { // This is line 149 from the stack trace
            console.error('Error handling sidebar message (type:', message.type, '):', error, 'Full message:', message);
        }
    });

    // Handle port disconnection
    port.onDisconnect.addListener(() => {
        console.log('Disconnected from background script, attempting to reconnect...');

        // Attempt to reconnect
        setTimeout(() => {
            try {
                port = chrome.runtime.connect({ name: 'sidebar' });
                setupPortListeners();
                console.log('Reconnected to background script');                // Check token status after reconnection (with smart debounce)
                // We'll use a shorter debounce if we recently authenticated
                const now = Date.now();
                const lastCheck = state.lastTokenCheck || 0;
                const timeSinceAuth = now - (state.lastAuthTime || 0);
                const reconnectDebounceTime = timeSinceAuth < 30000 ? 2000 : 8000; // 2s if recent auth, 8s otherwise

                if (now - lastCheck > reconnectDebounceTime) {
                    state.lastTokenCheck = now;
                    console.log(`Checking token status after reconnection (using ${reconnectDebounceTime / 1000}s debounce)`);
                    port.postMessage({ type: 'check-token' });
                } else {
                    console.log('Skipping reconnection token check - checked recently (' + Math.round((now - lastCheck) / 1000) + ' seconds ago)');
                }
            } catch (error) {
                console.error('Failed to reconnect to background script:', error);
                updateConnectionStatus(false, 'Background connection failed');
            }
        }, 1000);
    });
}

/**
 * Set up UI event listeners
 */
function setupEventListeners() {
    // Tab switching
    elements.tabButtons.forEach(button => {
        button.addEventListener('click', () => switchTab(button.id.replace('tab-', '')));
    });    // Chat input
    elements.userInput.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            await sendMessage();
        }
    }); elements.sendButton.addEventListener('click', async () => {
        await sendMessage();
    });
    elements.clearButton.addEventListener('click', clearChat);
    elements.helpButton.addEventListener('click', showHelpMessage);// Filter changes
    elements.projectFilter.addEventListener('change', loadTasks);
    elements.statusFilter.addEventListener('change', loadTasks);

    // Task actions
    elements.refreshTasksButton.addEventListener('click', () => {
        // Force refresh by clearing the debounce timer
        state.lastTasksCheck = 0;
        loadTasks();
    }); elements.createTaskButton.addEventListener('click', () => {
        // Open JIRA create issue dialog using actual JIRA domain
        const jiraDomain = 'https://3hk.atlassian.net';
        const createUrl = `${jiraDomain}/secure/CreateIssue.jspa?pid=10000&issuetype=10001`;
        window.open(createUrl, '_blank');
    });

    // Login/Logout
    elements.loginButton.addEventListener('click', initiateLogin);
    elements.logoutButton.addEventListener('click', initiateLogout);

    // Settings changes
    elements.serverUrl.addEventListener('change', saveSettings);
    elements.enableNotifications.addEventListener('change', saveSettings);
    elements.notificationTime.addEventListener('change', saveSettings);
}

/**
 * Load saved settings
 */
async function loadSettings() {
    const settings = await chrome.storage.local.get(['serverUrl', 'enableNotifications', 'notificationTime']);

    if (settings.serverUrl) {
        state.serverUrl = settings.serverUrl;
        elements.serverUrl.value = settings.serverUrl;
    }

    if (settings.enableNotifications !== undefined) {
        elements.enableNotifications.checked = settings.enableNotifications;
    }

    if (settings.notificationTime) {
        elements.notificationTime.value = settings.notificationTime;
    }
}

/**
 * Save settings to storage
 */
async function saveSettings() {
    state.serverUrl = elements.serverUrl.value;

    await chrome.storage.local.set({
        serverUrl: elements.serverUrl.value,
        enableNotifications: elements.enableNotifications.checked,
        notificationTime: elements.notificationTime.value
    });

    // Update connection if server URL changed
    checkServerConnectivity();
}

/**
 * Check connectivity to the server
 */
async function checkServerConnectivity() {
    try {
        updateConnectionStatus(false, 'Connecting...');

        const response = await fetch(`${state.serverUrl}/api/health`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            cache: 'no-cache'
        });

        if (!response.ok) throw new Error('Server error');

        const data = await response.json();
        console.log('Server health check:', data);

        // Update connection status
        updateConnectionStatus(true, 'Connected');

        // Update auth status if we got it from health check
        if (data.authenticated) {
            console.log('Server reports authenticated session, updating UI');
            handleAuthStatusUpdate({ isAuthenticated: true });
        }        // Double check authentication status through background (with debounce)
        setTimeout(() => {
            const now = Date.now();
            const lastCheck = state.lastTokenCheck || 0;
            if (now - lastCheck > 5000) { // 5 seconds debounce
                state.lastTokenCheck = now;
                port.postMessage({ type: 'check-token' });
            } else {
                console.log('Skipping health check token verification - checked recently');
            }
        }, 500);

    } catch (error) {
        console.error('Server connectivity error:', error);
        updateConnectionStatus(false, 'Connection failed');
    }
}

/**
 * Update connection status UI
 */
function updateConnectionStatus(connected, message) {
    state.serverConnected = connected;

    elements.statusIndicator.className = 'status-indicator ' +
        (connected ? 'connected' : 'disconnected');

    elements.statusText.textContent = message;
}

/**
 * Handle authentication status update
 */
function handleAuthStatusUpdate(payload) {
    console.log('Auth status update received:', payload);

    // More robust payload validation
    if (!payload) {
        console.error('Empty auth status payload received');
        return;
    }

    // Initialize all variables at the beginning to prevent reference errors
    let isAuth = false;
    let timestamp = Date.now();
    let source = 'unknown';
    let userInfo = null;
    let reason = 'N/A';
    // Track if authentication state actually changed
    let authStateChanged = false;

    try {
        // Extract additional metadata if available
        if (typeof payload === 'object') {
            timestamp = payload.timestamp || timestamp;
            source = payload.source || source;
            userInfo = payload.userInfo || null;
            reason = payload.reason || 'N/A';
        }

        // Ensure we have a valid boolean for isAuthenticated
        if (typeof payload === 'object' && 'isAuthenticated' in payload) {
            isAuth = payload.isAuthenticated === true;
        } else if (typeof payload === 'boolean') {
            isAuth = payload === true;
        } else if (typeof payload === 'string') {
            isAuth = payload === 'true' || payload === 'authenticated';
        } else {
            console.error('Invalid auth status payload format:', typeof payload, payload);
            return;
        }
        console.log(`Processed auth status: ${isAuth} (from: ${source}, at: ${new Date(timestamp).toISOString()}, reason: ${reason})`);    // Check if auth state actually changed
        authStateChanged = state.isAuthenticated !== isAuth;
        if (authStateChanged) {
            console.log(`Auth state changed from ${state.isAuthenticated} to ${isAuth}`);
            // Track authentication time for smart debouncing
            if (isAuth) {
                state.lastAuthTime = timestamp;
                console.log('Set lastAuthTime for smart debouncing');
            }
        } else {
            console.log(`Auth state unchanged: ${isAuth}`);
        }
    } catch (err) {
        console.error('Error processing auth payload:', err);
        return;
    }

    // Update state with safely processed value
    state.isAuthenticated = isAuth;    // Update UI immediately for responsive feel
    elements.oauthStatus.innerHTML = state.isAuthenticated ?
        '<span style=\"color: var(--success-color);\">Authenticated ✓</span>' :
        '<span style=\"color: var(--error-color);\">Not authenticated</span>';

    // Update button visibility immediately
    elements.loginButton.style.display = state.isAuthenticated ? 'none' : 'block';
    elements.logoutButton.style.display = state.isAuthenticated ? 'block' : 'none';
    elements.loginButton.disabled = state.isAuthenticated;
    elements.logoutButton.disabled = !state.isAuthenticated;

    // Save the last auth status for potential recovery on restart
    chrome.storage.local.set({
        lastAuthStatus: {
            isAuthenticated: state.isAuthenticated,
            timestamp: timestamp,
            source: source
        }
    });

    // Update button visibility
    elements.loginButton.style.display = state.isAuthenticated ? 'none' : 'block';
    elements.logoutButton.style.display = state.isAuthenticated ? 'block' : 'none';
    elements.loginButton.disabled = state.isAuthenticated;
    elements.logoutButton.disabled = !state.isAuthenticated;

    if (state.isAuthenticated) {
        // User info might come from 'auth-status' or 'token-status' (via background.js)
        // Let's ensure userDisplay is updated if userInfo is present in this payload
        if (userInfo && userInfo.displayName) {
            elements.userDisplay.textContent = `Logged in as: ${userInfo.displayName}`;
        } else {
            // If displayName is not in this specific payload,
            // it might arrive with 'token-status' or already be set.
            // Avoid clearing it unnecessarily unless explicitly logging out.
            // elements.userDisplay.textContent = elements.userDisplay.textContent || 'Authenticated'; // Keep existing or set generic
        }
    } else {
        elements.userDisplay.textContent = ''; // Clear username on logout or auth failure
        elements.tokenStatus.textContent = 'N/A'; // Clear token status as well
    }

    console.log('Auth UI updated - isAuthenticated:', state.isAuthenticated, 'Reason:', reason);

    // Save the auth state to local storage as fallback
    chrome.storage.local.set({
        lastUIAuthState: {
            isAuthenticated: state.isAuthenticated,
            timestamp: Date.now(),
            reason: reason,
            source: source
        }
    });

    // Only request data if auth state actually changed to true OR
    // this is an initial auth status update (indicated by source)
    const isInitialUpdate = source === 'initial-connection' || source === 'storage-init';

    if ((authStateChanged && state.isAuthenticated) || (isInitialUpdate && state.isAuthenticated)) {
        console.log(`Requesting data because auth ${authStateChanged ? 'state changed' : 'is initial update'}`);

        // Ensure we have a valid port connection before proceeding
        if (!port || !port.postMessage) {
            console.warn('Port not connected or invalid - attempting to reconnect first');
            try {
                // Try to reconnect first
                connectToBackground();

                // Give it a moment to establish the connection
                setTimeout(() => {
                    if (port && port.postMessage) {
                        console.log('Successfully reconnected port, proceeding with data requests');
                        requestAuthenticatedData();
                    } else {
                        console.error('Failed to reconnect port after attempt');
                    }
                }, 500);
            } catch (e) {
                console.error('Error attempting to reconnect:', e);
            }
        } else {
            // Port is valid, proceed directly
            requestAuthenticatedData();
        }
    } else if (!state.isAuthenticated) {
        // If not authenticated, clear projects and tasks
        handleProjectsUpdate([]); // Clear projects dropdown
        handleTasksUpdate([]);    // Clear tasks list
    } else {
        console.log('Skipping data requests - auth state unchanged or already handled');
    }
}

// Helper function to encapsulate authenticated data requests
function requestAuthenticatedData() {
    if (!port || !port.postMessage) {
        console.error('Port still invalid in requestAuthenticatedData');
        return;
    }

    const now = Date.now();

    // Smart debouncing for token checks - shorter for recent auth events
    const lastTokenCheck = state.lastTokenCheck || 0;
    const tokenCheckElapsed = now - lastTokenCheck;

    // Use shorter debounce if we recently completed authentication
    const recentAuthTime = state.lastAuthTime || 0;
    const timeSinceAuth = now - recentAuthTime;
    const debounceTime = timeSinceAuth < 30000 ? 2000 : 8000; // 2s if recent auth, 8s otherwise

    if (tokenCheckElapsed > debounceTime) {
        console.log(`Checking token status (${Math.round(tokenCheckElapsed / 1000)}s since last check, using ${debounceTime / 1000}s debounce)`);
        state.lastTokenCheck = now;
        port.postMessage({ type: 'check-token' });
    } else {
        console.log(`Skipping token check - last check was ${Math.round(tokenCheckElapsed / 1000)}s ago (${debounceTime / 1000}s debounce)`);
    }

    // Smart debouncing for projects - shorter for recent auth events
    const lastProjectsCheck = state.lastProjectsCheck || 0;
    const projectsCheckElapsed = now - lastProjectsCheck;
    const projectsDebounceTime = timeSinceAuth < 30000 ? 1000 : 4000; // 1s if recent auth, 4s otherwise

    if (projectsCheckElapsed > projectsDebounceTime) {
        console.log(`Fetching projects (${Math.round(projectsCheckElapsed / 1000)}s since last check, using ${projectsDebounceTime / 1000}s debounce)`);
        state.lastProjectsCheck = now;
        port.postMessage({ type: 'get-jira-projects' });
    } else {
        console.log(`Skipping projects check - last check was ${Math.round(projectsCheckElapsed / 1000)}s ago (${projectsDebounceTime / 1000}s debounce)`);
    }
}

/**
 * Handle token status update
 */
function handleTokenStatusUpdate(tokenData) {
    console.log('Token status update received:', tokenData);

    if (!tokenData) {
        console.warn('Empty token data received in handleTokenStatusUpdate');
        elements.tokenStatus.textContent = 'No token data';
        elements.userDisplay.textContent = ''; // Clear username
        // It's possible that an empty tokenData here should also trigger an auth state correction
        if (state.isAuthenticated) {
            console.warn('Token data is empty, but UI shows authenticated. Correcting UI state.');
            handleAuthStatusUpdate({ isAuthenticated: false, reason: "Empty token data" });
        }
        return;
    }

    // More robust check for token validity that handles different token data formats
    const isValid = (
        // Check explicit validity flag
        tokenData.valid === true ||
        // Check known status values
        tokenData.status === 'active' ||
        // Check expiration time
        (typeof tokenData.expires_in_seconds === 'number' && tokenData.expires_in_seconds > 0) ||
        // Check expires_at timestamp if available
        (tokenData.expires_at && new Date(tokenData.expires_at).getTime() > Date.now())
    );

    // Update authentication state if token is invalid but UI shows authenticated
    if (!isValid && state.isAuthenticated) {
        console.warn('Token is invalid but UI shows authenticated - correcting UI state. TokenData:', tokenData);
        handleAuthStatusUpdate({ isAuthenticated: false, reason: "Token invalid" });
    }    // Update token status in footer based on validity
    if (isValid) {
        // Calculate expiration time - try various token data formats
        let expiresIn = 0;
        let expiresAtDate = null;

        if (typeof tokenData.expires_in_seconds === 'number') {
            expiresIn = tokenData.expires_in_seconds;
        } else if (tokenData.expires_at) {
            // Calculate from expires_at timestamp
            const expiresAtTime = new Date(tokenData.expires_at).getTime();
            if (!isNaN(expiresAtTime)) {
                expiresIn = Math.floor((expiresAtTime - Date.now()) / 1000);
                expiresAtDate = new Date(expiresAtTime);
            }
        } else if (tokenData.expiresAt) {
            // Alternative property name
            const expiresAtTime = new Date(tokenData.expiresAt).getTime();
            if (!isNaN(expiresAtTime)) {
                expiresIn = Math.floor((expiresAtTime - Date.now()) / 1000);
                expiresAtDate = new Date(expiresAtTime);
            }
        } else if (tokenData.expires_in) {
            // OAuth standard property
            expiresIn = parseInt(tokenData.expires_in);
        } else {
            // Default fallback
            expiresIn = 3600;
        }

        if (expiresIn <= 0) {
            elements.tokenStatus.innerHTML = '<span style="color: var(--error-color);">Token expired</span>';
            console.warn('Token appears to be expired');

            // Token is expired, update authentication state
            if (state.isAuthenticated) {
                handleAuthStatusUpdate({ isAuthenticated: false, reason: "Token expired" });
            }
            return;
        }

        // Format expiration time
        let expirationText;
        if (expiresIn > 3600) {
            expirationText = `${Math.floor(expiresIn / 3600)} hours`;
        } else if (expiresIn > 60) {
            expirationText = `${Math.floor(expiresIn / 60)} minutes`;
        } else {
            expirationText = `${expiresIn} seconds`;
        }

        elements.tokenStatus.innerHTML = `<span style="color: var(--success-color);">Valid (expires in ${expirationText})</span>`;

        // If we have user info in the token data, update the display
        if (tokenData.user && tokenData.user.displayName) {
            // Update user display with name from token data
            elements.userDisplay.textContent = `Logged in as: ${tokenData.user.displayName}`;
        }

        // If we have userId in the token data, make sure it's saved
        if (tokenData.user_id) {
            console.log(`Token contains user ID: ${tokenData.user_id}`);
            // Send this back to background.js for consistency
            if (port && port.postMessage) {
                port.postMessage({
                    type: 'update-user-id',
                    payload: { userId: tokenData.user_id }
                });
            }
        }
    } else {
        // Token is invalid
        elements.tokenStatus.innerHTML = '<span style="color: var(--error-color);">Invalid token</span>';
    }
}

/**
 * Handle projects data update
 */
function handleProjectsUpdate(data) {
    console.log('Projects update received:', typeof data, data);

    // Handle cases where data might be an object with error and projects properties
    let projectsArray = [];

    // Handle different data formats
    if (Array.isArray(data)) {
        // Direct array of projects
        console.log('Projects data is a direct array of length:', data.length);
        projectsArray = data;
    } else if (data && data.projects && Array.isArray(data.projects)) {
        // Object with projects array property
        console.log('Projects data has projects array of length:', data.projects.length);
        projectsArray = data.projects;
    } else if (data && data.error) {
        // Error case - log and show empty projects
        console.warn('Error loading projects:', data.error);
        projectsArray = [];
    } else if (data == null || data === undefined) {
        // Null/undefined case - use empty array
        console.warn('Received null or undefined projects data');
        projectsArray = [];
    } else {
        // Unknown format - try to handle gracefully
        console.error('Received projects data in unknown format:', typeof data, data);
        try {
            // Attempt to extract any array-like data
            if (typeof data === 'object') {
                // Try to find any array property that might contain projects
                const possibleArrays = Object.values(data).filter(val => Array.isArray(val));
                if (possibleArrays.length > 0) {
                    // Use the first array found
                    projectsArray = possibleArrays[0];
                    console.log('Found potential projects array with length:', projectsArray.length);
                } else {
                    projectsArray = [];
                }
            } else {
                projectsArray = [];
            }
        } catch (e) {
            console.error('Failed to process projects data:', e);
            projectsArray = [];
        }
    }// Update state with processed array
    console.log('Setting projects state with array of length:', projectsArray ? projectsArray.length : 0);
    state.projects = projectsArray;

    // Update project filter
    elements.projectFilter.innerHTML = '<option value="all">All Projects</option>';

    // Only try to iterate if we have an array
    if (Array.isArray(projectsArray)) {
        console.log('Populating project filter with', projectsArray.length, 'projects');
        projectsArray.forEach(project => {
            // Defensive check that project is an object with needed properties
            if (project && project.key && project.name) {
                const option = document.createElement('option');
                option.value = project.key;
                option.textContent = project.name;
                elements.projectFilter.appendChild(option);
            } else {
                console.warn('Skipping invalid project item:', project);
            }
        });
    }

    // Load tasks with current filters
    loadTasks();
}

/**
 * Load tasks based on current filters
 */
function loadTasks() {
    if (!state.isAuthenticated) return;

    // Enhanced debounce to prevent multiple rapid requests
    const now = Date.now();
    const lastTasksCheck = state.lastTasksCheck || 0;
    const tasksCheckElapsed = now - lastTasksCheck;

    if (tasksCheckElapsed < 3000) { // 3 seconds debounce (increased from 2)
        console.log(`Skipping tasks request - last check was ${Math.round(tasksCheckElapsed / 1000)}s ago`);
        return;
    }

    // Validate port connection before proceeding
    if (!port || !port.postMessage) {
        console.error('Port disconnected - cannot load tasks');
        updateConnectionStatus(false, 'Connection lost');
        // Try to reconnect
        connectToBackground();
        return;
    }

    // Update last check time
    state.lastTasksCheck = now;

    // Show loading
    elements.tasksList.innerHTML = '<div class="loading-indicator">Loading tasks...</div>';

    // Get filter values
    const filters = {
        project: elements.projectFilter.value !== 'all' ? elements.projectFilter.value : null,
        status: elements.statusFilter.value !== 'all' ? elements.statusFilter.value : null,
        userId: state.userId, // Include user ID in all task requests
        maxResults: 50, // Limit the number of results to prevent unbounded queries
    };    // Always add a specific JQL query to prevent "Unbounded JQL" errors
    // Focus on issues assigned to the current user in the JCAI project by default
    let jqlBase = 'project = JCAI AND assignee = currentUser()';

    // Add project filter if specified (override default JCAI project)
    if (filters.project) {
        jqlBase = `project = ${filters.project} AND assignee = currentUser()`;
    }

    // Add status filter if specified
    if (filters.status) {
        jqlBase += ` AND status = "${filters.status}"`;
    }

    // Add date restriction to keep results recent and performant
    jqlBase += ' AND updated >= -30d';

    // Always add ordering for consistent results
    filters.jql = jqlBase + ' ORDER BY updated DESC';

    // Log the request for debugging
    console.log('Requesting tasks with filters:', JSON.stringify(filters));

    // Request tasks from background
    port.postMessage({
        type: 'get-jira-tasks',
        payload: filters
    });
}

/**
 * Handle tasks data update
 */
function handleTasksUpdate(data) {
    // Process the tasks data in a way similar to projects
    let tasksArray = [];

    console.log('Tasks update received:', typeof data, data);

    // Handle different data formats
    if (Array.isArray(data)) {
        // Direct array of tasks
        console.log('Tasks data is a direct array of length:', data.length);
        tasksArray = data;
    } else if (data && data.tasks && Array.isArray(data.tasks)) {
        // Object with tasks array
        console.log('Tasks data has tasks array of length:', data.tasks.length);
        tasksArray = data.tasks;
    } else if (data && data.error) {
        // Error case - log and show empty tasks
        console.warn('Error loading tasks:', data.error);
        tasksArray = [];
    } else if (data == null || data === undefined) {
        // Null/undefined case
        console.warn('Received null or undefined tasks data');
        tasksArray = [];
    } else {
        // Unknown format - try to handle gracefully
        console.error('Received tasks data in unexpected format:', typeof data, data);
        try {
            // Try to extract array data from any object
            if (typeof data === 'object') {
                // Look for any array property that might contain tasks
                const possibleArrays = Object.values(data).filter(val => Array.isArray(val));
                if (possibleArrays.length > 0) {
                    // Use the first array found
                    tasksArray = possibleArrays[0];
                    console.log('Found potential tasks array with length:', tasksArray.length);
                } else {
                    tasksArray = [];
                }
            } else {
                tasksArray = [];
            }
        } catch (e) {
            console.error('Failed to extract tasks data:', e);
            tasksArray = [];
        }
    }    // Update state
    console.log('Setting tasks state with array of length:', tasksArray ? tasksArray.length : 0);
    state.tasks = tasksArray;

    // Update task count
    const taskCount = tasksArray ? tasksArray.length : 0;
    if (elements.tasksCountText) {
        if (taskCount === 0) {
            elements.tasksCountText.textContent = 'No tasks found';
        } else if (taskCount === 1) {
            elements.tasksCountText.textContent = '1 task';
        } else {
            elements.tasksCountText.textContent = `${taskCount} tasks`;
        }
    }

    // Update tasks list
    elements.tasksList.innerHTML = '';

    if (!tasksArray || tasksArray.length === 0) {
        console.log('No tasks to display, showing empty state');
        elements.tasksList.innerHTML = `
            <div class="empty-state">
                <div style="font-size: 48px; margin-bottom: 16px;">📋</div>
                <div style="font-size: 16px; margin-bottom: 8px;">No tasks found</div>
                <div style="font-size: 14px; color: #6B778C;">Try adjusting your filters or create a new task</div>
            </div>
        `;
        return;
    }

    console.log('Rendering', tasksArray.length, 'tasks in the UI');

    // Create task elements
    tasksArray.forEach(task => {
        if (!task) {
            console.warn('Skipping null or undefined task in array');
            return; // Skip null or undefined tasks
        }

        // Check if the task has the required properties
        if (!task.key) {
            console.warn('Task missing key property:', task);
            return; // Skip this task
        } const taskElement = document.createElement('div');
        taskElement.className = 'task-item';        // Create clickable task key that opens JIRA issue
        const taskKey = task.key;

        // Extract JIRA domain from task.self URL if available, otherwise use default
        let jiraDomain = 'https://3hk.atlassian.net'; // Default domain
        if (task.self) {
            try {
                const selfUrl = new URL(task.self);
                jiraDomain = `${selfUrl.protocol}//${selfUrl.hostname}`;
            } catch (e) {
                // Use default if URL parsing fails
                console.warn('Could not parse task.self URL, using default JIRA domain');
            }
        }

        const jiraUrl = task.self ? task.self.replace('/rest/api/2/issue/', '/browse/') :
            `${jiraDomain}/browse/${taskKey}`;

        // Determine status class for styling
        const statusLower = (task.status || 'backlog').toLowerCase();
        let statusClass = 'backlog';
        if (statusLower.includes('progress') || statusLower.includes('doing')) {
            statusClass = 'in-progress';
        } else if (statusLower.includes('done') || statusLower.includes('complete')) {
            statusClass = 'done';
        } else if (statusLower.includes('todo') || statusLower.includes('open')) {
            statusClass = 'todo';
        }

        // Create priority indicator
        const priority = task.priority || 'Medium';
        const priorityClass = priority.toLowerCase().includes('high') ? 'high' :
            priority.toLowerCase().includes('low') ? 'low' : 'medium';

        taskElement.innerHTML = `
            <div class="task-header">
                <a href="${jiraUrl}" target="_blank" class="task-key" title="Open ${taskKey} in JIRA">${taskKey}</a>
                <span class="task-status ${statusClass}">${task.status || 'Backlog'}</span>
            </div>
            <div class="task-summary" title="${task.summary || 'No summary'}">${task.summary || 'No summary'}</div>
            <div class="task-meta">
                ${task.priority ? `<span class="task-priority ${priorityClass}">🔥 ${task.priority}</span>` : ''}
                ${task.dueDate ? `<span>📅 Due: ${formatDate(task.dueDate)}</span>` : ''}
                ${task.updated ? `<span>🔄 Updated: ${formatDate(task.updated)}</span>` : ''}
            </div>
        `;

        // Add click handler for the entire task item
        taskElement.addEventListener('click', (e) => {
            // Don't trigger if clicking on the task key link
            if (e.target.classList.contains('task-key')) return;

            // Open JIRA issue in new tab
            window.open(jiraUrl, '_blank');
        }); elements.tasksList.appendChild(taskElement);
    });
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    if (!dateString) return '';

    try {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        // If within 7 days, show relative time
        if (diffDays <= 7) {
            if (diffDays === 0) return 'Today';
            if (diffDays === 1) return date < now ? 'Yesterday' : 'Tomorrow';
            return `${diffDays} days ${date < now ? 'ago' : 'from now'}`;
        }

        // Otherwise show formatted date
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
        });
    } catch (e) {
        return dateString;
    }
}

/**
 * Switch between tabs
 */
function switchTab(tabName) {
    // Update active tab button
    elements.tabButtons.forEach(button => {
        button.classList.toggle('active', button.id === `tab-${tabName}`);
    });

    // Show active tab content
    elements.tabContents.forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}-container`);
    });

    // Perform tab-specific actions
    if (tabName === 'tasks' && state.isAuthenticated) {
        loadTasks();
    }
}

/**
 * Send a chat message
 */
async function sendMessage() {
    const message = elements.userInput.value.trim();
    if (!message) return;

    // Add message to chat
    addMessage(message, 'user');

    // Clear input
    elements.userInput.value = '';

    // Check if authenticated first
    if (!state.isAuthenticated || !state.userId) {
        addMessage('Please log in to JIRA first to use the chatbot features.', 'system');
        return;
    }

    // Add typing indicator
    const typingIndicator = addMessage('Thinking...', 'system');

    try {
        // Send message to the new chat API
        const response = await fetch(`${state.serverUrl}/api/chat/message/${encodeURIComponent(state.userId)}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: message
            })
        });

        // Remove typing indicator
        elements.messagesContainer.removeChild(typingIndicator);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Chat API error: ${response.status} - ${errorText}`);
        }

        const chatResponse = await response.json();

        // Add the bot's response
        addMessage(chatResponse.text, 'bot');

        // If there was a Jira action result, show additional feedback
        if (chatResponse.jira_action_result) {
            const actionResult = chatResponse.jira_action_result;
            if (actionResult.success) {
                addMessage(`✅ Action completed successfully: ${actionResult.message}`, 'system');

                // If an issue was created or modified, refresh tasks
                if (actionResult.issue_key || chatResponse.intent === 'create_issue') {
                    // Refresh the tasks list to show new/updated issues
                    setTimeout(() => {
                        state.lastTasksCheck = 0; // Force refresh
                        loadTasks();
                    }, 1000);
                }
            } else {
                addMessage(`❌ Action failed: ${actionResult.message || 'Unknown error'}`, 'system');
            }
        }

        // If the response requires clarification, give user some context
        if (chatResponse.requires_clarification) {
            const missingInfo = chatResponse.context?.missing_entities?.join(', ') || 'additional information';
            addMessage(`💡 Tip: I need ${missingInfo} to complete this action.`, 'system');
        }

    } catch (error) {
        console.error('Error sending chat message:', error);

        // Remove typing indicator if still present
        if (typingIndicator && typingIndicator.parentNode) {
            elements.messagesContainer.removeChild(typingIndicator);
        }

        // Show error to user
        addMessage(`Sorry, I encountered an error: ${error.message}. Please try again.`, 'system');
    }
}

/**
 * Add a message to the chat
 */
function addMessage(content, type) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${type}-message`;
    messageElement.innerHTML = `
        <div class="message-content">${content}</div>
    `;

    elements.messagesContainer.appendChild(messageElement);

    // Scroll to bottom
    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;

    return messageElement;
}

/**
 * Clear the chat
 */
function clearChat() {
    elements.messagesContainer.innerHTML = `
        <div class="message system-message">
            <div class="message-content">
                Welcome to JIRA Chatbot Assistant. How can I help you today?
            </div>
        </div>
    `;
}

/**
 * Initiate login process
 */
function initiateLogin() {
    port.postMessage({ type: 'login' });
}

/**
 * Initiate logout process
 */
function initiateLogout() {
    port.postMessage({ type: 'logout' });
}

/**
 * Show help message with command examples
 */
function showHelpMessage() {
    const helpMessage = `
        <div class="message-content">
            <strong>📋 Command Examples:</strong><br><br>

            <strong>Create Issues:</strong><br>
            • Summary: "Fix login bug", Assignee: "John Doe", Due Date: "Friday" for Create Issue<br>
            • Create task with summary="Update docs" assignee="Alice"<br>
            • New issue: "Database optimization", due_date="next week"<br><br>

            <strong>Due Date Options:</strong><br>
            • "today", "tomorrow", "Friday", "next week", "2025-06-01"<br><br>

            <strong>Other Commands:</strong><br>
            • "Show my open tasks"<br>
            • "List issues assigned to me"<br>
            • "Update PROJ-123 priority to high"<br>
            • "Assign PROJ-456 to Alice"<br><br>

            <strong>Tips:</strong><br>
            • Use quotes around multi-word values<br>
            • Separate fields with commas<br>
            • Be specific with field names (Summary, Assignee, Due Date)
        </div>
    `;

    addMessage(helpMessage, 'system');
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initialize);

/**
 * Handle user ID update from background
 */
function handleUserIdUpdate(data) {
    console.log('User ID update received:', data);

    if (!data || !data.userId) {
        console.warn('Received invalid user ID update data:', data);
        return;
    }

    // Store the user ID locally
    state.userId = data.userId;
    console.log('Updated local user ID to:', state.userId);

    // We could update UI if needed, but typically this is just for making API requests
    // Add user ID to any relevant data in the footer for debugging
    const debugLabel = document.getElementById('user-id-debug');
    if (debugLabel) {
        debugLabel.textContent = `User ID: ${state.userId}`;
    }

    // Save to local storage for persistence
    chrome.storage.local.set({
        savedUserId: data.userId,
        userIdTimestamp: Date.now()
    });
}
