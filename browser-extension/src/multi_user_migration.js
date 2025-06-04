/**
 * Client-side Migration Helper for Multi-user Authentication
 *
 * This script helps migrate the browser extension to use the multi-user API.
 * Include it in your browser extension to automatically handle the migration.
 */

/**
 * Migration class to handle transitioning to multi-user authentication
 */
class MultiUserMigration {
    /**
     * Initialize the migration helper
     * @param {Object} options Configuration options
     * @param {string} options.storageKey Key to use for storing user ID in localStorage
     * @param {string} options.apiBase Base URL for API calls
     */
    constructor(options = {}) {
        this.storageKey = options.storageKey || 'jira_user_id';
        this.apiBase = options.apiBase || '/api';
        this.logger = options.logger || console;
    }

    /**
     * Ensure a user ID exists in storage or create one
     * @returns {string} The user ID
     */
    ensureUserId() {
        let userId = localStorage.getItem(this.storageKey);

        if (!userId) {
            // Generate a new user ID (UUID v4)
            userId = this._generateUUID();
            this.logger.info(`Generated new user ID: ${userId}`);
            localStorage.setItem(this.storageKey, userId);
        }

        return userId;
    }

    /**
     * Generate a UUID v4
     * @returns {string} A random UUID
     */
    _generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * Update API endpoints to use multi-user versions
     * @param {Object} api The API object to update
     * @returns {Object} Updated API object
     */
    updateApiEndpoints(api) {
        const userId = this.ensureUserId();

        // Create updated API with multi-user endpoints
        const updatedApi = { ...api };

        // Update common methods to include user ID
        const originalFetch = updatedApi.fetch || window.fetch.bind(window);
        updatedApi.fetch = async (url, options = {}) => {
            // Add user_id parameter to URL if it's a Jira API endpoint
            if (url.includes('/api/jira/') || url.includes('/api/auth/')) {
                const separator = url.includes('?') ? '&' : '?';
                url = `${url}${separator}user_id=${userId}`;
            }

            return originalFetch(url, options);
        };

        // Update auth endpoints
        if (updatedApi.auth) {
            const originalLogin = updatedApi.auth.login;
            updatedApi.auth.login = async (...args) => {
                const url = `${this.apiBase}/auth/oauth/v2/login?user_id=${userId}`;
                return originalLogin(url, ...args);
            };

            const originalCheckToken = updatedApi.auth.checkToken;
            updatedApi.auth.checkToken = async (...args) => {
                const url = `${this.apiBase}/auth/oauth/v2/status?user_id=${userId}`;
                return originalFetch(url, ...args);
            };
        }

        // Update Jira endpoints
        if (updatedApi.jira) {
            const originalGetProjects = updatedApi.jira.getProjects;
            updatedApi.jira.getProjects = async (...args) => {
                const url = `${this.apiBase}/jira/v2/projects?user_id=${userId}`;
                return originalFetch(url, ...args);
            };

            const originalGetIssues = updatedApi.jira.getIssues;
            updatedApi.jira.getIssues = async (projectKey, ...args) => {
                const url = `${this.apiBase}/jira/v2/issues?project_key=${projectKey}&user_id=${userId}`;
                return originalFetch(url, ...args);
            };
        }

        return updatedApi;
    }

    /**
     * Check if the multi-user API is available
     * @returns {Promise<boolean>} True if multi-user API is available
     */
    async checkMultiUserAvailable() {
        try {
            const response = await fetch(`${this.apiBase}/health`);
            const data = await response.json();
            return data.multi_user_enabled === true;
        } catch (error) {
            this.logger.error('Error checking multi-user availability:', error);
            return false;
        }
    }

    /**
     * Run the migration
     * @returns {Promise<Object>} Migration result
     */
    async migrate() {
        try {
            // Check if multi-user API is available
            const isMultiUserAvailable = await this.checkMultiUserAvailable();

            if (!isMultiUserAvailable) {
                this.logger.warn('Multi-user API not available, skipping migration');
                return { success: false, reason: 'api_not_available' };
            }

            // Ensure user ID exists
            const userId = this.ensureUserId();

            // Set migration flag
            localStorage.setItem('jira_multi_user_migrated', 'true');

            return {
                success: true,
                userId,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            this.logger.error('Migration failed:', error);
            return {
                success: false,
                error: error.message,
                reason: 'exception'
            };
        }
    }
}

// Export for use in browser extension
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { MultiUserMigration };
} else if (typeof window !== 'undefined') {
    window.MultiUserMigration = MultiUserMigration;
}
