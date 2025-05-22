\
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Add app directory to sys.path to allow for absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

try:
    from app.core.database import get_db, Base, engine
    from app.models.token import OAuthToken
    from app.models.user import User  # <--- Add this import
    from app.core.config import settings # To ensure DATABASE_URL is loaded
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure you are running this script from the 'python-server' directory,")
    print("or that the 'app' directory is in your PYTHONPATH.")
    sys.exit(1)

# Load environment variables from .env file
# This will load JIRA_TOKEN_ENCRYPTION_KEY and DATABASE_URL
load_dotenv()

USER_ID_TO_DELETE = "edge-1747926342290-0o8cbiri" # The user ID with the problematic token

def cleanup_token():
    db: Session = next(get_db())
    try:
        token_to_delete = db.query(OAuthToken).filter(OAuthToken.user_id == USER_ID_TO_DELETE).first()

        if token_to_delete:
            print(f"Found token for user_id: {USER_ID_TO_DELETE}. Deleting...")
            db.delete(token_to_delete)
            db.commit()
            print(f"Successfully deleted token for user_id: {USER_ID_TO_DELETE}")
        else:
            print(f"No token found for user_id: {USER_ID_TO_DELETE}. Nothing to delete.")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print(f"Attempting to delete token for user: {USER_ID_TO_DELETE} from database: {settings.DATABASE_URL}")
    # Ensure the JIRA_TOKEN_ENCRYPTION_KEY is loaded if models.token tries to use it,
    # though for deletion it's not strictly necessary for decryption.
    encryption_key = os.getenv("JIRA_TOKEN_ENCRYPTION_KEY")
    if not encryption_key:
        print("WARNING: JIRA_TOKEN_ENCRYPTION_KEY is not set in the environment.")
    else:
        print("JIRA_TOKEN_ENCRYPTION_KEY is loaded.")
        
    cleanup_token()
