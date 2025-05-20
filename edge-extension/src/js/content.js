/**
 * Content script for JIRA Chatbot Assistant
 * This script runs in the context of web pages and can interact with their DOM
 */

console.log('JIRA Chatbot Assistant content script loaded');

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Content script received message:', message);
    
    // Handle messages here when needed
    
    return true;
});

// Future functionality:
// 1. Detect JIRA pages and enhance them with additional controls
// 2. Extract context from the current page for the chatbot
// 3. Create overlay components for quick actions
