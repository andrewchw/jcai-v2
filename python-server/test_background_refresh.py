#!/usr/bin/env python3
"""
OAuth Token Background Refresh Test Script

This script tests the background refresh implementation by:
1. Loading the current token
2. Monitoring its status in real-time
3. Testing manual refresh functionality
4. Displaying token service statistics

Usage:
    python test_background_refresh.py
"""

import os
import time
import json
import logging
import sys
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import services
try:
    from app.services.jira_service import jira_service
    from app.services.oauth_token_service import TokenRefreshEvent
except ImportError:
    logger.error("Failed to import required modules. Make sure you're running from the python-server directory.")
    sys.exit(1)

# ANSI color codes for terminal output
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"

# Test event handler to display events in real-time
def test_event_handler(event: TokenRefreshEvent):
    """Handle token events with color coding"""
    if event.event_type == "refresh":
        color = Colors.GREEN
    elif event.event_type == "error":
        color = Colors.RED
    elif event.event_type == "warning":
        color = Colors.YELLOW
    else:
        color = Colors.BLUE
    
    print(f"{color}{event.timestamp}: [{event.event_type.upper()}] {event.message}{Colors.END}")

def clear_screen():
    """Clear terminal screen"""
    os.system("cls" if os.name == "nt" else "clear")

def display_token_info(token):
    """Display formatted token information"""
    if not token:
        print(f"{Colors.RED}No token available{Colors.END}")
        return
    
    # Mask sensitive parts
    masked_token = token.copy()
    if "access_token" in masked_token:
        token_val = masked_token["access_token"]
        masked_token["access_token"] = token_val[:5] + "..." + token_val[-5:] if len(token_val) > 10 else "***"
    if "refresh_token" in masked_token:
        token_val = masked_token["refresh_token"]
        masked_token["refresh_token"] = token_val[:5] + "..." + token_val[-5:] if len(token_val) > 10 else "***"
    
    # Calculate expiration information if available
    if 'expires_at' in token:
        expires_at = token['expires_at']
        current_time = datetime.now().timestamp()
        time_remaining = expires_at - current_time
        expiry_time = datetime.fromtimestamp(expires_at)
        
        if time_remaining <= 0:
            status = f"{Colors.RED}EXPIRED{Colors.END}"
            expires_text = f"Expired {timedelta(seconds=int(abs(time_remaining)))} ago"
        else:
            if time_remaining < 600:  # Less than 10 minutes
                status = f"{Colors.YELLOW}EXPIRING SOON{Colors.END}"
            else:
                status = f"{Colors.GREEN}ACTIVE{Colors.END}"
            expires_text = f"Expires in {timedelta(seconds=int(time_remaining))}"
        
        print(f"{Colors.BOLD}Token Status:{Colors.END} {status}")
        print(f"{Colors.BOLD}Expiration:{Colors.END} {expires_text} ({expiry_time.strftime('%Y-%m-%d %H:%M:%S')})")
    
    print(f"{Colors.BOLD}Token Details:{Colors.END}")
    for key, value in masked_token.items():
        if key != "expires_at":  # Already displayed in a more readable format
            print(f"  {key}: {value}")

def display_service_stats():
    """Display token service statistics"""
    if not jira_service._token_service:
        print(f"{Colors.RED}Token service not initialized{Colors.END}")
        return
    
    stats = jira_service._token_service.stats
    
    print(f"{Colors.BOLD}Token Service Statistics:{Colors.END}")
    print(f"  Refreshes Attempted: {stats['refreshes_attempted']}")
    print(f"  Refreshes Succeeded: {stats['refreshes_succeeded']}")
    print(f"  Refreshes Failed: {stats['refreshes_failed']}")
    
    if stats["last_refresh"]:
        print(f"  Last Refresh: {stats['last_refresh'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    if stats["next_scheduled_check"]:
        next_check = stats["next_scheduled_check"]
        now = datetime.now()
        if next_check > now:
            wait_time = (next_check - now).total_seconds()
            print(f"  Next Check: {int(wait_time)} seconds from now ({next_check.strftime('%Y-%m-%d %H:%M:%S')})")
        else:
            print(f"  Next Check: imminent")

def main():
    """Main test function"""
    if not jira_service._token_service:
        logger.error("Token service not initialized. Check your OAuth configuration.")
        return
    
    try:
        # Add our test event handler
        jira_service._token_service.add_event_handler(test_event_handler)
        
        # Initial token check
        token = jira_service.get_oauth2_token()
        if not token:
            logger.error("No token available. Please authenticate first.")
            return
        
        # Main display loop
        try:
            while True:
                clear_screen()
                print(f"{Colors.BOLD}OAUTH TOKEN BACKGROUND REFRESH TEST{Colors.END}")
                print("=" * 50)
                print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("-" * 50)
                
                # Reload token for latest info
                token = jira_service.get_oauth2_token()
                display_token_info(token)
                
                print("-" * 50)
                display_service_stats()
                print("\n" + "-" * 50)
                print(f"{Colors.BOLD}Jira Connectivity Test:{Colors.END}")
                try:
                    # Test if connected to Jira
                    is_connected = jira_service.is_connected()
                    if is_connected:
                        print(f"{Colors.GREEN}✓ Connected to Jira{Colors.END}")
                    else:
                        print(f"{Colors.RED}× Not connected to Jira{Colors.END}")
                except Exception as e:
                    print(f"{Colors.RED}× Error checking Jira connection: {str(e)}{Colors.END}")
                
                print("\n" + "-" * 50)
                print(f"{Colors.BOLD}Commands:{Colors.END}")
                print("  r - Force refresh token")
                print("  j - Test Jira API with projects retrieval")
                print("  q - Quit")
                print("-" * 50)                # Non-blocking input check with timeout
                # Use a different approach for Windows since select.select() doesn't work well with stdin on Windows
                if os.name == 'nt':  # Windows
                    import msvcrt
                    # Check if there's a key press available
                    if msvcrt.kbhit():
                        key = msvcrt.getch().decode('utf-8').lower()
                        if key == 'q':
                            break
                        elif key == 'r':
                            print(f"{Colors.YELLOW}Forcing token refresh...{Colors.END}")
                            new_token = jira_service.refresh_oauth2_token(force=True)
                            if new_token:
                                print(f"{Colors.GREEN}Token refreshed successfully!{Colors.END}")
                            else:
                                print(f"{Colors.RED}Token refresh failed.{Colors.END}")
                            
                            # Wait to see the result
                            time.sleep(2)
                        elif key == 'j':
                            print(f"{Colors.YELLOW}Testing Jira API by retrieving projects...{Colors.END}")
                            try:
                                projects = jira_service.get_projects()
                                print(f"{Colors.GREEN}Successfully retrieved {len(projects)} projects:{Colors.END}")
                                for i, project in enumerate(projects[:5]):  # Show first 5 projects
                                    print(f"  {i+1}. {project['name']} ({project['key']})")
                                if len(projects) > 5:
                                    print(f"  ... and {len(projects) - 5} more")
                            except Exception as e:
                                print(f"{Colors.RED}Error retrieving Jira projects: {str(e)}{Colors.END}")
                            
                            # Wait to see the result
                            time.sleep(5)
                else:  # Unix-based systems
                    import select
                    rlist, _, _ = select.select([sys.stdin], [], [], 1)
                    
                    if rlist:
                        command = sys.stdin.readline().strip().lower()
                        if command == 'q':
                            break
                        elif command == 'r':
                            print(f"{Colors.YELLOW}Forcing token refresh...{Colors.END}")
                            new_token = jira_service.refresh_oauth2_token(force=True)
                            if new_token:
                                print(f"{Colors.GREEN}Token refreshed successfully!{Colors.END}")
                            else:
                                print(f"{Colors.RED}Token refresh failed.{Colors.END}")
                            
                            # Wait to see the result
                            time.sleep(2)
                        elif command == 'j':
                            print(f"{Colors.YELLOW}Testing Jira API by retrieving projects...{Colors.END}")
                            try:
                                projects = jira_service.get_projects()
                                print(f"{Colors.GREEN}Successfully retrieved {len(projects)} projects:{Colors.END}")
                                for i, project in enumerate(projects[:5]):  # Show first 5 projects
                                    print(f"  {i+1}. {project['name']} ({project['key']})")
                                if len(projects) > 5:
                                    print(f"  ... and {len(projects) - 5} more")
                            except Exception as e:
                                print(f"{Colors.RED}Error retrieving Jira projects: {str(e)}{Colors.END}")
                            
                            # Wait to see the result
                            time.sleep(5)
                
                # Wait before refreshing display
                time.sleep(1)
        
        except KeyboardInterrupt:
            print("\nExiting...")
        
    finally:
        # Cleanup
        if jira_service._token_service:
            print("Stopping token service...")
            jira_service.stop_token_service()

if __name__ == "__main__":
    main()
