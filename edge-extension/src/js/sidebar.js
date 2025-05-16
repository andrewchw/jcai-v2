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
    
    // Create a bot message element for streaming response
    const botMessageElement = document.createElement('div');
    botMessageElement.className = 'message bot typing';
    botMessageElement.textContent = '...';
    chatMessages.appendChild(botMessageElement);
    scrollToBottom();
    
    // Get the API URL from settings or use default
    const apiUrl = 'http://localhost:8000/api/chat/stream';
    
    // Send message to Python server via streaming API
    const eventSource = new EventSource(`${apiUrl}?message=${encodeURIComponent(message)}`);
    let fullResponse = '';
    let jiraReferences = [];
    
    eventSource.onmessage = (event) => {
      if (event.data === '[DONE]') {
        eventSource.close();
        // Update with full message when complete
        botMessageElement.className = 'message bot';
        botMessageElement.textContent = fullResponse;
        
        // Display Jira references if any
        if (jiraReferences.length > 0) {
          const referencesElement = document.createElement('div');
          referencesElement.className = 'jira-references';
          
          const title = document.createElement('div');
          title.className = 'references-title';
          title.textContent = 'Jira References:';
          referencesElement.appendChild(title);
          
          jiraReferences.forEach(ref => {
            const refElement = document.createElement('div');
            refElement.className = 'jira-reference';
            refElement.textContent = `${ref.key}: ${ref.summary} (${ref.status})`;
            referencesElement.appendChild(refElement);
          });
          
          chatMessages.appendChild(referencesElement);
        }
        
        scrollToBottom();
        return;
      }
      
      try {
        const data = JSON.parse(event.data);
        
        switch (data.event) {
          case 'token':
            fullResponse += data.message;
            botMessageElement.textContent = fullResponse;
            scrollToBottom();
            break;
            
          case 'reference':
            jiraReferences.push(data.reference);
            break;
            
          case 'error':
            botMessageElement.className = 'message bot error';
            botMessageElement.textContent = data.message;
            eventSource.close();
            break;
        }
      } catch (e) {
        console.error('Error parsing event data:', e);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error('EventSource error:', error);
      eventSource.close();
      botMessageElement.className = 'message bot error';
      botMessageElement.textContent = 'Error connecting to server. Please try again later.';
      scrollToBottom();
    };
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
