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
    
    // Tasks
    projectFilter: document.getElementById('project-filter'),
    statusFilter: document.getElementById('status-filter'),
    tasksList: document.getElementById('tasks-list'),
    
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
    tokenStatus: document.getElementById('token-status')
};

// Connection to background script
let port;

// App state
const state = {
    serverUrl: 'http://localhost:8000',
    isAuthenticated: false,
    serverConnected: false,
    projects: [],
    tasks: []
};

/**
 * Initialize the sidebar
 */
function initialize() {
    console.log('Initializing sidebar');
    
    // Connect to background script
    port = chrome.runtime.connect({ name: 'sidebar' });
    
    setupPortListeners();
    setupEventListeners();
    loadSettings();
    
    // Display connection status
    updateConnectionStatus(false, 'Connecting...');
    
    // Check connectivity to server
    checkServerConnectivity();
}

/**
 * Set up listeners for port communication
 */
function setupPortListeners() {
    port.onMessage.addListener((message) => {
        console.log('Received message:', message);
        
        switch (message.type) {
            case 'auth-status':
                handleAuthStatusUpdate(message.payload);
                break;
                
            case 'token-status':
                handleTokenStatusUpdate(message.payload);
                break;
                
            case 'jira-projects':
                handleProjectsUpdate(message.payload);
                break;
                
            case 'jira-tasks':
                handleTasksUpdate(message.payload);
                break;
        }
    });
}

/**
 * Set up UI event listeners
 */
function setupEventListeners() {
    // Tab switching
    elements.tabButtons.forEach(button => {
        button.addEventListener('click', () => switchTab(button.id.replace('tab-', '')));
    });
    
    // Chat input
    elements.userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    elements.sendButton.addEventListener('click', sendMessage);
    elements.clearButton.addEventListener('click', clearChat);
    
    // Filter changes
    elements.projectFilter.addEventListener('change', loadTasks);
    elements.statusFilter.addEventListener('change', loadTasks);
    
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
        
        const response = await fetch(`${state.serverUrl}/api/health`);
        if (!response.ok) throw new Error('Server error');
        
        const data = await response.json();
        console.log('Server health check:', data);
        
        // Update connection status
        updateConnectionStatus(true, 'Connected');
        
        // Check authentication status
        port.postMessage({ type: 'check-token' });
        
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
    state.isAuthenticated = payload.isAuthenticated;
    
    // Update UI
    elements.oauthStatus.innerHTML = state.isAuthenticated ? 
        '<span style="color: var(--success-color);">Authenticated</span>' : 
        '<span>Not authenticated</span>';
        
    elements.loginButton.disabled = state.isAuthenticated;
    elements.logoutButton.disabled = !state.isAuthenticated;
    
    // If authenticated, load projects and check token status
    if (state.isAuthenticated) {
        port.postMessage({ type: 'check-token' });
        port.postMessage({ type: 'get-jira-projects' });
    }
}

/**
 * Handle token status update
 */
function handleTokenStatusUpdate(tokenData) {
    if (!tokenData) return;
    
    // Update token status in footer
    if (tokenData.valid) {
        const expiresIn = Math.floor((tokenData.expiresAt - Date.now()) / 1000);
        const minutes = Math.floor(expiresIn / 60);
        const seconds = expiresIn % 60;
        
        elements.tokenStatus.textContent = `Token active - expires in ${minutes}m ${seconds}s`;
    } else {
        elements.tokenStatus.textContent = 'Token expired';
    }
}

/**
 * Handle projects data update
 */
function handleProjectsUpdate(projects) {
    state.projects = projects;
    
    // Update project filter
    elements.projectFilter.innerHTML = '<option value="all">All Projects</option>';
    
    projects.forEach(project => {
        const option = document.createElement('option');
        option.value = project.key;
        option.textContent = project.name;
        elements.projectFilter.appendChild(option);
    });
    
    // Load tasks with current filters
    loadTasks();
}

/**
 * Load tasks based on current filters
 */
function loadTasks() {
    if (!state.isAuthenticated) return;
    
    // Show loading
    elements.tasksList.innerHTML = '<div class="loading-indicator">Loading tasks...</div>';
    
    // Get filter values
    const filters = {
        project: elements.projectFilter.value !== 'all' ? elements.projectFilter.value : null,
        status: elements.statusFilter.value !== 'all' ? elements.statusFilter.value : null
    };
    
    // Request tasks from background
    port.postMessage({ 
        type: 'get-jira-tasks',
        payload: filters
    });
}

/**
 * Handle tasks data update
 */
function handleTasksUpdate(tasks) {
    state.tasks = tasks;
    
    // Update tasks list
    elements.tasksList.innerHTML = '';
    
    if (tasks.length === 0) {
        elements.tasksList.innerHTML = '<div class="empty-state">No tasks found</div>';
        return;
    }
    
    // Create task elements
    tasks.forEach(task => {
        const taskElement = document.createElement('div');
        taskElement.className = 'task-item';
        taskElement.innerHTML = `
            <div class="task-header">
                <span class="task-key">${task.key}</span>
                <span class="task-status">${task.status}</span>
            </div>
            <div class="task-summary">${task.summary}</div>
            <div class="task-meta">
                ${task.assignee ? `<span>Assignee: ${task.assignee}</span>` : ''}
                ${task.dueDate ? `<span>Due: ${formatDate(task.dueDate)}</span>` : ''}
            </div>
        `;
        
        elements.tasksList.appendChild(taskElement);
    });
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
function sendMessage() {
    const message = elements.userInput.value.trim();
    if (!message) return;
    
    // Add message to chat
    addMessage(message, 'user');
    
    // Clear input
    elements.userInput.value = '';
    
    // Check if authenticated first
    if (!state.isAuthenticated) {
        addMessage('Please log in to JIRA first to use the chatbot features.', 'system');
        return;
    }
    
    // Add typing indicator
    const typingIndicator = addMessage('Thinking...', 'system');
    
    // TODO: Send message to backend for processing
    // This will be implemented when LLM integration is added
    
    // For now, add a mock response after a delay
    setTimeout(() => {
        // Remove typing indicator
        elements.messagesContainer.removeChild(typingIndicator);
        
        // Add mock response
        addMessage('This is a placeholder response. LLM integration will be implemented in the next phase.', 'bot');
    }, 1500);
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
 * Format date for display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initialize);
