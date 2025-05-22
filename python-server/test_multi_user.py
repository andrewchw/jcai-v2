import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('multi_user_test_wrapper.log')
    ]
)

logger = logging.getLogger(__name__)
logger.info("Starting multi-user test wrapper")

# Add the project directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Run the test_multi_user script
try:
    from app.scripts.test_multi_user import run_tests
    
    if __name__ == "__main__":
        logger.info("Running multi-user tests")
        success = run_tests()
        if success:
            logger.info("Tests completed successfully")
            sys.exit(0)
        else:
            logger.error("Tests failed")
            sys.exit(1)
except Exception as e:
    logger.exception(f"Error running tests: {str(e)}")
    sys.exit(1)
