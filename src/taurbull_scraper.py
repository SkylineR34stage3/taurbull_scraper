"""
TaurBull Website Scraper

Module for scraping FAQ content from the TaurBull website.
"""

import re
import time
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class TaurBullScraper:
    """
    Class to scrape content from the TaurBull website
    """
    # Base URL for the TaurBull website
    BASE_URL = "https://taurbull.com"
    
    # Corrected FAQ page path
    FAQ_PATH = "/pages/faq"
    
    def __init__(self, request_delay: float = 1.0):
        """
        Initialize the TaurBull scraper
        
        Args:
            request_delay: Delay between requests in seconds to avoid rate limiting
        """
        self.request_delay = request_delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "Accept-Language": "en-US,en;q=0.9"
        })
    
    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Get a page and parse it with BeautifulSoup
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if the request failed
        """
        try:
            logger.info(f"Fetching page: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Add delay after request to be polite
            time.sleep(self.request_delay)
            
            return BeautifulSoup(response.text, "html.parser")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching page {url}: {e}")
            return None
    
    def _extract_faq_sections(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract FAQ sections from the FAQ page
        
        Args:
            soup: BeautifulSoup object of the FAQ page
            
        Returns:
            List of dictionaries with section title and questions
        """
        # Based on analysis, the TaurBull FAQ page doesn't have a typical FAQ structure
        # with accordions or details/summary. Instead, it has plain text questions and answers.
        # We'll extract these by looking for question marks.
        
        # Get the main content
        main_content = soup.select_one("main, .page-container, .page-content")
        if not main_content:
            logger.warning("Could not find main content section, using full page")
            main_content = soup
        
        # Find all paragraphs, text elements that might contain questions and answers
        text_elements = main_content.find_all(["p", "h3", "h4", "div", "span", "strong"])
        
        # Find potential questions (text containing a question mark)
        questions_with_answers = []
        current_question = None
        current_question_elem = None
        
        # Iterate through all text elements to identify questions and their answers
        for elem in text_elements:
            text = elem.get_text(strip=True)
            
            # Skip empty elements or very short text
            if not text or len(text) < 5:
                continue
            
            # Skip navigation elements, footers, etc.
            skip_phrases = ["menu", "links", "folge uns", "newsletter", "copyright", "powered by"]
            if any(phrase in text.lower() for phrase in skip_phrases):
                continue
            
            # Check if this element contains a question (has a question mark)
            if "?" in text and len(text) < 200:
                # If we already have a question waiting for an answer, store it with an empty answer
                if current_question and current_question not in [q["question"] for q in questions_with_answers]:
                    questions_with_answers.append({
                        "question": current_question,
                        "answer": ""  # No answer found
                    })
                
                current_question = text
                current_question_elem = elem
            
            # If we have a question and this element might be its answer
            elif current_question and elem != current_question_elem:
                # Check if this looks like an answer (not another question, reasonable length)
                if "?" not in text and len(text) > 10:
                    # This is likely the answer to our question
                    questions_with_answers.append({
                        "question": current_question,
                        "answer": text
                    })
                    current_question = None
                    current_question_elem = None
        
        # Handle any remaining question
        if current_question and current_question not in [q["question"] for q in questions_with_answers]:
            questions_with_answers.append({
                "question": current_question,
                "answer": ""  # No answer found
            })
        
        # Group by category if possible
        sections = []
        
        # Find all category headings (h2 elements)
        category_headings = main_content.select("h2")
        
        if category_headings:
            # Create a mapping of questions to categories
            question_categories = {}
            
            for heading in category_headings:
                category_name = heading.get_text(strip=True)
                
                # Skip non-category headings
                if len(category_name) < 3 or any(phrase in category_name.lower() for phrase in ["menu", "links", "folge"]):
                    continue
                
                # Get all text elements that follow this heading until the next heading
                next_elem = heading.next_sibling
                while next_elem and (not hasattr(next_elem, 'name') or next_elem.name != 'h2'):
                    if hasattr(next_elem, 'get_text'):
                        text = next_elem.get_text(strip=True)
                        
                        # Check if this element contains any of our questions
                        for qa_pair in questions_with_answers:
                            if qa_pair["question"] in text:
                                question_categories[qa_pair["question"]] = category_name
                    
                    # Move to the next element
                    if hasattr(next_elem, 'next_sibling'):
                        next_elem = next_elem.next_sibling
                    else:
                        break
            
            # Group questions by category
            categorized_questions = {}
            for qa_pair in questions_with_answers:
                category = question_categories.get(qa_pair["question"], "General FAQ")
                if category not in categorized_questions:
                    categorized_questions[category] = []
                categorized_questions[category].append(qa_pair)
            
            # Create sections from the categorized questions
            for category, questions in categorized_questions.items():
                if questions:
                    sections.append({
                        "title": category,
                        "questions": questions
                    })
        
        # If we couldn't categorize by heading, create a single section
        if not sections and questions_with_answers:
            sections.append({
                "title": "Frequently Asked Questions",
                "questions": questions_with_answers
            })
        
        # Log the results
        total_questions = sum(len(section["questions"]) for section in sections)
        if sections:
            logger.info(f"Extracted {len(sections)} FAQ sections with {total_questions} questions")
        else:
            logger.warning("No FAQ questions found on the page")
        
        return sections
    
    def _extract_additional_content(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extract additional content like company info, product descriptions, etc.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            Dictionary with extracted content
        """
        content = {}
        
        # Extract intro text if available
        intro_section = soup.select_one("h2 + p, .page-description, .rte > p:first-of-type")
        if intro_section:
            content["introduction"] = intro_section.get_text(strip=True)
        
        # Get the main heading
        main_heading = soup.select_one("h1")
        if main_heading:
            content["title"] = main_heading.get_text(strip=True)
        
        # Extract any highlighted paragraphs
        highlight_para = soup.select_one("h1 + p, .intro, .lead")
        if highlight_para:
            content["highlight"] = highlight_para.get_text(strip=True)
        
        return content
    
    def _explore_navigation(self) -> List[str]:
        """
        Explore the website navigation to find important pages
        
        Returns:
            List of important page URLs
        """
        urls = []
        
        # Get the homepage
        homepage = self._get_page(self.BASE_URL)
        if not homepage:
            return urls
        
        # Find all navigation links
        nav_links = homepage.select("nav a, .menu a, .navigation a, header a")
        
        for link in nav_links:
            href = link.get("href")
            
            if not href or href == "#" or href.startswith("javascript:"):
                continue
                
            # Normalize URL
            if href.startswith("/"):
                href = f"{self.BASE_URL}{href}"
            elif not href.startswith("http"):
                href = f"{self.BASE_URL}/{href}"
                
            # Only include links to the same domain
            if self.BASE_URL in href:
                urls.append(href)
        
        return urls
    
    def scrape_website(self) -> Dict[str, Any]:
        """
        Scrape content from the TaurBull website
        
        Returns:
            Dictionary with scraped content
        """
        result = {
            "faq": [],
            "additional_content": {}
        }
        
        # Scrape the FAQ page
        faq_url = f"{self.BASE_URL}{self.FAQ_PATH}"
        faq_page = self._get_page(faq_url)
        
        if faq_page:
            # Extract FAQ sections
            faq_sections = self._extract_faq_sections(faq_page)
            result["faq"] = faq_sections
            
            # Extract additional content from FAQ page
            additional_content = self._extract_additional_content(faq_page)
            result["additional_content"].update(additional_content)
            
            logger.info(f"Successfully scraped {len(faq_sections)} FAQ sections from {faq_url}")
        else:
            logger.warning(f"Failed to fetch FAQ page: {faq_url}")
            
            # Try to find FAQ content from other pages if FAQ page failed
            logger.info("Attempting to find FAQ content from navigation pages")
            important_pages = self._explore_navigation()
            
            for page_url in important_pages[:5]:  # Limit to first 5 important pages
                page_soup = self._get_page(page_url)
                if page_soup:
                    # Look for FAQ-like content on this page
                    page_faq = self._extract_faq_sections(page_soup)
                    if page_faq:
                        result["faq"].extend(page_faq)
                        logger.info(f"Found {len(page_faq)} FAQ sections on {page_url}")
                    
                    # Extract additional content
                    page_content = self._extract_additional_content(page_soup)
                    result["additional_content"].update(page_content)
        
        # Check if we found any FAQ content
        if not result["faq"]:
            logger.warning("No FAQ content found on the website")
        else:
            logger.info(f"Total FAQ items found: {sum(len(section.get('questions', [])) for section in result['faq'])}")
        
        return result
    
    def format_content_for_upload(self, scraped_data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Format scraped content for uploading to the knowledge base
        
        Args:
            scraped_data: Dictionary with scraped content
            
        Returns:
            Tuple of (formatted content, document title)
        """
        content_parts = []
        
        # Add title if available
        if "title" in scraped_data.get("additional_content", {}):
            content_parts.append(f"# {scraped_data['additional_content']['title']}\n")
        else:
            content_parts.append("# TaurBull Frequently Asked Questions\n")
        
        # Add introduction if available
        if "introduction" in scraped_data.get("additional_content", {}):
            content_parts.append(scraped_data["additional_content"]["introduction"])
            content_parts.append("\n")
        
        # Add highlight if available
        if "highlight" in scraped_data.get("additional_content", {}):
            content_parts.append(scraped_data["additional_content"]["highlight"])
            content_parts.append("\n")
        
        # Add FAQ sections
        for section in scraped_data.get("faq", []):
            # Add section title
            section_title = section.get("title", "General FAQ")
            content_parts.append(f"\n## {section_title}\n")
            
            # Add questions and answers
            for item in section.get("questions", []):
                question = item.get("question", "")
                answer = item.get("answer", "")
                
                if question:
                    content_parts.append(f"\n### {question}\n")
                    if answer:
                        content_parts.append(f"{answer}\n")
                    else:
                        content_parts.append("*No answer provided*\n")
        
        # Join all parts
        formatted_content = "\n".join(content_parts)
        
        # Create document title with timestamp and document type
        # Use underscore naming convention for better type detection
        document_title = f"TaurBull_FAQ - {time.strftime('%Y-%m-%d')}"
        
        return formatted_content, document_title 