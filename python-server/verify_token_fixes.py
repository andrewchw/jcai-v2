#!/usr/bin/env python
"""
Verify that the OAuth token service fixes have been correctly applied.
This script checks both the backend Python server and the frontend JavaScript code.
"""

import os
import re
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Path to the files to check
OAUTH_SERVICE_PATH = os.path.join('app', 'services', 'oauth_token_service.py')
BACKGROUND_JS_PATH = os.path.join('..', 'edge-extension', 'src', 'js', 'background.js')

def verify_python_fix():
    """Verify that the Python OAuth token service fix has been applied."""
    if not os.path.exists(OAUTH_SERVICE_PATH):
        logger.error(f"Could not find {OAUTH_SERVICE_PATH}")
        return False
    
    with open(OAUTH_SERVICE_PATH, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Check if the fix is applied
    if "_refresh_thread_running" not in content:
        logger.error("Python fix NOT applied: _refresh_thread_running flag not found!")
        return False

    # Check if flag is properly initialized
    if "OAuthTokenService._refresh_thread_running = False" not in content:
        logger.error("Python fix partially applied: flag reset code is missing!")
        return False
        
    logger.info("✓ Python server-side fix properly applied!")
    return True

def verify_js_fix():
    """Verify that the JavaScript background.js fix has been applied."""
    if not os.path.exists(BACKGROUND_JS_PATH):
        logger.error(f"Could not find {BACKGROUND_JS_PATH}")
        return False
    
    with open(BACKGROUND_JS_PATH, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Check for the debounce tracking
    if "lastTokenCheckStart" not in content:
        logger.error("JavaScript fix NOT applied: lastTokenCheckStart tracking not found!")
        return False
    
    # Check for try/catch blocks around interval setup
    if "catch (err) {" not in content or "Failed to start token checking interval" not in content:
        logger.warning("JavaScript fix partially applied: error handling may not be robust.")
    
    logger.info("✓ JavaScript client-side fix properly applied!")
    return True

if __name__ == "__main__":
    # Change directory to the script location to ensure relative paths work
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    logger.info("Verifying OAuth token service fixes...")
    python_fix_ok = verify_python_fix()
    js_fix_ok = verify_js_fix()
    
    if python_fix_ok and js_fix_ok:
        logger.info("All fixes have been properly applied!")
        logger.info("✓ Multiple OAuth token refresh services should now be prevented!")
        sys.exit(0)
    else:
        logger.warning("Some fixes may not be completely applied!")
        logger.warning("Please review the logs above and apply missing fixes.")
        sys.exit(1)
