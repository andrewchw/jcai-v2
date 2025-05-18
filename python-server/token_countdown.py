#!/usr/bin/env python3
"""
OAuth Token Countdown Timer

This script provides a real-time countdown display showing when the OAuth token will expire
and when it will be automatically refreshed (60 seconds before expiration).

Press 'r' to manually refresh the token at any time.
Press 'Ctrl+C' to exit.
"""

import os
import json
import sys
import time
import logging
import threading
import requests
import msvcrt  # For Windows keyboard input
from datetime import datetime, timedelta
from dotenv import load_dotenv
from requests_oauthlib import OAuth2Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# OAuth2 settings from environment variables
TOKEN_FILE = os.getenv("TOKEN_FILE", "oauth_token.json")
CLIENT_ID = os.getenv("JIRA_OAUTH_CLIENT_ID")
CLIENT_SECRET = os.getenv("JIRA_OAUTH_CLIENT_SECRET")
TOKEN_URL = "https://auth.atlassian.com/oauth/token"
RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"

# Global flag for refresh status notification
refresh_status = {"refreshing": False, "message": ""}

def load_token():
    """Load OAuth token from file"""
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load token: {str(e)}")
    return None

def save_token(token):
    """Save OAuth token to file"""
    try:
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token, f)
        return True
    except Exception as e:
        logger.error(f"Could not save token: {str(e)}")
        return False

def refresh_token(token):
    """Refresh the OAuth 2.0 token if it's expired"""
    if not token or 'refresh_token' not in token:
        refresh_status["message"] = "❌ No refresh token available"
        refresh_status["refreshing"] = False
        return token
        
    try:
        refresh_status["refreshing"] = True
        refresh_status["message"] = "🔄 Refreshing token..."
        
        # Create a new OAuth2 session
        oauth = OAuth2Session(CLIENT_ID, token=token)
        
        # Refresh the token
        new_token = oauth.refresh_token(
            TOKEN_URL,
            refresh_token=token['refresh_token'],
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )
        
        # Calculate new expiration
        if 'expires_at' in new_token:
            new_expires_at = new_token['expires_at']
            new_expiry = datetime.fromtimestamp(new_expires_at)
            refresh_status["message"] = f"✅ Token refreshed! New expiration: {new_expiry.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Save the new token
        save_token(new_token)
        refresh_status["refreshing"] = False
        return new_token
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        refresh_status["message"] = f"❌ Error refreshing token: {str(e)}"
        refresh_status["refreshing"] = False
        return token

def format_time_remaining(seconds):
    """Format seconds into a human-readable time string"""
    if seconds < 0:
        return "Expired"
    
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def clear_console():
    """Clear the console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def keyboard_monitor():
    """Monitor keyboard input for refresh command"""
    while True:
        try:
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8').lower()
                if key == 'r':
                    token = load_token()
                    if token and not refresh_status["refreshing"]:
                        # Start refresh in a separate thread
                        threading.Thread(target=refresh_token, args=(token,)).start()
            time.sleep(0.1)
        except Exception:
            pass

def display_countdown():
    """Display a real-time countdown to token expiration and refresh"""
    # Start keyboard monitor in a separate thread
    threading.Thread(target=keyboard_monitor, daemon=True).start()
    
    try:
        while True:
            clear_console()
            print("\n=== OAuth Token Countdown ===\n")
            
            # Load token (to get updated values if refreshed externally)
            token = load_token()
            
            if not token:
                print("❌ No OAuth token found")
                print(f"   Expected location: {os.path.abspath(TOKEN_FILE)}")
                print("\nPlease run the OAuth flow to obtain a token:")
                print("   python jira_oauth2_example.py")
                print("   Then visit http://localhost:8000/login")
                break
                
            # Get current time
            current_time = datetime.now().timestamp()
            
            # Check expires_at
            if 'expires_at' in token:
                expires_at = token['expires_at']
                time_to_expiry = expires_at - current_time
                time_to_refresh = time_to_expiry - 60  # 60 seconds before expiry
                
                # Calculate progress bars (20 characters wide)
                expiry_progress = min(1.0, max(0, 1 - time_to_expiry / 3600))  # Assuming 1hr token life
                refresh_progress = min(1.0, max(0, 1 - time_to_refresh / 3600))  # Assuming 1hr token life
                
                expiry_bar = '█' * int(expiry_progress * 20) + '░' * (20 - int(expiry_progress * 20))
                refresh_bar = '█' * int(refresh_progress * 20) + '░' * (20 - int(refresh_progress * 20))
                
                # Format display
                print(f"Token File: {os.path.abspath(TOKEN_FILE)}")
                print(f"Access Token: {token.get('access_token', 'Unknown')[:10]}...")
                
                # Show refresh token status
                if 'refresh_token' in token:
                    print(f"Refresh Token: {token.get('refresh_token', 'Unknown')[:5]}...")
                    print("♻️ Auto-renewal: ✅ Enabled (token can be refreshed)")
                else:
                    print("♻️ Auto-renewal: ❌ Disabled (no refresh token)")
                
                print("\n=== Expiration Countdown ===")
                if time_to_expiry <= 0:
                    print("⚠️ TOKEN EXPIRED! ⚠️")
                    print("Run /projects or /issues endpoint to trigger a refresh")
                else:
                    # Expiry countdown
                    print(f"Expires in: {format_time_remaining(time_to_expiry)}")
                    print(f"[{expiry_bar}] {int(expiry_progress * 100)}%")
                    
                    # Refresh countdown                print("\n=== Auto-Refresh Countdown ===")
                if time_to_refresh <= 0:
                    print("🔄 Token eligible for refresh NOW!")
                    print("Run /projects or /issues endpoint to trigger a refresh")
                else:
                    print(f"Auto-refresh in: {format_time_remaining(time_to_refresh)}")
                    print(f"[{refresh_bar}] {int(refresh_progress * 100)}%")
                
                # Show refresh status if active
                if refresh_status["message"]:
                    print(f"\n{refresh_status['message']}")
                    if not refresh_status["refreshing"]:
                        # Clear message after 5 seconds if not refreshing
                        if not hasattr(display_countdown, "message_time"):
                            display_countdown.message_time = time.time()
                        elif time.time() - display_countdown.message_time > 5:
                            refresh_status["message"] = ""
                            display_countdown.message_time = 0
                
                print("\nPress 'r' to refresh token manually")
                print("Press Ctrl+C to exit")
                
            else:
                print("⚠️ Token has no expiration information!")
                print("This token may not refresh properly.")
                break
                
            # Update every second
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nCountdown stopped by user.")
        return

if __name__ == "__main__":
    display_countdown()
