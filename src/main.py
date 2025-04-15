"""
TaurBull Scraper - Main Script

This script orchestrates the scraping process and updates to the Elevenlabs knowledge base.
It uses the knowledge base manager to detect changes and update the knowledge base accordingly.
"""

import os
import time
import logging
import argparse
import schedule
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.kb_manager import KnowledgeBaseManager

# Load environment variables from .env file
load_dotenv()

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/main.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")


def update_knowledge_base():
    """
    Run the knowledge base update process.
    """
    logger.info("Starting knowledge base update process...")
    
    try:
        # Initialize the knowledge base manager
        manager = KnowledgeBaseManager()
        
        # Print initial status
        manager.print_status()
        
        # Update the FAQ knowledge base
        success, message = manager.update_faq_kb()
        
        if success:
            logger.info(message)
        else:
            logger.error(message)
            
        # Here you could add more page types to scrape and update
        # For example:
        # success, message = manager.update_privacy_policy_kb()
        # success, message = manager.update_terms_kb()
        
        # Print final status
        manager.print_status()
        
        logger.info("Knowledge base update process completed.")
        return success
        
    except Exception as e:
        logger.error(f"Error in update process: {str(e)}")
        return False


def setup_schedule(interval_hours=None, run_immediate=True):
    """
    Set up the schedule for regular updates.
    
    Args:
        interval_hours (int): Interval in hours between updates.
        run_immediate (bool): Whether to run an update immediately.
    """
    # Get interval from environment variable if not provided
    if interval_hours is None:
        try:
            interval_hours = int(os.environ.get("UPDATE_INTERVAL", "24"))
        except ValueError:
            interval_hours = 24
            logger.warning("Invalid UPDATE_INTERVAL value in .env file. Using default 24 hours.")
    
    if run_immediate:
        logger.info("Running immediate update...")
        update_knowledge_base()
    
    # Schedule regular updates
    scheduled_time = f"{datetime.now().hour:02d}:{datetime.now().minute:02d}"
    logger.info(f"Scheduling updates to run every {interval_hours} hours, starting at {scheduled_time}")
    
    if interval_hours == 24:
        schedule.every().day.at(scheduled_time).do(update_knowledge_base)
    else:
        schedule.every(interval_hours).hours.do(update_knowledge_base)
    
    # Run the scheduler loop
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


def main():
    """
    Main function to parse arguments and start the process.
    """
    parser = argparse.ArgumentParser(description="TaurBull Scraper and Knowledge Base Updater")
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, help="Update interval in hours (default: from .env or 24)")
    parser.add_argument("--no-immediate", action="store_true", help="Don't run an immediate update on start")
    parser.add_argument("--assistant", type=str, help="Elevenlabs Assistant ID to associate knowledge base with")
    args = parser.parse_args()
    
    # Set assistant ID in environment if provided
    if args.assistant:
        os.environ["ELEVENLABS_ASSISTANT_ID"] = args.assistant
    
    logger.info("TaurBull Scraper starting...")
    
    if args.run_once:
        success = update_knowledge_base()
        return 0 if success else 1
    else:
        try:
            setup_schedule(args.interval, not args.no_immediate)
        except KeyboardInterrupt:
            logger.info("Process interrupted by user. Exiting gracefully...")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 