// Background script for Jira Action Items Manager

// Handle installation and updates
chrome.runtime.onInstalled.addListener(() => {
  console.log('Extension installed or updated');
  
  // Initialize storage if needed
  chrome.storage.local.get(['authToken', 'refreshToken'], (result) => {
    if (!result.authToken) {
      console.log('No authentication token found, user needs to log in');
    }
  });
});

// Listen for messages from sidebar
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'checkAuth') {
    // Check if user is authenticated
    chrome.storage.local.get(['authToken', 'username'], (result) => {
      sendResponse({
        isAuthenticated: !!result.authToken,
        username: result.username || ''
      });
    });
    return true; // Indicate we will send a response asynchronously
  }
  
  if (message.type === 'login') {
    // Will implement OAuth flow in Phase 1
    console.log('Login requested');
    // Mock authentication for now
    chrome.storage.local.set({
      authToken: 'mock-token',
      username: 'Test User'
    }, () => {
      sendResponse({ success: true });
    });
    return true;
  }
  
  if (message.type === 'logout') {
    // Handle logout
    chrome.storage.local.remove(['authToken', 'refreshToken', 'username'], () => {
      sendResponse({ success: true });
    });
    return true;
  }
});

// For future use: notification handling
chrome.notifications.onClicked.addListener((notificationId) => {
  // Handle notification click
  console.log(`Notification clicked: ${notificationId}`);
});
