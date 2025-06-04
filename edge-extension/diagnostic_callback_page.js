/**
 * Diagnostic script for JIRA Chatbot Assistant OAuth callback page
 * This script helps identify issues with the OAuth callback page
 *
 * Usage:
 * 1. Load this script in the browser console when on the callback page
 * 2. Run diagCallback() to see diagnostic information
 */

// Global diagnostic data collection
let callbackDiagnostics = {
    startTime: Date.now(),
    renderTimes: [],
    urlChanges: [],
    errors: [],
    successParams: null,
    elementVisibility: {}
};

/**
 * Main diagnostic function - call this from the console on the callback page
 */
function diagCallback() {
    console.group('OAuth Callback Page Diagnostics');

    // Capture current URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const currentUrl = window.location.href;

    console.log('Current URL:', currentUrl);
    console.log('Time on page:', Date.now() - callbackDiagnostics.startTime, 'ms');

    // Log all URL parameters
    console.log('URL Parameters:');
    const params = {};
    for (const [key, value] of urlParams.entries()) {
        params[key] = value;
        console.log(`  ${key}: ${value}`);
    }

    // Check for success indicator
    const success = urlParams.get('success');
    const code = urlParams.get('code');
    const error = urlParams.get('error');
    const state = urlParams.get('state');
    const userId = urlParams.get('user_id');

    console.log('Success:', success);
    console.log('Authorization Code:', code ? 'Present' : 'Missing');
    console.log('Error:', error || 'None');
    console.log('State:', state || 'None');
    console.log('User ID:', userId || 'None');

    // Analyze success criteria
    const hasCode = !!code;
    const isCallback = currentUrl.includes('/callback');
    const hasError = !!error;
    const implicitSuccess = (hasCode && isCallback) && !hasError;
    const explicitSuccess = (success === 'true') || implicitSuccess;

    console.log('Success Criteria Analysis:');
    console.log('  Has Code:', hasCode);
    console.log('  Is Callback URL:', isCallback);
    console.log('  Has Error:', hasError);
    console.log('  Implicit Success:', implicitSuccess);
    console.log('  Explicit Success:', explicitSuccess);

    // Check DOM for success/error messages
    const successElement = document.querySelector('.success-message, .auth-success, #success');
    const errorElement = document.querySelector('.error-message, .auth-error, #error');

    console.log('DOM Elements:');
    console.log('  Success Element:', successElement ? 'Present' : 'Missing');
    console.log('  Error Element:', errorElement ? 'Present' : 'Missing');

    // Record diagnostic data
    callbackDiagnostics.successParams = {
        success,
        hasCode,
        isCallback,
        hasError,
        implicitSuccess,
        explicitSuccess
    };

    callbackDiagnostics.elementVisibility = {
        successElement: !!successElement,
        errorElement: !!errorElement
    };

    console.log('URL Changes History:', callbackDiagnostics.urlChanges);
    console.log('Errors:', callbackDiagnostics.errors);

    // Suggestions based on diagnostics
    console.log('Diagnostic Suggestions:');
    if (!explicitSuccess && !hasError) {
        console.log('- The callback page lacks clear success indicators. Consider adding explicit success=true parameter.');
    }
    if (!successElement && explicitSuccess) {
        console.log('- Success detected but no success message is displayed in the DOM. Check HTML templates.');
    }
    if (!errorElement && hasError) {
        console.log('- Error detected but no error message is displayed in the DOM. Check HTML templates.');
    }
    if (callbackDiagnostics.renderTimes.length === 0) {
        console.log('- No render events detected. Page may not be updating dynamically.');
    }

    console.groupEnd();

    // Return diagnostic data for further analysis
    return {
        url: currentUrl,
        params,
        successCriteria: {
            hasCode,
            isCallback,
            hasError,
            implicitSuccess,
            explicitSuccess
        },
        elements: {
            successElement: !!successElement,
            errorElement: !!errorElement
        },
        history: {
            urlChanges: callbackDiagnostics.urlChanges,
            errors: callbackDiagnostics.errors,
            renderTimes: callbackDiagnostics.renderTimes
        }
    };
}

// Monitor URL changes
const originalPushState = history.pushState;
history.pushState = function () {
    callbackDiagnostics.urlChanges.push({
        time: Date.now() - callbackDiagnostics.startTime,
        url: arguments[2]
    });
    return originalPushState.apply(this, arguments);
};

const originalReplaceState = history.replaceState;
history.replaceState = function () {
    callbackDiagnostics.urlChanges.push({
        time: Date.now() - callbackDiagnostics.startTime,
        url: arguments[2],
        type: 'replace'
    });
    return originalReplaceState.apply(this, arguments);
};

// Monitor errors
window.addEventListener('error', function (event) {
    callbackDiagnostics.errors.push({
        time: Date.now() - callbackDiagnostics.startTime,
        message: event.message,
        source: event.filename,
        line: event.lineno,
        column: event.colno
    });
});

// Track render times
const originalSetTimeout = window.setTimeout;
window.setTimeout = function (callback, delay) {
    if (delay < 100) { // Likely a render or animation frame
        callbackDiagnostics.renderTimes.push(Date.now() - callbackDiagnostics.startTime);
    }
    return originalSetTimeout.apply(this, arguments);
};

console.log('OAuth callback diagnostic tools loaded. Run diagCallback() to see diagnostic information.');
