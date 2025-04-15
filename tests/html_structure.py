#!/usr/bin/env python3
"""
Script to analyze the HTML structure of the TaurBull FAQ page
"""

import os
import sys
import requests
import time
from bs4 import BeautifulSoup

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_page(url):
    """Get the page content"""
    print(f"Fetching page: {url}")
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.text

def analyze_html(html_content):
    """Analyze the HTML structure"""
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Get the title
    title = soup.title.string if soup.title else "No title"
    print(f"Page title: {title}")
    
    # Look for main content
    main_content = soup.select_one("main, .page-container, .page-content")
    if main_content:
        print("Found main content container")
    else:
        print("No main content container found, using full page")
        main_content = soup
    
    # Look for headings
    headings = main_content.find_all(["h1", "h2", "h3", "h4"])
    print(f"Found {len(headings)} headings")
    for i, heading in enumerate(headings[:10]):  # Show first 10
        print(f"  Heading {i+1}: {heading.get_text(strip=True)[:50]}")
    
    # Look for details/summary elements (typical FAQ structure)
    details = main_content.find_all("details")
    print(f"Found {len(details)} details elements")
    
    # Look for potential FAQ containers
    faq_containers = main_content.select(".faq, .faqs, .accordion, .question-answer, details")
    print(f"Found {len(faq_containers)} potential FAQ containers")
    
    # Look for elements with roles
    role_elements = main_content.select("[role]")
    print(f"Found {len(role_elements)} elements with role attributes")
    roles = set(elem.get("role") for elem in role_elements)
    print(f"Roles: {', '.join(roles)}")
    
    # Analyze text looking for question marks (potential questions)
    potential_questions = []
    for elem in main_content.find_all(["p", "div", "span", "strong", "h3", "h4", "summary"]):
        text = elem.get_text(strip=True)
        if "?" in text and 10 < len(text) < 200:
            potential_questions.append(text[:100] + ("..." if len(text) > 100 else ""))
    
    print(f"Found {len(potential_questions)} potential questions (containing '?')")
    for i, q in enumerate(potential_questions[:10]):  # Show first 10
        print(f"  Question {i+1}: {q}")
    
    # Specific analysis for commonly used FAQ class names
    faq_classes = {
        "accordion": main_content.select(".accordion, .accordions"),
        "faq": main_content.select(".faq, .faqs, .faq-item"),
        "question": main_content.select(".question, .faq-question"),
        "answer": main_content.select(".answer, .faq-answer"),
        "card": main_content.select(".card, .faq-card, .accordion-card"),
        "collapsible": main_content.select(".collapse, .collapsible"),
    }
    
    print("\nSpecific FAQ class analysis:")
    for class_name, elements in faq_classes.items():
        print(f"  {class_name}: {len(elements)} elements")
        if elements:
            for i, elem in enumerate(elements[:3]):  # Show first 3
                print(f"    Sample text: {elem.get_text(strip=True)[:50]}")
    
    # Check for JavaScript components
    scripts = soup.find_all("script")
    for script in scripts:
        script_text = script.string if script.string else ""
        if script_text and any(keyword in script_text.lower() for keyword in ["accordion", "faq", "collapse", "toggle"]):
            print("Found JavaScript potentially related to FAQs/accordions")
            break

def main():
    """Main function"""
    url = "https://taurbull.com/pages/faq"
    
    try:
        html_content = get_page(url)
        
        # Save the HTML content for manual inspection
        with open(os.path.join(os.path.dirname(__file__), "taurbull_faq.html"), "w", encoding="utf-8") as f:
            f.write(html_content)
            print(f"Saved HTML content to taurbull_faq.html")
        
        # Analyze the HTML structure
        analyze_html(html_content)
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 