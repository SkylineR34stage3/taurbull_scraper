"""
Knowledge Base Manager

This module manages the integration between our scraper and the Elevenlabs knowledge base,
handling change detection and updates.
"""

import os
import json
import hashlib
import sys
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
from dotenv import load_dotenv

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.elevenlabs_api import ElevenlabsAPI
from src.simple_faq_scraper import scrape_faq, save_faqs_to_file

# Load environment variables from .env file
load_dotenv()

# Configure logging
import logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/kb_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("kb_manager")


class KnowledgeBaseManager:
    """
    Manages the synchronization between scraped content and the Elevenlabs knowledge base.
    """
    def __init__(self, storage_dir: str = "content_cache", api_key: Optional[str] = None, assistant_id: Optional[str] = None):
        """
        Initialize the Knowledge Base Manager.
        
        Args:
            storage_dir (str): Directory to store content and metadata.
            api_key (str, optional): Elevenlabs API key. If not provided, will look for
                                   ELEVENLABS_API_KEY environment variable.
            assistant_id (str, optional): ID of the assistant to associate knowledge base with.
                                         If not provided, will look for ELEVENLABS_ASSISTANT_ID
                                         environment variable.
        """
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize Elevenlabs API
        self.api = ElevenlabsAPI(api_key, assistant_id)
        
        # Load the content map (metadata about tracked content)
        self.content_map_file = os.path.join(storage_dir, "content_map.json")
        self.content_map = self._load_content_map()
        
        # Initialize a document map to keep track of Elevenlabs knowledge base documents
        self.document_map_file = os.path.join(storage_dir, "document_map.json")
        self.document_map = self._load_document_map()
        
    def _load_content_map(self) -> Dict[str, Any]:
        """Load the content map from file."""
        if os.path.exists(self.content_map_file):
            try:
                with open(self.content_map_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading content map: {e}")
                return {}
        return {}
    
    def _save_content_map(self):
        """Save the content map to file."""
        try:
            with open(self.content_map_file, 'w', encoding='utf-8') as f:
                json.dump(self.content_map, f, indent=2)
        except IOError as e:
            logger.error(f"Error saving content map: {e}")
    
    def _load_document_map(self) -> Dict[str, str]:
        """Load the document map from file."""
        if os.path.exists(self.document_map_file):
            try:
                with open(self.document_map_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading document map: {e}")
                return {}
        return {}
    
    def _save_document_map(self):
        """Save the document map to file."""
        try:
            with open(self.document_map_file, 'w', encoding='utf-8') as f:
                json.dump(self.document_map, f, indent=2)
        except IOError as e:
            logger.error(f"Error saving document map: {e}")
    
    def compute_content_hash(self, content: Any) -> str:
        """
        Compute a hash of the content to detect changes.
        
        Args:
            content: The content to hash.
            
        Returns:
            str: SHA-256 hash of the content.
        """
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode('utf-8')).hexdigest()
    
    def has_content_changed(self, page_id: str, content: Any) -> bool:
        """
        Check if content has changed by comparing hashes.
        
        Args:
            page_id: Identifier for the page.
            content: New content to compare.
            
        Returns:
            bool: True if content has changed, False otherwise.
        """
        new_hash = self.compute_content_hash(content)
        
        if page_id not in self.content_map:
            logger.info(f"New page detected: {page_id}")
            return True
        
        current_hash = self.content_map[page_id].get('hash', '')
        if new_hash != current_hash:
            logger.info(f"Content changed for page: {page_id}")
            return True
            
        logger.info(f"No changes detected for page: {page_id}")
        return False
    
    def update_content_map(self, page_id: str, content: Any, document_id: Optional[str] = None) -> None:
        """
        Update the content map with new content and metadata.
        
        Args:
            page_id: Identifier for the page.
            content: The new content.
            document_id: Elevenlabs knowledge base document ID (if applicable).
        """
        content_hash = self.compute_content_hash(content)
        timestamp = datetime.now().isoformat()
        
        if page_id not in self.content_map:
            self.content_map[page_id] = {}
        
        self.content_map[page_id].update({
            'hash': content_hash,
            'last_updated': timestamp,
            'size': len(json.dumps(content))
        })
        
        if document_id:
            self.document_map[page_id] = document_id
            self._save_document_map()
        
        self._save_content_map()
        
        # Save the content to a file
        content_file = os.path.join(self.storage_dir, f"{page_id}_{content_hash[:8]}.json")
        with open(content_file, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
    
    def format_faqs_for_kb(self, faqs: List[Dict[str, str]]) -> str:
        """
        Format FAQs for the knowledge base in a structured way.
        
        Args:
            faqs: List of FAQ dictionaries with 'question' and 'answer' keys.
            
        Returns:
            str: Formatted FAQ text for the knowledge base.
        """
        formatted_text = "# Frequently Asked Questions\n\n"
        
        for i, faq in enumerate(faqs, 1):
            question = faq.get('question', '').strip()
            answer = faq.get('answer', '').strip()
            
            # Clean up the HTML tags if present in the answer
            answer = answer.replace('<p>', '').replace('</p>', '\n')
            
            formatted_text += f"## Q{i}: {question}\n\n{answer}\n\n"
            
        return formatted_text
    
    def update_faq_kb(self) -> Tuple[bool, Optional[str]]:
        """
        Scrape the FAQ page and update the knowledge base if content has changed.
        
        Returns:
            Tuple[bool, Optional[str]]: (success, message) tuple.
        """
        try:
            # Step 1: Scrape the FAQ page
            logger.info("Scraping FAQs from website...")
            faqs = scrape_faq()
            
            if not faqs:
                return False, "No FAQs found on the website."
            
            # Step 2: Check if content has changed
            page_id = "faq"
            if not self.has_content_changed(page_id, faqs):
                return True, "No changes detected in FAQ content. Knowledge base is up to date."
            
            # Step 3: Format the FAQs for the knowledge base
            formatted_faqs = self.format_faqs_for_kb(faqs)
            
            # Step 4: Check if we need to delete an existing document
            if page_id in self.document_map:
                old_document_id = self.document_map[page_id]
                try:
                    logger.info(f"Deleting old FAQ document: {old_document_id}")
                    self.api.delete_knowledge_base_document(old_document_id)
                except Exception as e:
                    logger.warning(f"Error deleting old document {old_document_id}: {e}")
            
            # Step 5: Add the new content to the knowledge base
            logger.info("Adding new FAQ content to knowledge base...")
            response = self.api.add_text_to_knowledge_base(
                text=formatted_faqs,
                name=f"TaurBull FAQ - {datetime.now().strftime('%Y-%m-%d')}"
            )
            
            # Step 6: Update the content map and document map
            new_document_id = response.get('id')
            if new_document_id:
                self.update_content_map(page_id, faqs, new_document_id)
                
                # Log additional information about assistant association
                if self.api.assistant_id:
                    logger.info(f"Document {new_document_id} associated with assistant {self.api.assistant_id}")
                    
                logger.info(f"Successfully updated knowledge base with new document ID: {new_document_id}")
                return True, f"Knowledge base updated successfully. New document ID: {new_document_id}"
            else:
                logger.error("Failed to get document ID from API response")
                return False, "Failed to get document ID from API response"
            
        except Exception as e:
            logger.error(f"Error updating FAQ knowledge base: {e}")
            return False, f"Error updating FAQ knowledge base: {str(e)}"
    
    def list_kb_documents(self) -> List[Dict[str, Any]]:
        """
        List all knowledge base documents.
        
        Returns:
            List[Dict[str, Any]]: List of knowledge base documents.
        """
        try:
            response = self.api.list_knowledge_base()
            return response.get('documents', [])
        except Exception as e:
            logger.error(f"Error listing knowledge base documents: {e}")
            return []
    
    def get_assistant_kb_documents(self) -> List[Dict[str, Any]]:
        """
        Get all knowledge base documents associated with the assistant.
        
        Returns:
            List[Dict[str, Any]]: List of knowledge base documents associated with the assistant.
        """
        if not self.api.assistant_id:
            logger.warning("No assistant ID provided. Cannot get assistant knowledge base documents.")
            return []
            
        try:
            return self.api.get_assistant_knowledge_base()
        except Exception as e:
            logger.error(f"Error getting assistant knowledge base documents: {e}")
            return []
    
    def print_status(self) -> None:
        """
        Print the current status of the knowledge base and assistant.
        """
        logger.info("=== Knowledge Base Status ===")
        
        # Log general knowledge base info
        kb_docs = self.list_kb_documents()
        logger.info(f"Total knowledge base documents: {len(kb_docs)}")
        
        # Log tracked documents
        logger.info(f"Tracked documents: {len(self.document_map)}")
        
        # Log assistant info if available
        if self.api.assistant_id:
            assistant_kb = self.get_assistant_kb_documents()
            logger.info(f"Assistant ID: {self.api.assistant_id}")
            logger.info(f"Documents associated with assistant: {len(assistant_kb)}")
            
            # Log any discrepancies
            tracked_ids = set(self.document_map.values())
            assistant_ids = {doc.get('id') for doc in assistant_kb}
            
            missing_from_assistant = tracked_ids - assistant_ids
            if missing_from_assistant:
                logger.warning(f"Documents tracked but not associated with assistant: {len(missing_from_assistant)}")
                
            extra_in_assistant = assistant_ids - tracked_ids
            if extra_in_assistant:
                logger.info(f"Documents associated with assistant but not tracked: {len(extra_in_assistant)}")

    def update_kb_with_custom_content(self, content_id: str, content: Any, document_name: str, 
                                     formatted_text: Optional[str] = None) -> bool:
        """
        Update the knowledge base with custom content from any scraper.
        
        Args:
            content_id: Unique identifier for the content type
            content: The content to upload (will be used for change detection)
            document_name: Name for the document in the knowledge base
            formatted_text: Optional pre-formatted text, if not provided will use format_faqs_for_kb
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if content has changed
            if not self.has_content_changed(content_id, content):
                logger.info(f"No changes detected in {content_id} content. Knowledge base is up to date.")
                return True
            
            # Format the content if not already formatted
            if formatted_text is None:
                # Assumes content is a list of FAQ dictionaries
                if isinstance(content, list) and all(isinstance(item, dict) for item in content):
                    formatted_text = self.format_faqs_for_kb(content)
                else:
                    logger.error("Cannot format content: Expected a list of dictionaries")
                    return False
            
            # Delete existing document if present
            if content_id in self.document_map:
                old_document_id = self.document_map[content_id]
                try:
                    logger.info(f"Deleting old document: {old_document_id}")
                    self.api.delete_knowledge_base_document(old_document_id)
                except Exception as e:
                    logger.warning(f"Error deleting old document {old_document_id}: {e}")
            
            # Add the new content to the knowledge base
            logger.info(f"Adding new content to knowledge base: {document_name}")
            response = self.api.add_text_to_knowledge_base(
                text=formatted_text,
                name=document_name
            )
            
            # Update the content map and document map
            new_document_id = response.get('id')
            if new_document_id:
                self.update_content_map(content_id, content, new_document_id)
                
                # Log additional information about assistant association
                if self.api.assistant_id:
                    logger.info(f"Document {new_document_id} associated with assistant {self.api.assistant_id}")
                    
                logger.info(f"Successfully updated knowledge base with new document ID: {new_document_id}")
                return True
            else:
                logger.error("Failed to get document ID from API response")
                return False
            
        except Exception as e:
            logger.error(f"Error updating knowledge base with custom content: {e}")
            return False
    
    def export_formatted_faq(self, output_file: str) -> bool:
        """
        Export the formatted FAQ content to a file.
        
        Args:
            output_file: Path to the output file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the latest FAQs
            faqs = scrape_faq()
            
            if not faqs:
                logger.warning("No FAQs found to export")
                return False
            
            # Format the FAQs
            formatted_content = self.format_faqs_for_kb(faqs)
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
                
            logger.info(f"Exported formatted FAQ content to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting formatted FAQ: {e}")
            return False


# Example usage
if __name__ == "__main__":
    manager = KnowledgeBaseManager()
    
    # Print current status
    manager.print_status()
    
    # Update the FAQ knowledge base
    success, message = manager.update_faq_kb()
    print(message)
    
    # Print updated status
    manager.print_status() 