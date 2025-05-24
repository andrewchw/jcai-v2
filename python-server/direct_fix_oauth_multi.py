"""
Direct Fix for oauth_multi.py

This script directly edits the oauth_multi.py file to add the POST logout endpoint.
It's a more direct approach than the PowerShell script if you're facing issues.
"""

import os
import sys
import shutil

def add_post_endpoint():
    """Add the POST endpoint for logout to oauth_multi.py"""
    oauth_file_path = os.path.join('app', 'api', 'endpoints', 'oauth_multi.py')
    
    if not os.path.exists(oauth_file_path):
        print(f"Error: Cannot find {oauth_file_path}")
        return False
    
    # Read the file content
    with open(oauth_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Look for the GET logout endpoint
    get_logout_index = -1
    for i, line in enumerate(lines):
        if '@router.get("/logout")' in line:
            get_logout_index = i
            break
    
    if get_logout_index == -1:
        print("Error: Could not find GET logout endpoint")
        return False
    
    # Find the end of the function (looking for a closing brace)
    function_end_index = -1
    brace_count = 0
    in_function = False
    
    for i in range(get_logout_index, len(lines)):
        line = lines[i]
        
        # Count opening braces
        brace_count += line.count('{')
        
        # We've found the function start once we see the first brace
        if not in_function and '{' in line:
            in_function = True
        
        # Count closing braces
        brace_count -= line.count('}')
        
        # If we've found the matching closing brace, this is the end
        if in_function and brace_count <= 0 and '}' in line:
            function_end_index = i
            break
    
    if function_end_index == -1:
        print("Error: Could not find the end of the GET logout function")
        return False
    
    # Create the POST endpoint code
    post_endpoint = [
        '\n',
        '@router.post("/logout")\n',
        'async def logout_post(\n',
        '    user_id: str,\n',
        '    db: Session = Depends(get_db)\n',
        '):\n',
        '    """Logout and invalidate OAuth token for a user via POST request"""\n',
        '    # This simply calls the same implementation as the GET endpoint\n',
        '    return await logout(user_id=user_id, db=db)\n'
    ]
    
    # Insert the POST endpoint after the GET endpoint function
    new_lines = lines[:function_end_index + 1] + post_endpoint + lines[function_end_index + 1:]
    
    # Create a backup of the original file
    backup_path = f"{oauth_file_path}.bak.{int(__import__('time').time())}"
    shutil.copy2(oauth_file_path, backup_path)
    print(f"Created backup at {backup_path}")
    
    # Write the modified file
    with open(oauth_file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"Successfully added POST logout endpoint to {oauth_file_path}")
    return True

if __name__ == "__main__":
    print("JIRA Extension Logout Fix - Direct Implementation")
    print("================================================")
    
    try:
        result = add_post_endpoint()
        if result:
            print("\nFix applied successfully!")
            print("Please restart your FastAPI server for the changes to take effect.")
            print("\nRemember to also add the stopTokenChecking function to your background.js file.")
            print("See edge-extension/background_fix.js for the code to add.")
        else:
            print("\nFailed to apply the fix automatically.")
            print("Please check the LOGOUT_FIX_GUIDE.md for manual fix instructions.")
    except Exception as e:
        print(f"Error: {e}")
        print("Please check the LOGOUT_FIX_GUIDE.md for manual fix instructions.")
