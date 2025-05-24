#!/usr/bin/env python
"""
Fix for multiple OAuth token background refresh services.

This script adds a check to the OAuth token service to prevent multiple background refresh
services from being started for the same token.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)

# Path to the OAuth token service file
TOKEN_SERVICE_PATH = os.path.join('app', 'services', 'oauth_token_service.py')

def fix_token_service():
    """Add singleton pattern to token refresh service to prevent multiple instances."""
    
    if not os.path.exists(TOKEN_SERVICE_PATH):
        logger.error(f"Could not find {TOKEN_SERVICE_PATH}")
        return False
    
    with open(TOKEN_SERVICE_PATH, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Check if the file already has the singleton check
    if "_refresh_thread_running" in content:
        logger.info("Singleton pattern already exists in the file.")
        return True
    
    # Find the class definition
    class_def = "class OAuthTokenService:"
    if class_def not in content:
        logger.error("Could not find OAuthTokenService class definition.")
        return False
    
    # Add class variable
    class_def_pos = content.find(class_def) + len(class_def)
    modified_content = content[:class_def_pos] + "\n    # Class-level flag to track if any refresh thread is running\n    _refresh_thread_running = False" + content[class_def_pos:]
    
    # Find the start method
    start_method = "def start(self):"
    start_pos = modified_content.find(start_method)
    if start_pos == -1:
        logger.error("Could not find start method.")
        return False
    
    # Find where the method body starts
    start_method_body_pos = modified_content.find(":", start_pos) + 1
    
    # Add singleton check
    singleton_check = """
        # Class-level check to prevent multiple instances across different objects
        if OAuthTokenService._refresh_thread_running:
            logger.warning("Another OAuth token refresh service is already running")
            return
            """
    
    modified_content = modified_content[:start_method_body_pos] + singleton_check + modified_content[start_method_body_pos:]
    
    # Find where the thread is started
    thread_start = "self._refresh_thread.start()"
    thread_start_pos = modified_content.find(thread_start)
    if thread_start_pos == -1:
        logger.error("Could not find thread start call.")
        return False
    
    # Add flag setting
    thread_start_end_pos = thread_start_pos + len(thread_start)
    thread_flag_set = "\n        # Set the running flag\n        OAuthTokenService._refresh_thread_running = True"
    
    modified_content = modified_content[:thread_start_end_pos] + thread_flag_set + modified_content[thread_start_end_pos:]
    
    # Find the stop method
    stop_method = "def stop(self):"
    stop_pos = modified_content.find(stop_method)
    if stop_pos == -1:
        logger.error("Could not find stop method.")
        return False
    
    # Find where the method body starts
    stop_method_body_pos = modified_content.find(":", stop_pos) + 1
    
    # Add flag reset in stop method
    flag_reset = """
        # Reset the class-level running flag when stopping
        OAuthTokenService._refresh_thread_running = False
        """
    
    modified_content = modified_content[:stop_method_body_pos] + flag_reset + modified_content[stop_method_body_pos:]
    
    # Find the background refresh loop
    refresh_loop = "def _background_refresh_loop(self):"
    refresh_loop_pos = modified_content.find(refresh_loop)
    if refresh_loop_pos == -1:
        logger.error("Could not find _background_refresh_loop method.")
        return False
    
    # Find where the method body starts
    refresh_loop_body_pos = modified_content.find(":", refresh_loop_pos) + 1
    
    # Add try block at the beginning
    try_block = """
        # Make sure we reset the running flag when this method exits
        try:"""
    
    modified_content = modified_content[:refresh_loop_body_pos] + try_block + modified_content[refresh_loop_body_pos:]
    
    # Find where the refresh loop ends
    refresh_end_log = 'logger.info("Background refresh loop ended")'
    refresh_end_pos = modified_content.find(refresh_end_log)
    if refresh_end_pos == -1:
        logger.warning("Could not find refresh loop end log message. Will attempt backup approach.")
        # Try to find a location near the end of the method to add the reset
        # This is a fallback strategy
        next_method_pos = modified_content.find("def ", refresh_loop_pos + 10)
        if next_method_pos != -1:
            # Add before the next method, with appropriate indentation
            flag_reset_fallback = "\n        # Reset the class-level running flag\n        OAuthTokenService._refresh_thread_running = False\n"
            modified_content = modified_content[:next_method_pos] + flag_reset_fallback + modified_content[next_method_pos:]
        else:
            logger.error("Could not find a good place to add flag reset at end of refresh loop.")
            return False
    else:
        # Add after the log message
        refresh_end_pos += len(refresh_end_log)
        reset_at_end = "\n            # Reset the class-level running flag\n            OAuthTokenService._refresh_thread_running = False"
        modified_content = modified_content[:refresh_end_pos] + reset_at_end + modified_content[refresh_end_pos:]
    
    # Find exception handling
    except_pos = modified_content.find("except Exception as e:", refresh_loop_pos)
    if except_pos != -1:
        # Find end of exception handler
        next_line_pos = modified_content.find("\n", except_pos + 20)
        if next_line_pos != -1:
            # Add reset in exception handler too
            except_reset = "\n            # Reset the running flag even if there's an exception\n            OAuthTokenService._refresh_thread_running = False"
            modified_content = modified_content[:next_line_pos] + except_reset + modified_content[next_line_pos:]
    else:
        # Add exception handling if not found
        refresh_except_pos = modified_content.find("def ", refresh_loop_pos + 10)
        if refresh_except_pos != -1:
            # Add before the next method
            except_block = """
        except Exception as e:
            logger.error("Error in background refresh loop: %s", e)
            # Reset the running flag even if there's an exception
            OAuthTokenService._refresh_thread_running = False
            
"""
            modified_content = modified_content[:refresh_except_pos] + except_block + modified_content[refresh_except_pos:]
    
    # Write back the modified file
    with open(TOKEN_SERVICE_PATH, 'w', encoding='utf-8') as file:
        file.write(modified_content)
    
    logger.info(f"Successfully updated {TOKEN_SERVICE_PATH} with singleton pattern.")
    return True

if __name__ == "__main__":
    # Change directory to the script location to ensure relative paths work
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    try:
        if fix_token_service():
            logger.info("OAuth token service fixed successfully. This should prevent multiple background refresh services.")
            sys.exit(0)
        else:
            logger.error("Failed to apply the fix. Please check the script and try again.")
            sys.exit(1)
    except Exception as e:
        logger.exception(f"Error applying token service fix: {e}")
        sys.exit(1)
