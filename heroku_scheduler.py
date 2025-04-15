#!/usr/bin/env python3
"""
TaurBull Scraper - Scheduler Script

This script is used by the Heroku Scheduler to run the scraper at regular intervals.
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"logs/scheduler_{datetime.now().strftime('%Y-%m-%d')}.log")
    ]
)
logger = logging.getLogger("taurbull_scheduler")

def init_setup():
    """Initial setup after deployment"""
    logger.info("Performing initial setup after deployment")
    
    # Create necessary directories
    os.makedirs("content_cache", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Initialize content map files
    if not os.path.exists("content_cache/content_map.json"):
        with open("content_cache/content_map.json", "w") as f:
            f.write("{}")
            
    if not os.path.exists("content_cache/document_map.json"):
        with open("content_cache/document_map.json", "w") as f:
            f.write("{}")
    
    logger.info("Initial setup completed successfully")
    return 0

def main():
    """Main function to handle scheduler operations"""
    parser = argparse.ArgumentParser(description="TaurBull Scheduler")
    parser.add_argument("--init", action="store_true", help="Initialize the app after deployment")
    args = parser.parse_args()
    
    if args.init:
        return init_setup()
    
    logger.info("Starting scheduled TaurBull scraper run")
    
    try:
        # Import and run the main function
        from main import main as run_scraper
        exit_code = run_scraper()
        
        logger.info(f"Scraper run completed with exit code: {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.exception(f"Error during scheduled scraper run: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 