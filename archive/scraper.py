"""
TaurBull Web Scraper

This module handles the scraping of content from the TaurBull website, specifically:
- FAQ sections
- Documentation
- API references
"""

import os
import re
import time
import logging
import requests
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("scraper")

# Base URL configuration
BASE_URL = "https://taurbull.com"
FAQ_URL = f"{BASE_URL}/faq"
DOCS_URL = f"{BASE_URL}/documentation"
API_URL = f"{BASE_URL}/api-reference"


class TaurBullScraper:
    """
    Scraper for TaurBull website content.
    """
    
    def __init__(self, rate_limit: float = 1.0):
        """
        Initialize the TaurBull scraper.
        
        Args:
            rate_limit (float): Minimum time between requests in seconds
                              to avoid overloading the server.
        """
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TaurBull Knowledge Base Updater (contact@example.com)'
        })
        
        logger.info("TaurBull scraper initialized")
    
    def _respect_rate_limit(self):
        """
        Wait if necessary to respect the rate limit.
        """
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            wait_time = self.rate_limit - elapsed
            logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
        self.last_request_time = time.time()
    
    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch a page and return a BeautifulSoup object.
        
        Args:
            url (str): URL to fetch
            
        Returns:
            BeautifulSoup: Parsed HTML, or None if fetch failed
        """
        try:
            self._respect_rate_limit()
            logger.info(f"Fetching page: {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def get_faq_content(self) -> Dict[str, str]:
        """
        Scrape FAQ content from the TaurBull website.
        
        Returns:
            Dict[str, str]: Dictionary mapping question to answer text
        """
        faq_dict = {}
        soup = self._fetch_page(FAQ_URL)
        
        if not soup:
            logger.error("Failed to fetch FAQ page")
            return faq_dict
        
        # Find all FAQ sections/accordions
        faq_sections = soup.select('.faq-container .faq-item')
        
        if not faq_sections:
            logger.warning("No FAQ sections found on the page")
            return faq_dict
        
        logger.info(f"Found {len(faq_sections)} FAQ sections")
        
        for item in faq_sections:
            question_elem = item.select_one('.faq-question')
            answer_elem = item.select_one('.faq-answer')
            
            if question_elem and answer_elem:
                question = question_elem.get_text(strip=True)
                answer = answer_elem.get_text(strip=True)
                
                if question and answer:
                    faq_dict[question] = answer
                    logger.debug(f"Extracted FAQ: {question[:30]}...")
        
        logger.info(f"Extracted {len(faq_dict)} FAQ items")
        return faq_dict
    
    def get_documentation_content(self) -> List[Dict]:
        """
        Scrape documentation content from the TaurBull website.
        
        Returns:
            List[Dict]: List of documentation sections, each containing:
                - title: Section title
                - content: Section content text
                - url: URL of the section
        """
        doc_sections = []
        soup = self._fetch_page(DOCS_URL)
        
        if not soup:
            logger.error("Failed to fetch documentation page")
            return doc_sections
        
        # Find all documentation section links
        section_links = soup.select('.documentation-menu a')
        
        if not section_links:
            logger.warning("No documentation section links found")
            return doc_sections
        
        logger.info(f"Found {len(section_links)} documentation section links")
        
        # Process each documentation section
        for link in section_links:
            section_url = link.get('href')
            section_title = link.get_text(strip=True)
            
            if not section_url or not section_title:
                continue
                
            # Make the URL absolute if it's relative
            if not section_url.startswith('http'):
                section_url = f"{BASE_URL}{section_url if section_url.startswith('/') else '/' + section_url}"
            
            logger.debug(f"Processing documentation section: {section_title}")
            
            # Fetch the section page
            section_soup = self._fetch_page(section_url)
            if not section_soup:
                logger.error(f"Failed to fetch documentation section: {section_title}")
                continue
            
            # Extract the main content
            content_elem = section_soup.select_one('.documentation-content')
            if not content_elem:
                logger.warning(f"No content found for documentation section: {section_title}")
                continue
            
            section_content = content_elem.get_text(strip=True)
            
            doc_sections.append({
                'title': section_title,
                'content': section_content,
                'url': section_url
            })
            
            logger.debug(f"Extracted documentation section: {section_title}")
        
        logger.info(f"Extracted {len(doc_sections)} documentation sections")
        return doc_sections
    
    def get_api_reference(self) -> List[Dict]:
        """
        Scrape API reference content from the TaurBull website.
        
        Returns:
            List[Dict]: List of API endpoints, each containing:
                - endpoint: API endpoint path
                - method: HTTP method (GET, POST, etc.)
                - description: Description of the endpoint
                - parameters: List of parameters
                - responses: Example responses
        """
        api_endpoints = []
        soup = self._fetch_page(API_URL)
        
        if not soup:
            logger.error("Failed to fetch API reference page")
            return api_endpoints
        
        # Find all API endpoint sections
        endpoint_sections = soup.select('.api-endpoint')
        
        if not endpoint_sections:
            logger.warning("No API endpoint sections found")
            return api_endpoints
        
        logger.info(f"Found {len(endpoint_sections)} API endpoints")
        
        for section in endpoint_sections:
            try:
                # Extract endpoint and method
                header = section.select_one('.endpoint-header')
                if not header:
                    continue
                
                method_elem = header.select_one('.http-method')
                path_elem = header.select_one('.endpoint-path')
                
                if not method_elem or not path_elem:
                    continue
                
                method = method_elem.get_text(strip=True)
                endpoint_path = path_elem.get_text(strip=True)
                
                # Extract description
                desc_elem = section.select_one('.endpoint-description')
                description = desc_elem.get_text(strip=True) if desc_elem else ""
                
                # Extract parameters
                params = []
                param_table = section.select_one('.parameters-table')
                if param_table:
                    param_rows = param_table.select('tr')[1:]  # Skip header row
                    for row in param_rows:
                        cols = row.select('td')
                        if len(cols) >= 3:
                            param_name = cols[0].get_text(strip=True)
                            param_type = cols[1].get_text(strip=True)
                            param_desc = cols[2].get_text(strip=True)
                            
                            params.append({
                                'name': param_name,
                                'type': param_type,
                                'description': param_desc
                            })
                
                # Extract example responses
                response_elem = section.select_one('.response-example')
                response_text = response_elem.get_text() if response_elem else ""
                
                # Add the endpoint to our list
                api_endpoints.append({
                    'method': method,
                    'endpoint': endpoint_path,
                    'description': description,
                    'parameters': params,
                    'response': response_text
                })
                
                logger.debug(f"Extracted API endpoint: {method} {endpoint_path}")
                
            except Exception as e:
                logger.error(f"Error processing API endpoint: {e}")
        
        logger.info(f"Extracted {len(api_endpoints)} API endpoints")
        return api_endpoints
    
    def format_knowledge_base_content(self) -> str:
        """
        Combine and format all content from the website for the knowledge base.
        
        Returns:
            str: Formatted content for the knowledge base
        """
        content_parts = []
        
        # Add FAQ content
        faq_content = self.get_faq_content()
        if faq_content:
            content_parts.append("# TaurBull Frequently Asked Questions\n")
            
            for question, answer in faq_content.items():
                content_parts.append(f"## {question}\n{answer}\n\n")
        
        # Add documentation content
        doc_content = self.get_documentation_content()
        if doc_content:
            content_parts.append("# TaurBull Documentation\n")
            
            for section in doc_content:
                content_parts.append(f"## {section['title']}\n{section['content']}\n\n")
                content_parts.append(f"Source: {section['url']}\n\n")
        
        # Add API reference content
        api_content = self.get_api_reference()
        if api_content:
            content_parts.append("# TaurBull API Reference\n")
            
            for endpoint in api_content:
                content_parts.append(f"## {endpoint['method']} {endpoint['endpoint']}\n")
                content_parts.append(f"{endpoint['description']}\n\n")
                
                if endpoint['parameters']:
                    content_parts.append("### Parameters\n")
                    for param in endpoint['parameters']:
                        content_parts.append(f"- **{param['name']}** ({param['type']}): {param['description']}\n")
                    content_parts.append("\n")
                
                if endpoint['response']:
                    content_parts.append("### Example Response\n")
                    content_parts.append(f"```json\n{endpoint['response']}\n```\n\n")
        
        # Combine all content parts
        combined_content = "\n".join(content_parts)
        logger.info(f"Generated knowledge base content ({len(combined_content)} characters)")
        
        return combined_content 