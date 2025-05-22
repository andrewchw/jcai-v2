// This is a validation script for the OAuth fixes
// It checks that all references to window have been properly replaced with self in the background.js file
// and verifies that the correct OAuth endpoints are being used

const fs = require('fs');
const path = require('path');

// Path to background.js
const backgroundJsPath = path.join(__dirname, 'src', 'js', 'background.js');

// Read background.js
try {
    const content = fs.readFileSync(backgroundJsPath, 'utf8');

    // Check for any remaining window references
    const windowReferences = (content.match(/window\./g) || []).length;
    console.log(`Found ${windowReferences} references to window.`);

    // Check for self references (should have replaced window)
    const selfReferences = (content.match(/self\./g) || []).length;
    console.log(`Found ${selfReferences} references to self.`);

    // Check for correct token status endpoint
    const hasCorrectEndpoint = content.includes('/auth/oauth/v2/token/status');
    console.log(`Correct token status endpoint: ${hasCorrectEndpoint ? 'YES' : 'NO'}`);

    // Check for user ID inclusion in API calls
    const hasUserIdParam = content.includes('user_id=${encodeURIComponent(tokenState.userId)}');
    console.log(`User ID parameter in API calls: ${hasUserIdParam ? 'YES' : 'NO'}`);

    // Check for auth status notification function
    const hasNotifyFunction = content.includes('async function notifySidebarsAboutAuth');
    console.log(`Auth status notification function: ${hasNotifyFunction ? 'YES' : 'NO'}`);

    console.log('\nValidation complete. If all checks show proper values, the OAuth fixes are in place.');
} catch (error) {
    console.error('Error reading or validating background.js:', error);
}
