"""
Fix for multiple OAuth token background refresh services.

This script adds a check to the OAuth token service to prevent multiple background refresh
services from being started for the same token.
"""

import os
import sys
import re

# Path to the OAuth token service file
TOKEN_SERVICE_PATH = os.path.join('app', 'services', 'oauth_token_service.py')

def fix_token_service():
    """Add singleton pattern to token refresh service to prevent multiple instances."""
    
    if not os.path.exists(TOKEN_SERVICE_PATH):
        print(f"Error: Could not find {TOKEN_SERVICE_PATH}")
        return False
    
    with open(TOKEN_SERVICE_PATH, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Check if the file already has the singleton check
    if "_refresh_thread_running" in content:
        print("Singleton pattern already exists in the file.")
        return True    # Add class variable to track if refresh thread is running
    class_pattern = r'class OAuthTokenService:'
    class_match = re.search(class_pattern, content, re.DOTALL)
    
    if not class_match:
        print("Could not find OAuthTokenService class definition.")
        return False
    
    # Add class variable after class definition    class_end_pos = class_match.end()
    modified_content = content[:class_end_pos] + "\n    # Class variable to track if refresh thread is running\n    _refresh_thread_running = False\n" + content[class_end_pos:]
    
    # Find the start_background_refresh method
    background_refresh_pattern = r'def start_background_refresh\(self.*?\):'
    background_refresh_match = re.search(background_refresh_pattern, modified_content, re.DOTALL)
    
    if not background_refresh_match:
        print("Could not find start_background_refresh method.")
        return False
    
    # Add check at the beginning of the method
    method_start_pos = background_refresh_match.end()
    indent = "        "  # Assuming standard 4-space indentation
    
    singleton_check = f"\n{indent}# Prevent multiple refresh threads from starting\n{indent}if OAuthTokenService._refresh_thread_running:\n{indent}    logger.info(\"Background refresh thread already running, not starting another one\")\n{indent}    return\n{indent}OAuthTokenService._refresh_thread_running = True"
    
    modified_content = modified_content[:method_start_pos] + singleton_check + modified_content[method_start_pos:]
    
    # Add cleanup in the _background_refresh_task method for when thread ends
    task_pattern = r'def _background_refresh_task\(self.*?\):'
    task_match = re.search(task_pattern, modified_content, re.DOTALL)
    
    if task_match:
        # Find the end of the method (look for the next def or end of file)
        next_def_match = re.search(r'(\n\s*def\s+|$)', modified_content[task_match.end():], re.DOTALL)
        if next_def_match:
            task_end_pos = task_match.end() + next_def_match.start()
              # Add cleanup before the end of the method
            cleanup_code = f"\n{indent}# Reset the running flag when thread exits\n{indent}OAuthTokenService._refresh_thread_running = False"
            modified_content = modified_content[:task_end_pos] + cleanup_code + modified_content[task_end_pos:]
    
    # Write back the modified file
    with open(TOKEN_SERVICE_PATH, 'w', encoding='utf-8') as file:
        file.write(modified_content)
    
    print(f"Successfully updated {TOKEN_SERVICE_PATH} with singleton pattern.")
    return True

if __name__ == "__main__":
    # Change directory to the server root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    if fix_token_service():
        print("OAuth token service fixed successfully. This should prevent multiple background refresh services.")
    else:
        print("Failed to apply the fix. Please check the script and try again.")
