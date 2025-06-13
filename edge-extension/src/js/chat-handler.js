/**
 * Chat Handler for Jira Chatbot Extension
 *
 * This module handles natural language chat interactions with the Jira API
 * through the LLM service integration.
 */

class ChatHandler {
    constructor() {
        this.baseUrl = null; // Will be loaded dynamically from settings
        this.currentUserId = null;
        this.isProcessing = false;
        this.conversationHistory = [];

        // Chat UI elements (will be set when DOM is ready)
        this.chatContainer = null;
        this.chatInput = null;
        this.sendButton = null;
        this.messagesContainer = null;

        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initialize());
        } else {
            this.initialize();
        }
    }

    /**
     * Get the current API base URL from settings
     */
    async getApiBaseUrl() {
        try {
            const settings = await chrome.storage.local.get(['serverUrl']);
            const serverUrl = settings.serverUrl || 'https://67fa-203-145-94-95.ngrok-free.app';
            return `${serverUrl}/api`;
        } catch (error) {
            console.error('Error getting server URL from settings:', error);
            return 'https://67fa-203-145-94-95.ngrok-free.app/api'; // Fallback
        }
    }

    initialize() {
        console.log('Initializing ChatHandler...');
        this.setupChatUI();
        this.bindEvents();
    }

    setupChatUI() {
        // Get chat elements
        this.chatContainer = document.getElementById('chat-container');
        this.chatInput = document.getElementById('chat-input');
        this.sendButton = document.getElementById('send-button');
        this.messagesContainer = document.getElementById('messages-container');

        if (!this.chatContainer) {
            console.warn('Chat container not found - chat functionality disabled');
            return;
        }

        // Create messages container if it doesn't exist
        if (!this.messagesContainer) {
            this.messagesContainer = document.createElement('div');
            this.messagesContainer.id = 'messages-container';
            this.messagesContainer.className = 'messages-container';
            this.chatContainer.insertBefore(this.messagesContainer, this.chatInput?.parentElement || this.chatContainer.firstChild);
        }

        // Show welcome message
        this.addMessage({
            text: "Hi! I'm your Jira assistant. You can ask me to create tasks, search for issues, or update existing ones. Try saying something like 'Create a task for John to review docs by Friday' or 'What tasks are assigned to me?'",
            sender: 'bot',
            timestamp: new Date()
        });
    }

    bindEvents() {
        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => this.handleSendMessage());
        }

        if (this.chatInput) {
            this.chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleSendMessage();
                }
            });

            // Auto-resize textarea
            this.chatInput.addEventListener('input', () => {
                this.chatInput.style.height = 'auto';
                this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 120) + 'px';
            });
        }
    }

    async handleSendMessage() {
        if (this.isProcessing || !this.chatInput) return;

        const message = this.chatInput.value.trim();
        if (!message) return;

        // Check if user is authenticated
        if (!this.currentUserId) {
            this.addMessage({
                text: "Please log in to Jira first to use the chatbot features.",
                sender: 'bot',
                timestamp: new Date()
            });
            return;
        }

        // Add user message to UI
        this.addMessage({
            text: message,
            sender: 'user',
            timestamp: new Date()
        });

        // Clear input
        this.chatInput.value = '';
        this.chatInput.style.height = 'auto';

        // Process message
        await this.processMessage(message);
    }

    async processMessage(message) {
        this.setProcessing(true); try {
            console.log(`Processing message: ${message}`);
            const baseUrl = await this.getApiBaseUrl();
            const response = await fetch(`${baseUrl}/chat/message/${this.currentUserId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: JSON.stringify({
                    text: message
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const chatResponse = await response.json();
            console.log('Chat response:', chatResponse);

            // Add bot response to UI
            this.addMessage({
                text: chatResponse.text,
                sender: 'bot',
                timestamp: new Date(),
                intent: chatResponse.intent,
                confidence: chatResponse.confidence,
                jira_result: chatResponse.jira_action_result
            });

            // Handle special actions
            if (chatResponse.jira_action_result) {
                this.handleJiraResult(chatResponse.jira_action_result);
            }

            // Store conversation history
            this.conversationHistory.push({
                user_message: message,
                bot_response: chatResponse,
                timestamp: new Date()
            });

        } catch (error) {
            console.error('Error processing message:', error);
            this.addMessage({
                text: `Sorry, I encountered an error: ${error.message}. Please try again.`,
                sender: 'bot',
                timestamp: new Date(),
                isError: true
            });
        } finally {
            this.setProcessing(false);
        }
    }

    addMessage(message) {
        if (!this.messagesContainer) return;

        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.sender}-message`;

        if (message.isError) {
            messageElement.classList.add('error-message');
        }

        const timestamp = message.timestamp ? this.formatTimestamp(message.timestamp) : '';

        let messageHTML = `
            <div class="message-content">
                <div class="message-text">${this.formatMessageText(message.text)}</div>
                ${timestamp ? `<div class="message-timestamp">${timestamp}</div>` : ''}
            </div>
        `;

        // Add confidence indicator for bot messages
        if (message.sender === 'bot' && message.confidence !== undefined) {
            const confidenceClass = message.confidence > 0.8 ? 'high' : message.confidence > 0.5 ? 'medium' : 'low';
            messageHTML += `<div class="confidence-indicator ${confidenceClass}" title="Confidence: ${Math.round(message.confidence * 100)}%"></div>`;
        }

        // Add Jira result display
        if (message.jira_result) {
            messageHTML += this.formatJiraResult(message.jira_result);
        }

        messageElement.innerHTML = messageHTML;
        this.messagesContainer.appendChild(messageElement);

        // Scroll to bottom
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    formatMessageText(text) {
        // Convert URLs to links
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        text = text.replace(urlRegex, '<a href="$1" target="_blank">$1</a>');

        // Convert issue keys to links (assuming JIRA URL is available)
        const issueKeyRegex = /\b([A-Z]+-\d+)\b/g;
        text = text.replace(issueKeyRegex, '<span class="issue-key">$1</span>');

        // Convert newlines to <br>
        text = text.replace(/\n/g, '<br>');

        return text;
    }

    formatJiraResult(result) {
        if (!result) return '';

        let html = '<div class="jira-result">';

        if (result.success) {
            html += '<div class="jira-success">✅ Success</div>';
            if (result.issue_key) {
                html += `<div class="jira-issue-key">Issue: <span class="issue-key">${result.issue_key}</span></div>`;
            }
            if (result.issue_url) {
                html += `<div class="jira-link"><a href="${result.issue_url}" target="_blank">View in Jira</a></div>`;
            }
        } else {
            html += '<div class="jira-error">❌ Error</div>';
            if (result.error) {
                html += `<div class="jira-error-message">${result.error}</div>`;
            }
        }

        html += '</div>';
        return html;
    }

    handleJiraResult(result) {
        if (result && result.success) {
            console.log('Jira action completed successfully:', result);

            // Trigger refresh of tasks list if it exists
            if (window.updateTasksList) {
                window.updateTasksList();
            }

            // Send update to background script
            if (chrome?.runtime?.sendMessage) {
                chrome.runtime.sendMessage({
                    type: 'jira-action-completed',
                    result: result
                });
            }
        }
    }

    formatTimestamp(timestamp) {
        if (!timestamp) return '';
        const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    setProcessing(processing) {
        this.isProcessing = processing;

        if (this.sendButton) {
            this.sendButton.disabled = processing;
            this.sendButton.textContent = processing ? '...' : 'Send';
        }

        if (this.chatInput) {
            this.chatInput.disabled = processing;
        }

        // Add/remove processing indicator
        if (processing) {
            this.addProcessingIndicator();
        } else {
            this.removeProcessingIndicator();
        }
    }

    addProcessingIndicator() {
        if (!this.messagesContainer) return;

        const existingIndicator = this.messagesContainer.querySelector('.processing-indicator');
        if (existingIndicator) return;

        const indicator = document.createElement('div');
        indicator.className = 'message bot-message processing-indicator';
        indicator.innerHTML = `
            <div class="message-content">
                <div class="message-text">
                    <span class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </span>
                </div>
            </div>
        `;

        this.messagesContainer.appendChild(indicator);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    removeProcessingIndicator() {
        if (!this.messagesContainer) return;

        const indicator = this.messagesContainer.querySelector('.processing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    setUserId(userId) {
        this.currentUserId = userId;
        console.log(`Chat handler set for user: ${userId}`);
    }

    clearChat() {
        if (this.messagesContainer) {
            this.messagesContainer.innerHTML = '';
            this.setupChatUI(); // Re-add welcome message
        }
        this.conversationHistory = [];
    }    // Public API for integration with sidebar
    async testConnection() {
        try {
            const baseUrl = await this.getApiBaseUrl();
            const response = await fetch(`${baseUrl}/chat/health`, {
                headers: {
                    'ngrok-skip-browser-warning': 'true'
                }
            });
            return response.ok;
        } catch (error) {
            console.error('Chat service connection test failed:', error);
            return false;
        }
    } async getUserProjects() {
        if (!this.currentUserId) return [];
        try {
            const baseUrl = await this.getApiBaseUrl();
            const response = await fetch(`${baseUrl}/chat/projects/${this.currentUserId}`, {
                headers: {
                    'ngrok-skip-browser-warning': 'true'
                }
            });
            if (response.ok) {
                const data = await response.json();
                return data.projects || [];
            }
        } catch (error) {
            console.error('Error getting user projects:', error);
        }
        return [];
    }
}

// Create global instance
window.chatHandler = new ChatHandler();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChatHandler;
}
