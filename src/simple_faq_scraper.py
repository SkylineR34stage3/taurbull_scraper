"""
Simple FAQ Scraper - A basic script to scrape FAQs from TaurBull website.

This script demonstrates the basics of web scraping and JSON extraction.
"""

import requests  # For making HTTP requests
from bs4 import BeautifulSoup  # For parsing HTML
import json  # For working with JSON data
import re  # For regular expressions

# The URL of the FAQ page
URL = "https://taurbull.com/pages/faq"

def clean_json_ld(json_str):
    """
    Clean and fix common issues in JSON-LD strings found in webpages.
    
    Args:
        json_str (str): The JSON-LD string to clean
        
    Returns:
        str: The cleaned JSON string
    """
    # Remove leading/trailing whitespace
    cleaned = json_str.strip()
    
    # Sometimes JSON has JavaScript comments which are not valid in JSON
    cleaned = re.sub(r'//.*?\n', '', cleaned)
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
    
    # Look for common errors in JSON-LD and fix them
    
    # Fix common error: missing commas between objects in an array
    cleaned = re.sub(r'}\s*{', '},{', cleaned)
    
    # Fix trailing commas (not allowed in JSON)
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
    
    # Fix missing quotes around property names
    cleaned = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', cleaned)
    
    return cleaned

def scrape_faq():
    """
    Scrape FAQs from the TaurBull website.
    
    Returns:
        list: A list of dictionaries, each containing a question and answer
    """
    print(f"Fetching content from {URL}...")
    
    # Step 1: Fetch the webpage content
    response = requests.get(URL)
    
    # Check if the request was successful (status code 200)
    if response.status_code != 200:
        print(f"Failed to fetch the page. Status code: {response.status_code}")
        return []
    
    # Step 2: Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Step 3: Extract FAQs from JSON-LD script tags
    script_tags = soup.find_all('script', {'type': 'application/ld+json'})
    
    # List to store the extracted FAQs
    faqs = []
    
    print(f"Found {len(script_tags)} script tags with JSON-LD content")
    
    # Loop through each script tag
    for i, script in enumerate(script_tags):
        try:
            # Get the script content
            script_content = script.string
            
            # Print a snippet of the content for debugging
            print(f"\nScript {i+1} preview (first 100 chars): {script_content[:100].strip()}")
            
            # Special handling for the second script tag (index 1) which has JSON issues
            if i == 1:
                print("This is the script tag with FAQ data that had parsing issues.")
                print("Trying a targeted approach to extract questions and answers...")
                
                # Use regex to extract Question/Answer patterns directly
                qa_pattern = r'@type": *"Question"[^}]*"name": *"([^"]*)"[^}]*"acceptedAnswer": *\{[^}]*"text": *"([^"]*)"'
                qa_matches = re.findall(qa_pattern, script_content, re.DOTALL)
                
                if qa_matches:
                    print(f"Found {len(qa_matches)} Q&A pairs using regex pattern matching")
                    for question, answer in qa_matches:
                        faqs.append({
                            "question": question,
                            "answer": answer
                        })
                        print(f"Found FAQ (regex): {question[:50]}...")
                    continue
                    
                # If still no matches, try manually cleaning the JSON
                print("No matches found with regex, trying to clean the JSON...")
                try:
                    cleaned_json = clean_json_ld(script_content)
                    data = json.loads(cleaned_json)
                    print("Successfully cleaned and parsed the JSON!")
                    
                    # Handle FAQPage structure
                    if data.get("@type") == "FAQPage" and "mainEntity" in data:
                        for item in data["mainEntity"]:
                            if item.get("@type") == "Question":
                                question = item.get("name", "")
                                answer = ""
                                if "acceptedAnswer" in item and "text" in item["acceptedAnswer"]:
                                    answer = item["acceptedAnswer"]["text"]
                                
                                faqs.append({
                                    "question": question,
                                    "answer": answer
                                })
                                print(f"Found FAQ (cleaned JSON): {question[:50]}...")
                    continue
                except Exception as e:
                    print(f"Still couldn't parse after cleaning: {e}")
                    # Give up on this script tag and continue to next
                    continue
            
            # For other script tags, try normal parsing
            try:
                # Try to parse as-is first
                data = json.loads(script_content)
                print(f"JSON data type: {type(data)}")
                
                # Process the data based on its structure
                # If data is a list, check each item
                if isinstance(data, list):
                    for item in data:
                        # Check if this item is a Question
                        if isinstance(item, dict) and item.get("@type") == "Question":
                            # Extract the question text
                            question = item.get("name", "")
                            
                            # Extract the answer text
                            answer = ""
                            if "acceptedAnswer" in item and "text" in item["acceptedAnswer"]:
                                answer = item["acceptedAnswer"]["text"]
                            
                            # Add to our FAQs list
                            faqs.append({
                                "question": question,
                                "answer": answer
                            })
                            print(f"Found FAQ: {question[:50]}...")
                
                # If data is a dictionary, check if it's an FAQ page
                elif isinstance(data, dict):
                    # Some websites use the FAQPage schema type
                    if data.get("@type") == "FAQPage" and "mainEntity" in data:
                        for item in data["mainEntity"]:
                            if item.get("@type") == "Question":
                                question = item.get("name", "")
                                answer = ""
                                if "acceptedAnswer" in item and "text" in item["acceptedAnswer"]:
                                    answer = item["acceptedAnswer"]["text"]
                                
                                faqs.append({
                                    "question": question,
                                    "answer": answer
                                })
                                print(f"Found FAQ: {question[:50]}...")
                    # Direct Question type (as in your example)
                    elif data.get("@type") == "Question":
                        question = data.get("name", "")
                        answer = ""
                        if "acceptedAnswer" in data and "text" in data["acceptedAnswer"]:
                            answer = data["acceptedAnswer"]["text"]
                        
                        faqs.append({
                            "question": question,
                            "answer": answer
                        })
                        print(f"Found FAQ: {question[:50]}...")
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                
        except Exception as e:
            print(f"Unexpected error in script {i+1}: {e}")
    
    # If no FAQs found using JSON-LD, try alternative HTML parsing
    if not faqs:
        print("\nNo FAQs found in JSON-LD, trying alternative HTML parsing...")
        faqs = extract_faqs_from_html(soup)
    
    print(f"Extracted {len(faqs)} FAQs from the page")
    return faqs

def extract_faqs_from_html(soup):
    """
    Extract FAQs from the HTML structure as a fallback method.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content
        
    Returns:
        list: A list of dictionaries containing questions and answers
    """
    faqs = []
    
    # Look for elements that might contain FAQs
    # We'll try several common patterns for FAQ sections
    
    # Pattern 1: Look for details/summary elements (HTML5 accordion)
    details_elements = soup.find_all('details')
    if details_elements:
        print(f"Found {len(details_elements)} details elements")
        for details in details_elements:
            summary = details.find('summary')
            if summary:
                question = summary.get_text(strip=True)
                # Get the answer (all text in details except summary)
                summary.extract()  # Temporarily remove summary
                answer = details.get_text(strip=True)
                
                faqs.append({
                    "question": question,
                    "answer": answer
                })
                print(f"Found FAQ (details/summary): {question[:50]}...")
    
    # Pattern 2: Look for elements with specific FAQ-related classes
    faq_elements = soup.select('.faq-item, .accordion-item, .faq-block, .faq-entry')
    if faq_elements:
        print(f"Found {len(faq_elements)} FAQ elements by class")
        for faq in faq_elements:
            q_elem = faq.select_one('.faq-question, .accordion-header, h3, .question')
            a_elem = faq.select_one('.faq-answer, .accordion-content, .answer')
            
            if q_elem and a_elem:
                question = q_elem.get_text(strip=True)
                answer = a_elem.get_text(strip=True)
                
                faqs.append({
                    "question": question,
                    "answer": answer
                })
                print(f"Found FAQ (by class): {question[:50]}...")
    
    # Pattern 3: Look for common heading-paragraph patterns
    headings = soup.find_all(['h2', 'h3', 'h4'])
    for heading in headings:
        # Check if this heading contains question-like text
        heading_text = heading.get_text(strip=True)
        if '?' in heading_text or heading_text.lower().startswith(('what', 'how', 'why', 'when', 'where', 'who', 'can', 'do')):
            # Find the next paragraph or div as the potential answer
            answer_elem = heading.find_next(['p', 'div'])
            if answer_elem:
                answer = answer_elem.get_text(strip=True)
                
                faqs.append({
                    "question": heading_text,
                    "answer": answer
                })
                print(f"Found FAQ (heading pattern): {heading_text[:50]}...")
    
    return faqs

def save_faqs_to_file(faqs, filename="taurbull_faqs.json"):
    """
    Save the extracted FAQs to a JSON file.
    
    Args:
        faqs (list): List of FAQs to save
        filename (str): Name of the file to save to
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(faqs, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(faqs)} FAQs to {filename}")

def main():
    """Main function to run the scraper."""
    print("Simple FAQ Scraper - Starting")
    
    # Scrape the FAQs
    faqs = scrape_faq()
    
    # Save the FAQs to a file
    if faqs:
        save_faqs_to_file(faqs)
    else:
        print("No FAQs were found to save.")
    
    print("Simple FAQ Scraper - Completed")

if __name__ == "__main__":
    main()
