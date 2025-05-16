// Sidebar functionality for Jira Action Items Manager

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const loginButton = document.getElementById('loginButton');
  const userInfo = document.getElementById('userInfo');
  const usernameElement = document.getElementById('username');
  const chatMessages = document.getElementById('chatMessages');
  const userInput = document.getElementById('userInput');
  const sendButton = document.getElementById('sendButton');

  // Check authentication status
  checkAuthStatus();

  // Event listeners
  loginButton.addEventListener('click', handleLogin);
  sendButton.addEventListener('click', handleSendMessage);
  userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  // Function to check authentication status
  function checkAuthStatus() {
    chrome.runtime.sendMessage({ type: 'checkAuth' }, (response) => {
      if (response.isAuthenticated) {
        loginButton.textContent = 'Logout';
        loginButton.dataset.action = 'logout';
        userInfo.classList.remove('hidden');
        usernameElement.textContent = response.username;
      } else {
        loginButton.textContent = 'Login';
        loginButton.dataset.action = 'login';
        userInfo.classList.add('hidden');
      }
    });
  }

  // Function to handle login/logout
  function handleLogin() {
    const action = loginButton.dataset.action || 'login';
    
    if (action === 'login') {
      chrome.runtime.sendMessage({ type: 'login' }, (response) => {
        if (response.success) {
          checkAuthStatus();
          addSystemMessage('Authentication successful!');
        }
      });
    } else {
      chrome.runtime.sendMessage({ type: 'logout' }, (response) => {
        if (response.success) {
          checkAuthStatus();
          addSystemMessage('You have been logged out.');
        }
      });
    }
  }

  // Function to handle sending messages
  function handleSendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addUserMessage(message);
    userInput.value = '';

    // Mock response for now - will be replaced with actual API call
    setTimeout(() => {
      addBotMessage('I received your message: "' + message + '". This is a placeholder response. The actual integration with the Python server and Jira will be implemented soon.');
    }, 1000);

    // TODO: Send message to Python server via API call
  }

  // Function to add a user message to the chat
  function addUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    messageDiv.textContent = text;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
  }

  // Function to add a bot message to the chat
  function addBotMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';
    messageDiv.textContent = text;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
  }

  // Function to add a system message to the chat
  function addSystemMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';
    messageDiv.textContent = text;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
  }

  // Function to scroll chat to the bottom
  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
});
