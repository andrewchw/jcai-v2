#!/usr/bin/env python3
"""
Cleanup OAuth token files to start fresh

This script deletes any existing OAuth token files to ensure a clean authentication process.
"""

import os
import sys
import logging
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    # Token files to clean up
    token_files = [
        "oauth_token.json",
        "python-server/oauth_token.json"
    ]
    
    # Backup directory
    backup_dir = f"token_backups_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Process each token file
    for token_file in token_files:
        if os.path.exists(token_file):
            logger.info(f"Found token file: {token_file}")
            
            # Create backup
            backup_path = os.path.join(backup_dir, os.path.basename(token_file))
            try:
                shutil.copy2(token_file, backup_path)
                logger.info(f"Created backup at: {backup_path}")
            except Exception as e:
                logger.warning(f"Could not create backup: {str(e)}")
            
            # Delete the file
            try:
                os.remove(token_file)
                logger.info(f"Deleted token file: {token_file}")
            except Exception as e:
                logger.error(f"Failed to delete {token_file}: {str(e)}")
    
    # Check if we actually backed up any files
    if not any(os.path.exists(os.path.join(backup_dir, os.path.basename(f))) for f in token_files):
        # Remove empty backup directory
        try:
            os.rmdir(backup_dir)
            logger.info("No token files found, removed empty backup directory.")
        except:
            pass
    
    logger.info("Cleanup complete!")
    logger.info("You can now run the OAuth troubleshooter script to get new tokens.")

if __name__ == "__main__":
    main()
