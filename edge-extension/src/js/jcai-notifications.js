/**
 * Enhanced Browser Notification System for JCAI Extension
 * Integrates working notification functions from test pages into browser extension
 * Provides popup-blocker-proof notifications with multiple fallback methods
 */

class JCAINotificationSystem {
    constructor() {
        this.API_BASE = 'http://localhost:8000/api';
        this.userId = null;
        this.pollingInterval = null;
        this.customNotificationSystem = false;
        this.isExtensionContext = typeof chrome !== 'undefined' && chrome.runtime;

        console.log('🔔 JCAI Enhanced Notification System initialized');
        this.init();
    }

    async init() {
        // Get user ID from extension storage
        if (this.isExtensionContext) {
            const result = await chrome.storage.local.get(['userId']);
            this.userId = result.userId;
        }

        // Initialize notification system
        this.enableCustomNotificationSystem();
    }

    // ========================
    // CORE NOTIFICATION FUNCTIONS (From working test page)
    // ========================

    /**
     * Show toast notification (top-right corner)
     * @param {string} type - 'success', 'error', 'info'
     * @param {string} title - Notification title
     * @param {string} message - Notification message
     */
    showToastNotification(type, title, message) {
        // Remove existing toast if any
        const existingToast = document.querySelector('.jcai-toast-notification');
        if (existingToast) {
            existingToast.remove();
        }

        // Create new toast
        const toast = document.createElement('div');
        toast.className = `jcai-toast-notification ${type}`;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            min-width: 300px;
            max-width: 400px;
            padding: 15px 20px;
            background: ${this.getTypeColor(type)};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            z-index: 2147483647;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        `;

        toast.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 5px;">${title}</div>
            <div style="font-size: 14px;">${message}</div>
            <div style="font-size: 12px; margin-top: 8px; opacity: 0.8;">Click to dismiss</div>
        `;

        // Add hover effect
        toast.onmouseenter = () => {
            toast.style.transform = 'translateY(-2px)';
            toast.style.boxShadow = '0 6px 16px rgba(0, 0, 0, 0.4)';
        };
        toast.onmouseleave = () => {
            toast.style.transform = 'translateY(0)';
            toast.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.3)';
        };

        // Click to dismiss
        toast.onclick = () => toast.remove();

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }
        }, 5000);

        document.body.appendChild(toast);
        console.log(`🍞 Toast: ${title} - ${message}`);
    }

    /**
     * Show custom notification (center screen)
     * @param {string} title - Notification title
     * @param {string} message - Notification message
     * @param {function} clickAction - Optional click handler
     */
    showCustomNotification(title, message, clickAction = null) {
        // Remove existing custom notification
        const existingCustom = document.querySelector('.jcai-custom-notification');
        if (existingCustom) {
            existingCustom.remove();
        }

        // Create backdrop
        const backdrop = document.createElement('div');
        backdrop.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.3);
            z-index: 2147483646;
        `;

        // Create notification
        const notification = document.createElement('div');
        notification.className = 'jcai-custom-notification';
        notification.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            min-width: 350px;
            max-width: 500px;
            padding: 25px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
            z-index: 2147483647;
            cursor: pointer;
            border-left: 5px solid #007bff;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            animation: jcaiSlideIn 0.3s ease-out;
        `;

        // Add animation keyframes
        if (!document.getElementById('jcai-notification-styles')) {
            const style = document.createElement('style');
            style.id = 'jcai-notification-styles';
            style.textContent = `
                @keyframes jcaiSlideIn {
                    from { transform: translate(-50%, -50%) scale(0.8); opacity: 0; }
                    to { transform: translate(-50%, -50%) scale(1); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }

        notification.innerHTML = `
            <h4 style="margin: 0 0 10px 0; color: #333; font-size: 18px;">${title}</h4>
            <p style="margin: 0; color: #666; line-height: 1.5;">${message}</p>
            <div style="margin-top: 15px; font-size: 12px; color: #999;">Click anywhere to dismiss</div>
        `;

        // Click handlers
        const dismiss = () => {
            if (clickAction && typeof clickAction === 'function') {
                clickAction();
            }
            backdrop.remove();
            notification.remove();
        };

        backdrop.onclick = dismiss;
        notification.onclick = dismiss;

        document.body.appendChild(backdrop);
        document.body.appendChild(notification);
        console.log(`🎯 Custom: ${title} - ${message}`);
    }

    /**
     * Show inline notification (bottom of page)
     * @param {string} message - Notification message
     */
    showInlineNotification(message) {
        // Remove existing inline notification
        const existingInline = document.querySelector('.jcai-inline-notification');
        if (existingInline) {
            existingInline.remove();
        }

        // Create inline notification
        const notification = document.createElement('div');
        notification.className = 'jcai-inline-notification';
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            right: 20px;
            padding: 15px 20px;
            background: #007bff;
            color: white;
            border-radius: 8px;
            text-align: center;
            z-index: 2147483647;
            cursor: pointer;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            animation: jcaiSlideUp 0.3s ease-out;
        `;

        // Add slide up animation
        if (!document.getElementById('jcai-inline-styles')) {
            const style = document.createElement('style');
            style.id = 'jcai-inline-styles';
            style.textContent = `
                @keyframes jcaiSlideUp {
                    from { transform: translateY(100%); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }

        notification.innerHTML = `
            ${message}
            <span style="margin-left: 15px; font-size: 12px; opacity: 0.8;">(Click to dismiss)</span>
        `;

        // Click to dismiss
        notification.onclick = () => notification.remove();

        // Auto-dismiss after 4 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.opacity = '0';
                setTimeout(() => notification.remove(), 300);
            }
        }, 4000);

        document.body.appendChild(notification);
        console.log(`📢 Inline: ${message}`);
    }

    /**
     * Show Jira-specific notification with clickable link
     * @param {string} issueKey - Jira issue key (e.g., "JCAI-123")
     * @param {string} title - Notification title
     * @param {string} jiraUrl - URL to open when clicked
     */
    showJiraNotification(issueKey, title, jiraUrl) {
        this.showCustomNotification(
            `📋 ${issueKey}: ${title}`,
            `Click to open ${issueKey} in Jira`,
            () => {
                window.open(jiraUrl, '_blank');
                this.showToastNotification('success', '🔗 Opened Jira', `${issueKey} opened in new tab`);
            }
        );
    }

    // ========================
    // EXTENSION INTEGRATION FUNCTIONS
    // ========================

    /**
     * Enable the custom notification system
     */
    async enableCustomNotificationSystem() {
        try {
            this.customNotificationSystem = true;

            // Store preference in extension storage
            if (this.isExtensionContext) {
                await chrome.storage.local.set({ 'jcai-custom-notifications': 'enabled' });
            } else {
                localStorage.setItem('jcai-custom-notifications', 'enabled');
            }

            // Show confirmation
            this.showToastNotification('success', '✅ JCAI Notifications Enabled',
                'Custom notification system is now active and bypasses popup blockers!');

            // Start polling for notifications
            this.startNotificationPolling();

            console.log('🚀 JCAI custom notification system enabled');
        } catch (error) {
            console.error('❌ Error enabling notification system:', error);
        }
    }

    /**
     * Stop the custom notification system
     */
    async stopCustomNotificationSystem() {
        try {
            this.customNotificationSystem = false;

            // Clear polling
            if (this.pollingInterval) {
                clearInterval(this.pollingInterval);
                this.pollingInterval = null;
            }

            // Remove preference from storage
            if (this.isExtensionContext) {
                await chrome.storage.local.remove(['jcai-custom-notifications']);
            } else {
                localStorage.removeItem('jcai-custom-notifications');
            }

            // Clear existing notifications
            this.clearAllNotifications();

            this.showToastNotification('info', '🛑 JCAI Notifications Stopped',
                'Custom notification system has been disabled.');

            console.log('🛑 JCAI custom notification system stopped');
        } catch (error) {
            console.error('❌ Error stopping notification system:', error);
        }
    }

    /**
     * Start polling for new notifications from the server
     */
    startNotificationPolling() {
        // Clear any existing polling
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }

        // Poll every 15 seconds
        this.pollingInterval = setInterval(async () => {
            if (this.customNotificationSystem && this.userId) {
                try {
                    const response = await fetch(`${this.API_BASE}/notifications/browser/pending/${this.userId}`);
                    if (response.ok) {
                        const data = await response.json();

                        if (data.notifications && data.notifications.length > 0) {
                            // Process each notification
                            data.notifications.forEach(notification => {
                                this.processServerNotification(notification);
                            });

                            // Mark notifications as delivered
                            await this.markNotificationsAsDelivered(data.notifications.map(n => n.id));
                        }
                    }
                } catch (error) {
                    console.error('⚠️ Polling error:', error);
                }
            }
        }, 15000);

        console.log('🔄 JCAI notification polling started (every 15 seconds)');
    }

    /**
     * Process a notification received from the server
     * @param {object} notification - Notification object from server
     */
    processServerNotification(notification) {
        const { type, title, message, issueKey, jiraUrl, notificationType } = notification;

        switch (notificationType || type) {
            case 'jira_issue':
                if (issueKey && jiraUrl) {
                    this.showJiraNotification(issueKey, title, jiraUrl);
                } else {
                    this.showCustomNotification(title, message);
                }
                break;

            case 'task_completed':
                this.showToastNotification('success', title, message);
                break;

            case 'assignment':
                this.showToastNotification('info', title, message);
                break;

            case 'comment':
                this.showToastNotification('info', title, message);
                break;

            case 'urgent':
                this.showCustomNotification(title, message);
                break;

            default:
                this.showToastNotification('info', title, message);
        }
    }

    /**
     * Mark notifications as delivered to prevent re-showing
     * @param {array} notificationIds - Array of notification IDs
     */
    async markNotificationsAsDelivered(notificationIds) {
        try {
            await fetch(`${this.API_BASE}/notifications/browser/delivered`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    userId: this.userId,
                    notificationIds: notificationIds
                })
            });
        } catch (error) {
            console.error('❌ Error marking notifications as delivered:', error);
        }
    }

    // ========================
    // UTILITY FUNCTIONS
    // ========================

    /**
     * Get color for notification type
     * @param {string} type - Notification type
     * @returns {string} CSS color
     */
    getTypeColor(type) {
        const colors = {
            success: '#28a745',
            error: '#dc3545',
            info: '#17a2b8',
            warning: '#ffc107'
        };
        return colors[type] || colors.info;
    }

    /**
     * Clear all JCAI notifications
     */
    clearAllNotifications() {
        const selectors = [
            '.jcai-toast-notification',
            '.jcai-custom-notification',
            '.jcai-inline-notification'
        ];

        selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => element.remove());
        });

        // Also remove backdrops
        const backdrops = document.querySelectorAll('div[style*="z-index: 2147483646"]');
        backdrops.forEach(backdrop => backdrop.remove());

        console.log('🧹 All JCAI notifications cleared');
    }

    /**
     * Test the complete notification workflow
     */
    testNotificationWorkflow() {
        console.log('🧪 Testing JCAI notification workflow...');

        // Step 1: Inline notification
        this.showInlineNotification('📋 Step 1: Testing inline notification system');

        setTimeout(() => {
            // Step 2: Toast notification
            this.showToastNotification('info', '📋 Step 2: Toast Test', 'Testing toast notification system');

            setTimeout(() => {
                // Step 3: Custom notification
                this.showCustomNotification('📋 Step 3: Custom Test', 'Testing custom notification system');

                setTimeout(() => {
                    // Step 4: Jira notification
                    this.showJiraNotification('JCAI-TEST', 'Test Issue', 'https://example.atlassian.net/browse/JCAI-TEST');

                    setTimeout(() => {
                        this.showToastNotification('success', '✅ Workflow Complete', 'All notification systems tested successfully!');
                    }, 2000);
                }, 1500);
            }, 1500);
        }, 1500);
    }

    /**
     * Update user ID (called from extension when user authenticates)
     * @param {string} userId - User ID
     */
    setUserId(userId) {
        this.userId = userId;
        console.log(`👤 JCAI notification system user ID set: ${userId}`);

        // Start polling if system is enabled
        if (this.customNotificationSystem) {
            this.startNotificationPolling();
        }
    }

    /**
     * Update API base URL (called from extension settings)
     * @param {string} apiBase - API base URL
     */
    setApiBase(apiBase) {
        this.API_BASE = apiBase;
        console.log(`🌐 JCAI notification system API base updated: ${apiBase}`);
    }
}

// ========================
// EXTENSION INTEGRATION
// ========================

// Initialize the notification system
const jcaiNotifications = new JCAINotificationSystem();

// Export for use in other extension files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = JCAINotificationSystem;
}

// Make available globally for extension context
if (typeof window !== 'undefined') {
    window.JCAINotificationSystem = JCAINotificationSystem;
    window.jcaiNotifications = jcaiNotifications;
}

console.log('🎉 JCAI Enhanced Notification System loaded and ready!');
