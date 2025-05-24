import os
import sys
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Add app directory to sys.path to allow for absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

try:
    from app.core.database import get_db
    from app.models.token import OAuthToken
    from app.models.user import User
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure you are running this script from the 'python-server' directory,")
    print("or that the 'app' directory is in your PYTHONPATH.")
    sys.exit(1)

# Load environment variables from .env file
load_dotenv()

def handle_logout(user_id):
    """
    Handles the logout process for a user by deleting their OAuth token.
    
    Args:
        user_id (str): The ID of the user to log out
        
    Returns:
        bool: True if the token was found and deleted, False otherwise
    """
    if not user_id:
        print("No user ID provided. Cannot process logout.")
        return False
    
    db = next(get_db())
    try:
        token_to_delete = db.query(OAuthToken).filter(OAuthToken.user_id == user_id).first()

        if token_to_delete:
            print(f"Found token for user_id: {user_id}. Deleting...")
            db.delete(token_to_delete)
            db.commit()
            print(f"Successfully deleted token for user_id: {user_id}")
            return True
        else:
            print(f"No token found for user_id: {user_id}. Nothing to delete.")
            return False

    except Exception as e:
        print(f"An error occurred during logout: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # This allows the script to be run directly for testing
    if len(sys.argv) > 1:
        test_user_id = sys.argv[1]
        print(f"Testing logout for user ID: {test_user_id}")
        result = handle_logout(test_user_id)
        print(f"Logout result: {'Success' if result else 'Failed'}")
    else:
        print("Please provide a user ID as an argument to test the logout functionality.")
