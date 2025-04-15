#!/usr/bin/env python3
"""
TaurBull Scraper - Scheduler Script

This script is used by the Heroku Scheduler to run the scraper at regular intervals.
"""

import os
import sys
import logging
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

if __name__ == "__main__":
    logger.info("Starting scheduled TaurBull scraper run")
    
    try:
        # Import and run the main function
        from main import main
        exit_code = main()
        
        logger.info(f"Scraper run completed with exit code: {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        logger.exception(f"Error during scheduled scraper run: {e}")
        sys.exit(1) 