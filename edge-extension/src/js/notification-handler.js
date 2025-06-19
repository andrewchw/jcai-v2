/**
 * Browser Notification Handler for Jira Chatbot Extension
 * Handles receiving and displaying browser notifications from the server
 */

class NotificationHandler {
    constructor() {
        this.serverUrl = 'http://localhost:8000'; // Will be configurable
        this.userId = null;
        this.pollInterval = 30000; // 30 seconds
        this.isPolling = false;
        this.notificationQueue = [];

        this.init();
    }

    async init() {
        console.log('🔔 Initializing notification handler');

        // Request notification permission
        await this.requestNotificationPermission();

        // Get user ID from storage
        await this.loadUserInfo();

        // Start polling for notifications if user is authenticated
        if (this.userId) {
            this.startPolling();
        }

        // Listen for authentication status changes
        this.setupAuthenticationListener();
    }

    async requestNotificationPermission() {
        try {
            if (!('Notification' in window)) {
                console.warn('This browser does not support notifications');
                return false;
            }

            if (Notification.permission === 'granted') {
                console.log('✅ Notification permission already granted');
                return true;
            }

            if (Notification.permission !== 'denied') {
                const permission = await Notification.requestPermission();
                if (permission === 'granted') {
                    console.log('✅ Notification permission granted');
                    return true;
                } else {
                    console.log('❌ Notification permission denied');
                    return false;
                }
            }

            console.log('❌ Notifications are blocked');
            return false;
        } catch (error) {
            console.error('Error requesting notification permission:', error);
            return false;
        }
    }

    async loadUserInfo() {
        try {
            const result = await chrome.storage.local.get(['currentUserId']);
            this.userId = result.currentUserId;
            console.log('👤 Loaded user ID:', this.userId);
        } catch (error) {
            console.error('Error loading user info:', error);
        }
    }

    setupAuthenticationListener() {
        // Listen for changes in authentication status
        chrome.storage.onChanged.addListener((changes, area) => {
            if (area === 'local' && changes.currentUserId) {
                const newUserId = changes.currentUserId.newValue;

                if (newUserId !== this.userId) {
                    this.userId = newUserId;
                    console.log('👤 User ID changed:', this.userId);

                    if (newUserId) {
                        this.startPolling();
                    } else {
                        this.stopPolling();
                    }
                }
            }
        });
    }

    startPolling() {
        if (this.isPolling || !this.userId) {
            return;
        }

        console.log('🔄 Starting notification polling');
        this.isPolling = true;
        this.pollForNotifications();
    }

    stopPolling() {
        console.log('⏹️ Stopping notification polling');
        this.isPolling = false;

        if (this.pollTimeoutId) {
            clearTimeout(this.pollTimeoutId);
        }
    }

    async pollForNotifications() {
        if (!this.isPolling || !this.userId) {
            return;
        }

        try {
            const notifications = await this.fetchPendingNotifications();

            if (notifications && notifications.length > 0) {
                console.log(`📬 Received ${notifications.length} notifications`);

                for (const notification of notifications) {
                    await this.showNotification(notification);
                }
            }

        } catch (error) {
            console.error('Error polling for notifications:', error);
        }

        // Schedule next poll
        this.pollTimeoutId = setTimeout(() => {
            this.pollForNotifications();
        }, this.pollInterval);
    }

    async fetchPendingNotifications() {
        try {
            const response = await fetch(`${this.serverUrl}/api/notifications/browser/pending/${this.userId}`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data.notifications || [];

        } catch (error) {
            console.error('Error fetching notifications:', error);
            return [];
        }
    }

    async showNotification(notificationData) {
        try {
            if (Notification.permission !== 'granted') {
                console.warn('Cannot show notification: permission not granted');
                return;
            }

            const options = {
                body: notificationData.body,
                icon: notificationData.icon || '/icons/icon-48.png',
                badge: notificationData.badge || '/icons/badge-notification.png',
                tag: notificationData.tag,
                requireInteraction: notificationData.requireInteraction || false,
                silent: notificationData.silent || false,
                data: notificationData.data,
                actions: this.formatNotificationActions(notificationData.actions)
            };

            const notification = new Notification(notificationData.title, options);

            // Handle notification click
            notification.onclick = (event) => {
                this.handleNotificationClick(event, notificationData);
            };

            // Handle action clicks (if supported)
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.addEventListener('notificationclick', (event) => {
                    this.handleNotificationAction(event, notificationData);
                });
            }

            // Mark notification as sent on server
            await this.markNotificationSent(notificationData.id);

            console.log('✅ Notification displayed:', notificationData.title);

        } catch (error) {
            console.error('Error showing notification:', error);
        }
    }

    formatNotificationActions(actions) {
        if (!actions || !Array.isArray(actions)) {
            return [];
        }

        // Format actions for Notification API
        return actions.map(action => ({
            action: action.action,
            title: action.title,
            icon: action.icon
        }));
    }

    async handleNotificationClick(event, notificationData) {
        console.log('🖱️ Notification clicked:', notificationData);

        // Close the notification
        event.target.close();

        // Focus the browser window
        window.focus();

        // Open Jira issue if URL is provided
        if (notificationData.data && notificationData.data.issue_url) {
            const newTab = window.open(notificationData.data.issue_url, '_blank');
            if (newTab) {
                newTab.focus();
            }
        }

        // Send click event to server for analytics
        await this.sendNotificationResponse(notificationData, 'clicked');
    }

    async handleNotificationAction(event, notificationData) {
        console.log('⚡ Notification action:', event.action, notificationData);

        // Close the notification
        event.notification.close();

        switch (event.action) {
            case 'view':
                if (notificationData.data && notificationData.data.issue_url) {
                    const newTab = window.open(notificationData.data.issue_url, '_blank');
                    if (newTab) {
                        newTab.focus();
                    }
                }
                break;

            case 'snooze':
                await this.snoozeNotification(notificationData);
                break;

            default:
                console.log('Unknown action:', event.action);
        }

        // Send action to server
        await this.sendNotificationResponse(notificationData, event.action);
    }

    async markNotificationSent(notificationId) {
        try {
            const response = await fetch(`${this.serverUrl}/api/notifications/browser/${notificationId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                console.log('✅ Notification marked as sent:', notificationId);
            }
        } catch (error) {
            console.error('Error marking notification as sent:', error);
        }
    }

    async sendNotificationResponse(notificationData, action) {
        try {
            const issueKey = notificationData.data?.issue_key;
            if (!issueKey) return;

            const response = await fetch(`${this.serverUrl}/api/notifications/respond/${this.userId}?issue_key=${issueKey}&action=${action}`, {
                method: 'POST'
            });

            if (response.ok) {
                console.log('✅ Notification response sent:', action, issueKey);
            }
        } catch (error) {
            console.error('Error sending notification response:', error);
        }
    }

    async snoozeNotification(notificationData) {
        console.log('😴 Snoozing notification:', notificationData);

        // Show a confirmation
        const snoozeTime = '1 hour';
        this.showInfoNotification(
            'Notification Snoozed',
            `You'll be reminded about ${notificationData.data?.issue_key} in ${snoozeTime}`,
            '/icons/icon-snooze.png'
        );
    }

    showInfoNotification(title, message, icon = '/icons/icon-48.png') {
        if (Notification.permission === 'granted') {
            new Notification(title, {
                body: message,
                icon: icon,
                silent: true,
                tag: 'info'
            });
        }
    }

    // Public method to test notifications
    async createTestNotification() {
        try {
            const response = await fetch(`${this.serverUrl}/api/notifications/browser/test/${this.userId}`, {
                method: 'POST'
            });

            if (response.ok) {
                const result = await response.json();
                console.log('✅ Test notification created:', result);

                // Force an immediate poll to show the test notification
                setTimeout(() => {
                    this.pollForNotifications();
                }, 1000);

                return result;
            } else {
                throw new Error(`Failed to create test notification: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Error creating test notification:', error);
            throw error;
        }
    }

    // Get notification stats
    async getNotificationStats() {
        try {
            const response = await fetch(`${this.serverUrl}/api/notifications/browser/stats`);

            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Error getting notification stats:', error);
        }

        return null;
    }
}

// Initialize notification handler when the extension loads
let notificationHandler;

if (typeof chrome !== 'undefined' && chrome.runtime) {
    // Initialize in extension context
    notificationHandler = new NotificationHandler();

    // Make it globally accessible for testing
    window.notificationHandler = notificationHandler;

    console.log('🚀 Notification handler initialized in extension context');
} else {
    console.log('📄 Notification handler loaded but not in extension context');
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationHandler;
}
