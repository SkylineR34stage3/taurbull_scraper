#!/usr/bin/env python3
"""
TaurBull Scraper - Main Script

This script orchestrates the scraping process and updates to the Elevenlabs knowledge base.
It uses the knowledge base manager to detect changes and update the knowledge base accordingly.
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

from src.kb_manager import KnowledgeBaseManager
from src.taurbull_scraper import TaurBullScraper

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"logs/scraper_{datetime.now().strftime('%Y-%m-%d')}.log")
    ]
)
logger = logging.getLogger("taurbull_scraper_main")

def setup_environment():
    """Set up the environment and validate required variables"""
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = ["ELEVENLABS_API_KEY", "ELEVENLABS_ASSISTANT_ID"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in a .env file or export them in your shell")
        sys.exit(1)
    
    return {
        "api_key": os.environ.get("ELEVENLABS_API_KEY"),
        "assistant_id": os.environ.get("ELEVENLABS_ASSISTANT_ID")
    }

def main():
    """Main function to run the TaurBull scraper and update the knowledge base"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="TaurBull Scraper for Elevenlabs Knowledge Base")
    parser.add_argument("--dry-run", action="store_true", help="Run scraper without uploading to Elevenlabs")
    parser.add_argument("--force", action="store_true", help="Force update even if content hasn't changed")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds (default: 1.0)")
    parser.add_argument("--output", type=str, help="Save scraped content to file")
    args = parser.parse_args()
    
    # Set up environment
    logger.info("Setting up environment")
    env = setup_environment()
    
    # Initialize the knowledge base manager
    manager = KnowledgeBaseManager(
        api_key=env["api_key"],
        assistant_id=env["assistant_id"]
    )
    
    # Display initial status
    if not args.dry_run:
        manager.print_status()
    
    try:
        # Approach 1: Use simple_faq_scraper via KB Manager
        if not args.force:
            logger.info("Using Knowledge Base Manager to update FAQ knowledge base")
            success, message = manager.update_faq_kb()
            
            if success:
                logger.info(message)
                if args.output:
                    manager.export_formatted_faq(args.output)
                    logger.info(f"Saved formatted content to {args.output}")
            else:
                logger.error(message)
                
                # If KB Manager approach failed, try the direct scraper as fallback
                logger.info("Trying alternative scraper as fallback...")
                use_direct_scraper = True
        else:
            # Skip KB Manager if --force flag is used
            use_direct_scraper = True
        
        # Approach 2: Direct scraping with TaurBullScraper (used as fallback or with --force)
        if args.force or locals().get('use_direct_scraper'):
            logger.info(f"Using direct scraper with {args.delay}s delay between requests")
            
            # Initialize the scraper
            scraper = TaurBullScraper(request_delay=args.delay)
            
            # Scrape the website
            logger.info("Starting website scraping")
            start_time = time.time()
            scraped_data = scraper.scrape_website()
            logger.info(f"Scraping completed in {time.time() - start_time:.2f} seconds")
            
            # Check if any content was scraped
            if not scraped_data.get("faq"):
                logger.warning("No FAQ content was scraped, nothing to upload")
                return 1
            
            # Format content for upload
            logger.info("Formatting content for knowledge base")
            formatted_content, document_title = scraper.format_content_for_upload(scraped_data)
            
            # Save to file if requested
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(formatted_content)
                logger.info(f"Saved formatted content to {args.output}")
            
            # Exit if dry run
            if args.dry_run:
                logger.info("Dry run completed, skipping upload to Elevenlabs")
                return 0
            
            # Use the KB Manager to handle the upload
            logger.info("Using KB Manager to upload scraped content")
            
            # Convert the scraped data into the format expected by KB Manager
            kb_faqs = []
            for section in scraped_data.get("faq", []):
                for item in section.get("questions", []):
                    kb_faqs.append({
                        "question": item.get("question", ""),
                        "answer": item.get("answer", "")
                    })
            
            # Upload using the KB Manager (which handles document replacement)
            success = manager.update_kb_with_custom_content(
                content_id="faq_direct",
                content=kb_faqs,
                document_name=document_title,
                formatted_text=formatted_content
            )
            
            if success:
                logger.info("Successfully uploaded TaurBull content to Elevenlabs knowledge base")
            else:
                logger.error("Failed to upload content to knowledge base")
                return 1
        
        # Display final status
        if not args.dry_run:
            manager.print_status()
            
        return 0
    
    except Exception as e:
        logger.exception(f"Error during scraping process: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 