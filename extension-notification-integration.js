/**
 * JCAI Browser Extension - Notification System Integration
 *
 * This file contains the notification system that works in Edge without popup blockers.
 * Copy these functions into your browser extension's content script or popup script.
 */

// Configuration
const JCAI_API_BASE = 'http://localhost:8000/api';  // Update with your production API URL
let notificationPollingInterval = null;
let customNotificationSystem = false;

// CSS for notifications (inject into page)
const NOTIFICATION_CSS = `
    .jcai-toast-container {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        max-width: 350px;
    }

    .jcai-toast-notification {
        background: #2d3748;
        color: white;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        animation: jcaiSlideIn 0.3s ease-out;
        cursor: pointer;
        transition: transform 0.2s ease;
    }

    .jcai-toast-notification:hover {
        transform: translateX(-5px);
    }

    .jcai-toast-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        font-weight: bold;
        font-size: 14px;
    }

    .jcai-toast-body {
        font-size: 13px;
        line-height: 1.4;
        color: #e2e8f0;
    }

    .jcai-toast-footer {
        font-size: 11px;
        color: #a0aec0;
        margin-top: 8px;
        font-style: italic;
    }

    .jcai-toast-close {
        background: none;
        border: none;
        color: #a0aec0;
        font-size: 18px;
        cursor: pointer;
        padding: 0;
        margin: 0;
        width: 20px;
        height: 20px;
    }

    .jcai-toast-close:hover {
        color: white;
    }

    @keyframes jcaiSlideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;

/**
 * Initialize the JCAI notification system
 * Call this when your extension starts
 */
function initializeJCAINotifications(userId) {
    // Inject CSS
    injectNotificationCSS();

    // Create toast container
    createToastContainer();

    // Store user ID
    window.jcaiUserId = userId;

    console.log('✅ JCAI Notification System initialized for user:', userId);
}

/**
 * Inject notification CSS into the page
 */
function injectNotificationCSS() {
    const existingStyle = document.getElementById('jcai-notification-css');
    if (existingStyle) {
        existingStyle.remove();
    }

    const style = document.createElement('style');
    style.id = 'jcai-notification-css';
    style.textContent = NOTIFICATION_CSS;
    document.head.appendChild(style);
}

/**
 * Create toast container if it doesn't exist
 */
function createToastContainer() {
    let container = document.getElementById('jcai-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'jcai-toast-container';
        container.className = 'jcai-toast-container';
        document.body.appendChild(container);
    }
    return container;
}

/**
 * Show a clickable toast notification
 */
function showJCAIToastNotification(title, message, notificationData = null) {
    const container = createToastContainer();

    const toast = document.createElement('div');
    toast.className = 'jcai-toast-notification';

    // Make it clickable if we have Jira URL
    if (notificationData && notificationData.data && notificationData.data.issue_url) {
        toast.onclick = function () {
            window.open(notificationData.data.issue_url, '_blank');
            toast.remove();
            console.log('🔗 JCAI notification clicked, opening:', notificationData.data.issue_url);
        };
    }

    toast.innerHTML = `
        <div class="jcai-toast-header">
            <strong>${title}</strong>
            <button onclick="this.parentElement.parentElement.remove()" class="jcai-toast-close">&times;</button>
        </div>
        <div class="jcai-toast-body">${message}</div>
        ${notificationData && notificationData.data && notificationData.data.issue_url ?
            `<div class="jcai-toast-footer">Click to open in Jira</div>` :
            ''}
    `;

    container.appendChild(toast);

    // Auto-remove after 8 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 8000);
}

/**
 * Start polling for JCAI notifications
 */
function startJCAINotificationPolling(userId, intervalSeconds = 30) {
    // Stop any existing polling
    stopJCAINotificationPolling();

    customNotificationSystem = true;

    notificationPollingInterval = setInterval(async () => {
        if (customNotificationSystem) {
            try {
                const response = await fetch(`${JCAI_API_BASE}/notifications/browser/pending/${userId}`);
                const data = await response.json();

                if (data.notifications && data.notifications.length > 0) {
                    // Show only the first notification to avoid spam
                    const notification = data.notifications[0];
                    showJCAIToastNotification(notification.title, notification.body, notification);

                    // Mark as shown by deleting it
                    await fetch(`${JCAI_API_BASE}/notifications/browser/${notification.id}`, {
                        method: 'DELETE'
                    });
                }
            } catch (error) {
                console.log('JCAI polling error:', error.message);
            }
        }
    }, intervalSeconds * 1000);

    console.log(`🔄 JCAI notification polling started (every ${intervalSeconds} seconds)`);
}

/**
 * Stop polling for JCAI notifications
 */
function stopJCAINotificationPolling() {
    if (notificationPollingInterval) {
        clearInterval(notificationPollingInterval);
        notificationPollingInterval = null;
    }

    customNotificationSystem = false;
    console.log('🛑 JCAI notification polling stopped');
}

/**
 * Test the notification system
 */
function testJCAINotificationSystem() {
    showJCAIToastNotification(
        '🧪 JCAI Test Notification',
        'This is a test notification from your JCAI extension!',
        {
            data: {
                issue_url: 'https://your-jira-instance.atlassian.net/browse/JCAI-124'
            }
        }
    );
}

// Example usage in your browser extension:
/*
// In your extension's content script or popup:

// 1. Initialize the system
initializeJCAINotifications('your-user-id-here');

// 2. Start polling for notifications
startJCAINotificationPolling('your-user-id-here', 30); // Poll every 30 seconds

// 3. Test it
testJCAINotificationSystem();

// 4. Stop when needed (e.g., when user closes extension)
// stopJCAINotificationPolling();
*/

// Export functions for use in extension
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeJCAINotifications,
        startJCAINotificationPolling,
        stopJCAINotificationPolling,
        showJCAIToastNotification,
        testJCAINotificationSystem
    };
}
