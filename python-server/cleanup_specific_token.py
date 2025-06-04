import os
import sys

from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Add app directory to sys.path to allow for absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

try:
    from app.core.config import settings  # To ensure DATABASE_URL is loaded
    from app.core.database import Base, engine, get_db
    from app.models.token import OAuthToken
    from app.models.user import User
except ImportError as e:
    print(f"Error importing modules: {e}")
    print(
        "Please ensure you are running this script from the 'python-server' directory,"
    )
    print("or that the 'app' directory is in your PYTHONPATH.")
    sys.exit(1)

# Load environment variables from .env file
# This will load JIRA_TOKEN_ENCRYPTION_KEY and DATABASE_URL
load_dotenv()


def cleanup_token(user_id: str) -> bool:
    """
    Delete a token for a specific user ID

    Args:
        user_id (str): The user ID to delete the token for

    Returns:
        bool: True if a token was found and deleted, False otherwise
    """
    db: Session = next(get_db())
    try:
        token_to_delete = (
            db.query(OAuthToken).filter(OAuthToken.user_id == user_id).first()
        )

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
        print(f"An error occurred: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    # Default user ID can be changed here or overridden with command line arg
    DEFAULT_USER_ID = "edge-1747926342290-0o8cbiri"  # Example user ID

    if len(sys.argv) > 1:
        USER_ID_TO_DELETE = sys.argv[1]
        print(f"Using user ID from command line: {USER_ID_TO_DELETE}")
    else:
        USER_ID_TO_DELETE = DEFAULT_USER_ID
        print(f"Using default user ID: {USER_ID_TO_DELETE}")

    print(
        f"Attempting to delete token for user: {USER_ID_TO_DELETE} from database: {settings.DATABASE_URL}"
    )

    # Ensure the JIRA_TOKEN_ENCRYPTION_KEY is loaded if models.token tries to use it,
    # though for deletion it's not strictly necessary for decryption.
    encryption_key = os.getenv("JIRA_TOKEN_ENCRYPTION_KEY")
    if not encryption_key:
        print("WARNING: JIRA_TOKEN_ENCRYPTION_KEY is not set in the environment.")
    else:
        print("JIRA_TOKEN_ENCRYPTION_KEY is loaded.")

    result = cleanup_token(USER_ID_TO_DELETE)
    print(f"Token cleanup result: {'Success' if result else 'Failed or not found'}")
