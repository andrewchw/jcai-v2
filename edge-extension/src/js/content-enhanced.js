/**
 * Enhanced Content Script for JIRA Chatbot Assistant
 * Integrates the JCAI notification system into web pages
 * This script runs in the context of web pages and handles notifications
 */

// Wrap in IIFE to avoid global scope pollution
(function () {
    'use strict';    // Check extension context with better debugging and validation
    console.log('JCAI: Content script starting...');
    console.log('JCAI: Chrome runtime available:', typeof chrome !== 'undefined' && !!chrome.runtime);

    let isExtensionContextValid = false;

    if (typeof chrome === 'undefined' || !chrome.runtime) {
        console.error('JCAI: Chrome extension APIs not available');
        return;
    }

    try {
        // Test if extension context is valid
        const extensionId = chrome.runtime.id;
        console.log('JCAI: Extension ID:', extensionId);

        // Additional validation - try to access extension APIs
        if (chrome.runtime.sendMessage && chrome.runtime.getManifest) {
            isExtensionContextValid = true;
            console.log('JCAI Enhanced Content Script loaded successfully');
        } else {
            throw new Error('Extension APIs not fully available');
        }
    } catch (error) {
        console.error('JCAI: Extension context error:', error);
        console.log('JCAI: Extension context is invalid - likely after reload');
        isExtensionContextValid = false;
        // Don't return here - we can still provide the bridge for testing
    }

    // Function to check if extension context is still valid
    function checkExtensionContext() {
        try {
            return chrome.runtime && chrome.runtime.id && isExtensionContextValid;
        } catch (error) {
            console.warn('JCAI: Extension context became invalid:', error);
            isExtensionContextValid = false;
            return false;
        }
    }

    // ========================
    // NOTIFICATION SYSTEM INTEGRATION
    // ========================

    /**
     * JCAI Enhanced Notification System for Content Script
     * Popup-blocker-proof notifications that work in any web page context
     */
    class JCAIContentNotifications {
        constructor() {
            this.userId = null;
            this.isEnabled = false;
            this.init();
        }

        async init() {
            // Get user ID and notification settings from extension storage
            try {
                const result = await chrome.storage.local.get(['userId', 'jcai-custom-notifications']);
                this.userId = result.userId;
                this.isEnabled = result['jcai-custom-notifications'] === 'enabled';

                if (this.isEnabled) {
                    console.log('🔔 JCAI notifications enabled for content script');
                    this.setupNotificationListener();
                }
            } catch (error) {
                console.error('❌ Error initializing JCAI notifications:', error);
            }
        }

        /**
         * Setup listener for notifications from background script
         */
        setupNotificationListener() {
            // Listen for messages from background script
            chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
                if (message.type === 'jcai-notification') {
                    this.handleNotification(message.data);
                    sendResponse({ success: true });
                }
                return true;
            });
        }

        /**
         * Handle notification received from background script
         * @param {object} notificationData - Notification data
         */
        handleNotification(notificationData) {
            const { notificationType, type, title, message, issueKey, jiraUrl } = notificationData;

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
         * Show toast notification (top-right corner)
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
                animation: jcaiToastSlideIn 0.3s ease-out;
            `;

            // Add animation styles if not already present
            this.addAnimationStyles();

            toast.innerHTML = `
                <div style="font-weight: bold; margin-bottom: 5px;">${title}</div>
                <div style="font-size: 14px; line-height: 1.4;">${message}</div>
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
            toast.onclick = () => {
                toast.style.animation = 'jcaiToastSlideOut 0.3s ease-in';
                setTimeout(() => toast.remove(), 300);
            };

            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.style.animation = 'jcaiToastSlideOut 0.3s ease-in';
                    setTimeout(() => toast.remove(), 300);
                }
            }, 5000);

            document.body.appendChild(toast);
            console.log(`🍞 JCAI Toast: ${title} - ${message}`);
        }

        /**
         * Show custom notification (center screen)
         */
        showCustomNotification(title, message, clickAction = null) {
            // Remove existing custom notification
            const existingCustom = document.querySelector('.jcai-custom-notification');
            if (existingCustom) {
                existingCustom.remove();
            }

            // Create backdrop
            const backdrop = document.createElement('div');
            backdrop.className = 'jcai-notification-backdrop';
            backdrop.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.3);
                z-index: 2147483646;
                animation: jcaiBackdropFadeIn 0.3s ease-out;
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
                animation: jcaiCustomSlideIn 0.3s ease-out;
            `;

            notification.innerHTML = `
                <h4 style="margin: 0 0 10px 0; color: #333; font-size: 18px; font-weight: 600;">${title}</h4>
                <p style="margin: 0; color: #666; line-height: 1.5; font-size: 14px;">${message}</p>
                <div style="margin-top: 15px; font-size: 12px; color: #999;">Click anywhere to dismiss</div>
            `;

            // Click handlers
            const dismiss = () => {
                if (clickAction && typeof clickAction === 'function') {
                    clickAction();
                }
                backdrop.style.animation = 'jcaiBackdropFadeOut 0.3s ease-in';
                notification.style.animation = 'jcaiCustomSlideOut 0.3s ease-in';
                setTimeout(() => {
                    backdrop.remove();
                    notification.remove();
                }, 300);
            };

            backdrop.onclick = dismiss;
            notification.onclick = dismiss;

            document.body.appendChild(backdrop);
            document.body.appendChild(notification);
            console.log(`🎯 JCAI Custom: ${title} - ${message}`);
        }

        /**
         * Show Jira-specific notification with clickable link
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

        /**
         * Show inline notification (bottom of page)
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
                animation: jcaiInlineSlideUp 0.3s ease-out;
            `;

            notification.innerHTML = `
                ${message}
                <span style="margin-left: 15px; font-size: 12px; opacity: 0.8;">(Click to dismiss)</span>
            `;

            // Click to dismiss
            notification.onclick = () => {
                notification.style.animation = 'jcaiInlineSlideDown 0.3s ease-in';
                setTimeout(() => notification.remove(), 300);
            };

            // Auto-dismiss after 4 seconds
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.style.animation = 'jcaiInlineSlideDown 0.3s ease-in';
                    setTimeout(() => notification.remove(), 300);
                }
            }, 4000);

            document.body.appendChild(notification);
            console.log(`📢 JCAI Inline: ${message}`);
        }

        /**
         * Add animation styles to the page
         */
        addAnimationStyles() {
            if (document.getElementById('jcai-notification-animations')) return;

            const style = document.createElement('style');
            style.id = 'jcai-notification-animations';
            style.textContent = `
                @keyframes jcaiToastSlideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes jcaiToastSlideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
                @keyframes jcaiCustomSlideIn {
                    from { transform: translate(-50%, -50%) scale(0.8); opacity: 0; }
                    to { transform: translate(-50%, -50%) scale(1); opacity: 1; }
                }
                @keyframes jcaiCustomSlideOut {
                    from { transform: translate(-50%, -50%) scale(1); opacity: 1; }
                    to { transform: translate(-50%, -50%) scale(0.8); opacity: 0; }
                }
                @keyframes jcaiBackdropFadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                @keyframes jcaiBackdropFadeOut {
                    from { opacity: 1; }
                    to { opacity: 0; }
                }
                @keyframes jcaiInlineSlideUp {
                    from { transform: translateY(100%); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
                @keyframes jcaiInlineSlideDown {
                    from { transform: translateY(0); opacity: 1; }
                    to { transform: translateY(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }

        /**
         * Get color for notification type
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
                '.jcai-inline-notification',
                '.jcai-notification-backdrop'
            ];

            selectors.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                elements.forEach(element => element.remove());
            });

            console.log('🧹 All JCAI notifications cleared');
        }
    }

    // ========================
    // HOVER ICON SYSTEM (Existing functionality)
    // ========================

    let hoverIcon = null;
    let isIconVisible = false;
    let hideTimeout = null;

    // Styles for the hover icon
    const iconStyles = `
    .jcai-hover-container {
        position: fixed;
        top: 50%;
        right: 20px;
        transform: translateY(-50%);
        z-index: 10000;
        pointer-events: none;
        transition: opacity 0.3s ease, transform 0.3s ease;
    }
    .jcai-hover-icon {
        width: 48px;
        height: 48px;
        background: none;
        border: none;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        pointer-events: auto;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: visible;
    }
    .jcai-hover-icon:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 25px rgba(0, 0, 0, 0.2);
    }
    .jcai-hover-icon img {
        width: 100%;
        height: 100%;
        border-radius: inherit;
        object-fit: cover;
    }
    .jcai-hidden {
        opacity: 0;
        pointer-events: none;
        transform: translateY(-50%) translateX(20px);
    }
    `;

    /**
     * Create and inject the hover icon
     */
    function createHoverIcon() {
        if (hoverIcon) return;

        // Add styles to the page
        const style = document.createElement('style');
        style.textContent = iconStyles;
        document.head.appendChild(style);

        // Create the icon container
        const container = document.createElement('div');
        container.className = 'jcai-hover-container jcai-hidden';
        container.innerHTML = `
            <button class="jcai-hover-icon" title="JIRA Chatbot Assistant">
                <img src="${chrome.runtime.getURL('images/icon128.png')}" alt="JCAI" />
            </button>
        `;

        // Add click handler
        container.querySelector('.jcai-hover-icon').addEventListener('click', handleIconClick);

        document.body.appendChild(container);
        hoverIcon = container;

        // Show the icon after a brief delay
        setTimeout(() => {
            if (hoverIcon) {
                hoverIcon.classList.remove('jcai-hidden');
                isIconVisible = true;
            }
        }, 1000);
    }

    /**
     * Handle icon click
     */    function handleIconClick() {
        console.log('JCAI hover icon clicked');

        // Check if extension context is still valid
        if (!checkExtensionContext()) {
            console.warn('JCAI: Cannot open side panel - extension context invalid. Please refresh the page.');
            // Show a user-friendly notification instead
            if (typeof jcaiNotifications !== 'undefined') {
                jcaiNotifications.showToastNotification('warning', '⚠️ Extension Reload Required', 'Please refresh the page after reloading the extension.');
            } else {
                alert('Extension was reloaded. Please refresh the page to use JCAI features.');
            }
            return;
        }

        try {
            // Open the extension side panel
            chrome.runtime.sendMessage({ type: 'openSidePanel' }, (response) => {
                if (chrome.runtime.lastError) {
                    console.error('Error opening side panel:', chrome.runtime.lastError);
                    // Mark context as invalid if we get this error
                    isExtensionContextValid = false;
                }
            });
        } catch (error) {
            console.error('Error opening side panel:', error);
            isExtensionContextValid = false;
        }
    }// ========================
    // INITIALIZATION
    // ========================

    // Initialize the notification system
    const jcaiNotifications = new JCAIContentNotifications();

    // Create hover icon
    createHoverIcon();

    // Listen for extension messages
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        switch (message.type) {
            case 'test-notification':
                jcaiNotifications.showToastNotification('info', '🧪 Test Notification', 'This is a test from the extension!');
                sendResponse({ success: true });
                break;

            case 'clear-notifications':
                jcaiNotifications.clearAllNotifications();
                sendResponse({ success: true });
                break;

            default:
                // Let the notification system handle other messages
                break;
        }
        return true;
    });

    // ========================
    // EXPOSE API TO WEB PAGE (for testing)
    // ========================    // Create a bridge between content script and web page for testing
    let extensionInfo = {
        id: 'unknown',
        version: '0.1.0',
        name: 'JIRA Chatbot Assistant'
    };

    // Try to get extension info safely
    try {
        if (chrome.runtime && chrome.runtime.id) {
            extensionInfo.id = chrome.runtime.id;
        }
        if (chrome.runtime && chrome.runtime.getManifest) {
            const manifest = chrome.runtime.getManifest();
            extensionInfo.version = manifest.version;
            extensionInfo.name = manifest.name;
        }
    } catch (error) {
        console.warn('JCAI: Could not get extension info:', error);
    }

    const jcaiExtensionBridge = {
        isExtensionAvailable: true,
        extensionId: extensionInfo.id,
        version: extensionInfo.version,
        name: extensionInfo.name,

        // Test functions that web page can call
        testNotification: () => {
            jcaiNotifications.showToastNotification('success', '🧪 Extension Test', 'Direct test from extension bridge!');
        },

        testCustomNotification: () => {
            jcaiNotifications.showCustomNotification('🧪 Extension Custom Test', 'This custom notification came from the extension!');
        },

        testJiraNotification: () => {
            jcaiNotifications.showJiraNotification('JCAI-BRIDGE', 'Bridge Test Issue', 'https://example.atlassian.net/browse/JCAI-BRIDGE');
        },

        testInlineNotification: () => {
            jcaiNotifications.showInlineNotification('🧪 Extension bridge inline notification test!');
        }, clearNotifications: () => {
            jcaiNotifications.clearAllNotifications();
        },

        // Send message to background script
        sendMessageToBackground: (message) => {
            return new Promise((resolve) => {
                try {
                    if (!checkExtensionContext()) {
                        resolve({ error: 'Extension context invalid - please refresh page after reloading extension' });
                        return;
                    }

                    chrome.runtime.sendMessage(message, (response) => {
                        if (chrome.runtime.lastError) {
                            console.warn('JCAI: Background message error:', chrome.runtime.lastError.message);
                            if (chrome.runtime.lastError.message.includes('context invalidated')) {
                                isExtensionContextValid = false;
                            }
                            resolve({ error: chrome.runtime.lastError.message });
                        } else {
                            resolve(response || { success: true });
                        }
                    });
                } catch (error) {
                    resolve({ error: error.message });
                }
            });
        }
    };

    // Create CSP-safe bridge using direct window assignment and custom events
    console.log('JCAI: Creating CSP-safe extension bridge...');

    try {
        // Use a custom event-based approach that works with CSP
        const bridgeInterface = {
            isExtensionAvailable: true,
            extensionId: jcaiExtensionBridge.extensionId,
            version: jcaiExtensionBridge.version,
            name: jcaiExtensionBridge.name,

            // Test functions that dispatch custom events
            testNotification: function () {
                console.log('JCAI: Bridge test notification called');
                document.dispatchEvent(new CustomEvent('jcai-test-notification'));
            },

            testCustomNotification: function () {
                document.dispatchEvent(new CustomEvent('jcai-test-custom-notification'));
            },

            testJiraNotification: function () {
                document.dispatchEvent(new CustomEvent('jcai-test-jira-notification'));
            },

            testInlineNotification: function () {
                document.dispatchEvent(new CustomEvent('jcai-test-inline-notification'));
            },

            clearNotifications: function () {
                document.dispatchEvent(new CustomEvent('jcai-clear-notifications'));
            }, sendMessageToBackground: function (message) {
                return new Promise((resolve) => {
                    if (!checkExtensionContext()) {
                        resolve({ error: 'Extension context invalid - please refresh page after reloading extension' });
                        return;
                    }

                    const messageId = 'jcai-msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);

                    function handleResponse(event) {
                        if (event.detail.messageId === messageId) {
                            document.removeEventListener('jcai-background-response', handleResponse);
                            resolve(event.detail.response);
                        }
                    }

                    document.addEventListener('jcai-background-response', handleResponse);
                    document.dispatchEvent(new CustomEvent('jcai-background-message', {
                        detail: {
                            message: message,
                            messageId: messageId
                        }
                    }));

                    // Timeout after 5 seconds
                    setTimeout(() => {
                        document.removeEventListener('jcai-background-response', handleResponse);
                        resolve({ error: 'Timeout' });
                    }, 5000);
                });
            }
        };

        // Assign bridge directly to window (works in most contexts)
        window.jcaiExtensionBridge = bridgeInterface;
        console.log('JCAI: Extension bridge assigned directly to window');
        console.log('🎉 JCAI Extension Bridge loaded and available (CSP-safe)!');
    } catch (error) {
        console.error('JCAI: Failed to create CSP-safe extension bridge:', error);
    }    // Listen for custom events from the web page bridge
    document.addEventListener('jcai-test-notification', () => {
        jcaiNotifications.showToastNotification('success', '🧪 Extension Test', 'Direct test from extension bridge!');
    });

    document.addEventListener('jcai-test-custom-notification', () => {
        jcaiNotifications.showCustomNotification('🧪 Extension Custom Test', 'This custom notification came from the extension!');
    });

    document.addEventListener('jcai-test-jira-notification', () => {
        jcaiNotifications.showJiraNotification('JCAI-BRIDGE', 'Bridge Test Issue', 'https://example.atlassian.net/browse/JCAI-BRIDGE');
    });

    document.addEventListener('jcai-test-inline-notification', () => {
        jcaiNotifications.showInlineNotification('🧪 Extension bridge inline notification test!');
    });

    document.addEventListener('jcai-clear-notifications', () => {
        jcaiNotifications.clearAllNotifications();
    }); document.addEventListener('jcai-background-message', (event) => {
        // Check extension context before forwarding message
        if (!checkExtensionContext()) {
            document.dispatchEvent(new CustomEvent('jcai-background-response', {
                detail: {
                    messageId: event.detail.messageId,
                    response: { error: 'Extension context invalid - please refresh page after reloading extension' }
                }
            }));
            return;
        }

        // Forward message to background script
        chrome.runtime.sendMessage(event.detail.message, (response) => {
            if (chrome.runtime.lastError && chrome.runtime.lastError.message.includes('context invalidated')) {
                isExtensionContextValid = false;
            }

            document.dispatchEvent(new CustomEvent('jcai-background-response', {
                detail: {
                    messageId: event.detail.messageId,
                    response: response || { error: chrome.runtime.lastError?.message }
                }
            }));
        });
    });

    console.log('🎉 JCAI Enhanced Content Script fully loaded!');

})();
