#!/usr/bin/env python
"""
OAuth Logout Fix Applier

This script adds a POST logout endpoint to the OAuth multi-user API
to fix the compatibility issue with the browser extension.
"""

import os
import re
import shutil
import sys


def add_post_endpoint():
    """Add a POST endpoint for logout to the oauth_multi.py file"""

    # Path to the OAuth multi-user API file
    oauth_file_path = os.path.join("app", "api", "endpoints", "oauth_multi.py")

    if not os.path.exists(oauth_file_path):
        print(f"Error: Could not find OAuth file at {oauth_file_path}")
        return False

    # Read the file content
    with open(oauth_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if POST endpoint already exists
    if re.search(r'@router\.post\(["\']\/logout["\']\)', content):
        print("POST logout endpoint already exists. No changes needed.")
        return True

    # Find the GET logout endpoint
    get_endpoint_match = re.search(r'@router\.get\(["\']\/logout["\']\)', content)
    if not get_endpoint_match:
        print("Error: Could not find GET logout endpoint in oauth_multi.py")
        return False

    # Find the end of the GET logout function
    # This is a bit tricky as we need to count braces to find the matching closing brace
    start_pos = get_endpoint_match.start()

    # Find the function body by starting from the decorator
    current_pos = start_pos
    brace_count = 0
    in_function = False
    end_pos = None

    # Simple state machine to find the closing brace
    for i in range(start_pos, len(content)):
        if content[i] == "{":
            brace_count += 1
            in_function = True
        elif content[i] == "}":
            brace_count -= 1
            if in_function and brace_count == 0:
                end_pos = i + 1
                break

    if end_pos is None:
        # Fallback: look for a line with just a closing brace after the decorator
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if get_endpoint_match.start() < content.find(line):
                if re.match(r"^\s*}\s*$", line):
                    line_start = content.find(line)
                    end_pos = line_start + len(line)
                    break

    if end_pos is None:
        print("Error: Could not find the end of the GET logout function")
        return False

    # Create the POST endpoint code
    post_endpoint = """

@router.post("/logout")
async def logout_post(
    user_id: str,
    db: Session = Depends(get_db)
):
    \"""Logout and invalidate OAuth token for a user via POST request\"""
    # This simply calls the same implementation as the GET endpoint
    return await logout(user_id=user_id, db=db)
"""

    # Insert the POST endpoint after the GET endpoint
    new_content = content[:end_pos] + post_endpoint + content[end_pos:]

    # Backup the original file
    backup_path = oauth_file_path + ".bak"
    shutil.copy2(oauth_file_path, backup_path)
    print(f"Created backup at {backup_path}")

    # Write the updated content
    with open(oauth_file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("Successfully added POST logout endpoint to oauth_multi.py")
    return True


def find_place_manually():
    """Find the right place to add the endpoint and print instructions"""
    oauth_file_path = os.path.join("app", "api", "endpoints", "oauth_multi.py")

    if not os.path.exists(oauth_file_path):
        print(f"Error: Could not find OAuth file at {oauth_file_path}")
        return

    # Read the file content as lines
    with open(oauth_file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    get_endpoint_line = None
    for i, line in enumerate(lines):
        if '@router.get("/logout")' in line:
            get_endpoint_line = i
            break

    if get_endpoint_line is None:
        print("Could not find GET logout endpoint line")
        return

    # Find the end of the function by looking for a closing brace
    function_end_line = None
    for i in range(get_endpoint_line, len(lines)):
        if re.match(r"^\s*}\s*$", lines[i]):
            function_end_line = i
            break

    if function_end_line is None:
        print("Could not find the end of the logout function")
        return

    print(f"\nFound GET logout endpoint at line {get_endpoint_line+1}")
    print(f"Function ends at line {function_end_line+1}")
    print("\nManual Instructions:")
    print(f"1. Open the file: {oauth_file_path}")
    print(
        f"2. Go to line {function_end_line+1} (the closing brace of the GET logout function)"
    )
    print("3. After this line, add the following code:")
    print('\n@router.post("/logout")')
    print("async def logout_post(")
    print("    user_id: str,")
    print("    db: Session = Depends(get_db)")
    print("):")
    print('    """Logout and invalidate OAuth token for a user via POST request"""')
    print("    # This simply calls the same implementation as the GET endpoint")
    print("    return await logout(user_id=user_id, db=db)")


def manual_edit_file():
    """Provide a simple tool to manually edit the file"""
    oauth_file_path = os.path.join("app", "api", "endpoints", "oauth_multi.py")

    if not os.path.exists(oauth_file_path):
        print(f"Error: Could not find OAuth file at {oauth_file_path}")
        return

    # Create a temp file with the POST endpoint
    temp_file = "post_endpoint.py"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(
            """
@router.post("/logout")
async def logout_post(
    user_id: str,
    db: Session = Depends(get_db)
):
    \"""Logout and invalidate OAuth token for a user via POST request\"""
    # This simply calls the same implementation as the GET endpoint
    return await logout(user_id=user_id, db=db)
"""
        )

    print(f"\nCreated temp file with POST endpoint: {temp_file}")
    print("Instructions:")
    print(f"1. Open {oauth_file_path}")
    print("2. Find the GET logout endpoint (@router.get('/logout'))")
    print(
        "3. After the closing brace of that function, paste the contents of post_endpoint.py"
    )
    print("4. Save the file")


def create_background_fix():
    """Create the background_fix.js file in the edge-extension directory"""
    edge_extension_dir = os.path.abspath(os.path.join("..", "edge-extension"))

    if not os.path.exists(edge_extension_dir):
        os.makedirs(edge_extension_dir, exist_ok=True)
        print(f"Created directory: {edge_extension_dir}")

    background_fix_path = os.path.join(edge_extension_dir, "background_fix.js")

    with open(background_fix_path, "w", encoding="utf-8") as f:
        f.write(
            """/**
 * Stop periodic token checking
 */
function stopTokenChecking() {
    console.log('Stopping periodic token checking');
    if (self.tokenCheckIntervalId) {
        clearInterval(self.tokenCheckIntervalId);
        self.tokenCheckIntervalId = null;
    }
}
"""
        )

    print(f"\nCreated background_fix.js at {background_fix_path}")
    print("Instructions:")
    print("1. Add the stopTokenChecking function to your background.js file")
    print("2. Place it before the performLogout function")


def print_instructions():
    """Print final instructions for completing the fix"""
    print("\n=======================")
    print("Logout Fix Instructions")
    print("=======================")
    print("\nTo complete the fix:")
    print("1. Restart your FastAPI server")
    print("2. Update your browser extension's background.js file")
    print("   - Add the stopTokenChecking function from background_fix.js")
    print(
        "   - OR modify the performLogout function to use method: 'GET' instead of 'POST'"
    )
    print("\nAlternative client-side fix:")
    print("In background.js, find the fetch call in performLogout() and change:")
    print("  method: 'POST' to method: 'GET'")


if __name__ == "__main__":
    print("JIRA Chatbot Extension Logout Fix")
    print("=================================")

    # Try automatic fix first
    if add_post_endpoint():
        create_background_fix()
        print_instructions()
    else:
        print("\nAutomatic fix failed. Trying manual approach...")
        find_place_manually()
        manual_edit_file()
        create_background_fix()
        print_instructions()
