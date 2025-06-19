/**
 * Enhanced Background Script Integration for JCAI Notifications
 * Add this code to your existing background.js to integrate the notification system
 */

// ========================
// NOTIFICATION SYSTEM INTEGRATION
// ========================

/**
 * JCAI Notification Manager for Background Script
 * Handles server communication and sends notifications to content scripts
 */
class JCAINotificationManager {
    constructor() {
        this.userId = null;
        this.apiBase = 'http://localhost:8000/api';
        this.pollingInterval = null;
        this.isEnabled = false;

        console.log('🔔 JCAI Notification Manager initialized');
        this.init();
    }

    async init() {
        // Get settings from storage
        await this.loadSettings();

        // Setup storage change listener
        chrome.storage.onChanged.addListener((changes) => {
            this.handleStorageChanges(changes);
        });

        // Setup message listeners
        this.setupMessageListeners();

        // Start polling if enabled
        if (this.isEnabled && this.userId) {
            this.startPolling();
        }
    }

    /**
     * Load settings from extension storage
     */
    async loadSettings() {
        try {
            const result = await chrome.storage.local.get([
                'userId',
                'serverUrl',
                'jcai-custom-notifications'
            ]);

            this.userId = result.userId;
            this.isEnabled = result['jcai-custom-notifications'] === 'enabled';

            if (result.serverUrl) {
                this.apiBase = `${result.serverUrl}/api`;
            }

            console.log(`🔧 JCAI Notifications: userId=${this.userId}, enabled=${this.isEnabled}, api=${this.apiBase}`);
        } catch (error) {
            console.error('❌ Error loading notification settings:', error);
        }
    }

    /**
     * Handle storage changes
     */
    handleStorageChanges(changes) {
        if (changes.userId) {
            this.userId = changes.userId.newValue;
            console.log(`👤 User ID updated: ${this.userId}`);
        }

        if (changes.serverUrl) {
            this.apiBase = `${changes.serverUrl.newValue}/api`;
            console.log(`🌐 API base updated: ${this.apiBase}`);
        }

        if (changes['jcai-custom-notifications']) {
            this.isEnabled = changes['jcai-custom-notifications'].newValue === 'enabled';
            console.log(`🔔 Notifications enabled: ${this.isEnabled}`);

            if (this.isEnabled && this.userId) {
                this.startPolling();
            } else {
                this.stopPolling();
            }
        }
    }

    /**
     * Setup message listeners
     */
    setupMessageListeners() {
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            switch (message.type) {
                case 'enable-notifications':
                    this.enableNotifications();
                    sendResponse({ success: true });
                    break;

                case 'disable-notifications':
                    this.disableNotifications();
                    sendResponse({ success: true });
                    break;

                case 'test-notification':
                    this.sendTestNotification();
                    sendResponse({ success: true });
                    break;

                case 'send-notification':
                    this.sendNotificationToContentScripts(message.data);
                    sendResponse({ success: true });
                    break;
            }
            return true;
        });
    }

    /**
     * Enable notification system
     */
    async enableNotifications() {
        try {
            this.isEnabled = true;
            await chrome.storage.local.set({ 'jcai-custom-notifications': 'enabled' });

            if (this.userId) {
                this.startPolling();
            }

            // Send confirmation notification
            this.sendNotificationToContentScripts({
                type: 'toast',
                notificationType: 'success',
                title: '✅ JCAI Notifications Enabled',
                message: 'Notification system is now active and will bypass popup blockers!'
            });

            console.log('🚀 JCAI notifications enabled');
        } catch (error) {
            console.error('❌ Error enabling notifications:', error);
        }
    }

    /**
     * Disable notification system
     */
    async disableNotifications() {
        try {
            this.isEnabled = false;
            await chrome.storage.local.remove(['jcai-custom-notifications']);
            this.stopPolling();

            // Send confirmation notification
            this.sendNotificationToContentScripts({
                type: 'toast',
                notificationType: 'info',
                title: '🛑 JCAI Notifications Disabled',
                message: 'Notification system has been turned off.'
            });

            console.log('🛑 JCAI notifications disabled');
        } catch (error) {
            console.error('❌ Error disabling notifications:', error);
        }
    }

    /**
     * Start polling for notifications from server
     */
    startPolling() {
        // Clear existing polling
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }

        // Poll every 15 seconds
        this.pollingInterval = setInterval(async () => {
            if (this.isEnabled && this.userId) {
                await this.checkForNotifications();
            }
        }, 15000);

        console.log('🔄 JCAI notification polling started (every 15 seconds)');
    }

    /**
     * Stop polling for notifications
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
            console.log('⏹️ JCAI notification polling stopped');
        }
    }

    /**
     * Check for new notifications from server
     */
    async checkForNotifications() {
        try {
            const response = await fetch(`${this.apiBase}/notifications/browser/pending/${this.userId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();

                if (data.notifications && data.notifications.length > 0) {
                    console.log(`📥 Received ${data.notifications.length} notifications`);

                    // Process each notification
                    for (const notification of data.notifications) {
                        this.processNotification(notification);
                    }

                    // Mark notifications as delivered
                    await this.markNotificationsAsDelivered(data.notifications.map(n => n.id));
                }
            } else if (response.status !== 404) {
                console.warn(`⚠️ Notification check failed: ${response.status}`);
            }
        } catch (error) {
            console.error('❌ Error checking for notifications:', error);
        }
    }

    /**
     * Process a single notification
     */
    processNotification(notification) {
        const { type, title, message, issueKey, jiraUrl, notificationType, priority } = notification;

        // Determine notification display method based on priority/type
        let displayType = 'toast';
        if (priority === 'high' || notificationType === 'urgent') {
            displayType = 'custom';
        }

        const notificationData = {
            type: displayType,
            notificationType: notificationType || type,
            title: title || 'JCAI Notification',
            message: message || 'You have a new notification',
            issueKey,
            jiraUrl
        };

        // Send to all content scripts
        this.sendNotificationToContentScripts(notificationData);

        // Also create native browser notification as fallback
        this.createNativeBrowserNotification(notificationData);

        console.log(`📤 Processed notification: ${title}`);
    }

    /**
     * Send notification to all content scripts
     */
    async sendNotificationToContentScripts(notificationData) {
        try {
            // Get all tabs
            const tabs = await chrome.tabs.query({});

            // Send message to each tab
            for (const tab of tabs) {
                try {
                    await chrome.tabs.sendMessage(tab.id, {
                        type: 'jcai-notification',
                        data: notificationData
                    });
                } catch (error) {
                    // Tab might not have content script loaded, ignore
                }
            }
        } catch (error) {
            console.error('❌ Error sending notification to content scripts:', error);
        }
    }

    /**
     * Create native browser notification as fallback
     */
    createNativeBrowserNotification(notificationData) {
        try {
            const { title, message, issueKey } = notificationData;

            chrome.notifications.create({
                type: 'basic',
                iconUrl: 'images/icon128.png',
                title: title,
                message: message,
                contextMessage: issueKey ? `Issue: ${issueKey}` : 'JCAI Notification'
            });
        } catch (error) {
            console.error('❌ Error creating native notification:', error);
        }
    }

    /**
     * Mark notifications as delivered to prevent re-showing
     */
    async markNotificationsAsDelivered(notificationIds) {
        try {
            await fetch(`${this.apiBase}/notifications/browser/delivered`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    userId: this.userId,
                    notificationIds: notificationIds
                })
            });

            console.log(`✅ Marked ${notificationIds.length} notifications as delivered`);
        } catch (error) {
            console.error('❌ Error marking notifications as delivered:', error);
        }
    }

    /**
     * Send test notification
     */
    sendTestNotification() {
        const testNotifications = [
            {
                type: 'toast',
                notificationType: 'success',
                title: '🧪 Test Toast',
                message: 'This is a test toast notification from JCAI!'
            },
            {
                type: 'custom',
                notificationType: 'jira_issue',
                title: 'New Issue Assignment',
                message: 'You have been assigned to a test issue',
                issueKey: 'JCAI-TEST',
                jiraUrl: 'https://example.atlassian.net/browse/JCAI-TEST'
            }
        ];

        // Send both test notifications with delay
        this.sendNotificationToContentScripts(testNotifications[0]);

        setTimeout(() => {
            this.sendNotificationToContentScripts(testNotifications[1]);
        }, 2000);

        console.log('🧪 Test notifications sent');
    }

    /**
     * Update user ID (call when user authenticates)
     */
    setUserId(userId) {
        this.userId = userId;
        console.log(`👤 JCAI notification manager user ID set: ${userId}`);

        // Start polling if enabled
        if (this.isEnabled) {
            this.startPolling();
        }
    }
}

// ========================
// INTEGRATION WITH EXISTING BACKGROUND SCRIPT
// ========================

// Initialize the notification manager
const jcaiNotificationManager = new JCAINotificationManager();

// Export for use in your existing background script
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { JCAINotificationManager, jcaiNotificationManager };
}

// Make available globally
if (typeof globalThis !== 'undefined') {
    globalThis.jcaiNotificationManager = jcaiNotificationManager;
}

/**
 * INTEGRATION INSTRUCTIONS:
 *
 * 1. Add this code to your existing background.js file
 * 2. When user authenticates successfully, call:
 *    jcaiNotificationManager.setUserId(userId);
 *
 * 3. To enable notifications programmatically:
 *    await jcaiNotificationManager.enableNotifications();
 *
 * 4. To test notifications:
 *    jcaiNotificationManager.sendTestNotification();
 *
 * 5. Update your manifest.json to include the enhanced content script:
 *    "content_scripts": [
 *      {
 *        "matches": ["<all_urls>"],
 *        "js": ["js/content-enhanced.js"]
 *      }
 *    ]
 */

console.log('🎉 JCAI Notification Manager loaded and ready for integration!');
