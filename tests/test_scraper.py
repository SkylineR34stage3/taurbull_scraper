#!/usr/bin/env python3
"""
Test script for the TaurBull scraper

This script tests the TaurBull scraper's ability to fetch and parse FAQ content
from the TaurBull website.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pprint import pprint

# Add the parent directory to the path so we can import the scraper module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.taurbull_scraper import TaurBullScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_scraper")

def save_to_file(data, filename):
    """Save data to a JSON file in the tests directory"""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Data saved to {filepath}")

def test_scraper_basic():
    """Test the basic functionality of the TaurBull scraper"""
    logger.info("Testing basic TaurBull scraper functionality")
    
    # Initialize the scraper
    scraper = TaurBullScraper(request_delay=1.0)
    
    # Test the _get_page method
    logger.info("Testing _get_page method on the FAQ page")
    faq_url = f"{scraper.BASE_URL}{scraper.FAQ_PATH}"
    page = scraper._get_page(faq_url)
    
    if page:
        logger.info("Successfully fetched the FAQ page")
        logger.info(f"Page title: {page.title.string if page.title else 'No title found'}")
    else:
        logger.error("Failed to fetch the FAQ page")
        return False
    
    # Test extracting FAQ sections
    logger.info("Testing _extract_faq_sections method")
    faq_sections = scraper._extract_faq_sections(page)
    
    if faq_sections:
        logger.info(f"Found {len(faq_sections)} FAQ sections")
        for i, section in enumerate(faq_sections):
            logger.info(f"Section {i+1}: {section.get('title', 'Untitled')}")
            logger.info(f"  Questions: {len(section.get('questions', []))}")
    else:
        logger.warning("No FAQ sections found")
    
    # Save the extracted FAQ sections to a file for manual review
    if faq_sections:
        save_to_file(faq_sections, "extracted_faq_sections.json")
    
    # Test extracting additional content
    logger.info("Testing _extract_additional_content method")
    additional_content = scraper._extract_additional_content(page)
    
    if additional_content:
        logger.info(f"Found additional content: {', '.join(additional_content.keys())}")
    else:
        logger.info("No additional content found")
    
    return True

def test_full_scrape():
    """Test the full scraping process"""
    logger.info("Testing full website scraping")
    
    # Initialize the scraper
    scraper = TaurBullScraper(request_delay=1.0)
    
    # Scrape the website
    scraped_data = scraper.scrape_website()
    
    # Check the results
    faq_sections = scraped_data.get("faq", [])
    if faq_sections:
        total_questions = sum(len(section.get("questions", [])) for section in faq_sections)
        logger.info(f"Successfully scraped {len(faq_sections)} FAQ sections with {total_questions} total questions")
        
        # Save the scraped data to a file for manual review
        save_to_file(scraped_data, "scraped_data.json")
        
        # Test formatting the content for upload
        logger.info("Testing format_content_for_upload method")
        formatted_content, document_title = scraper.format_content_for_upload(scraped_data)
        
        logger.info(f"Formatted content length: {len(formatted_content)} characters")
        logger.info(f"Document title: {document_title}")
        
        # Save the formatted content to a file for manual review
        with open(os.path.join(os.path.dirname(__file__), "formatted_content.md"), 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        logger.info("Formatted content saved to formatted_content.md")
        
        return True
    else:
        logger.error("No FAQ sections found during website scraping")
        return False

if __name__ == "__main__":
    logger.info("Starting TaurBull scraper tests")
    
    # Run the tests
    basic_result = test_scraper_basic()
    full_result = test_full_scrape()
    
    # Print the results
    logger.info("\n== Test Results ==")
    logger.info(f"Basic scraper test: {'PASSED' if basic_result else 'FAILED'}")
    logger.info(f"Full scrape test: {'PASSED' if full_result else 'FAILED'}")
    
    # Exit with appropriate code
    if basic_result and full_result:
        logger.info("All tests passed successfully!")
        sys.exit(0)
    else:
        logger.error("Some tests failed")
        sys.exit(1) 