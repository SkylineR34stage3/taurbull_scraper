"""
Elevenlabs API Integration Module

Handles interactions with the Elevenlabs API to manage the knowledge base for TaurBull content.
"""

import os
import json
import time
import logging
import requests
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ElevenlabsAPI:
    """
    Class to handle interactions with the Elevenlabs API
    """
    BASE_URL = "https://api.elevenlabs.io/v1"
    
    def __init__(self, api_key: str, assistant_id: str):
        """
        Initialize the Elevenlabs API client
        
        Args:
            api_key: The Elevenlabs API key
            assistant_id: The ID of the assistant to update the knowledge base for
        """
        self.api_key = api_key
        self.assistant_id = assistant_id
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the Elevenlabs API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint to call
            data: Optional data to send
            
        Returns:
            API response as a dictionary
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data
            )
            
            # Check for rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limited. Waiting for {retry_after} seconds")
                time.sleep(retry_after)
                return self._make_request(method, endpoint, data)
                
            # Handle other error status codes
            if response.status_code >= 400:
                logger.error(f"API error: {response.status_code}, {response.text}")
                return {"error": response.text, "status_code": response.status_code}
                
            # Return JSON response or empty dict if no content
            if response.status_code != 204:  # No content
                return response.json()
            return {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return {"error": str(e)}
            
    def verify_credentials(self) -> bool:
        """
        Verify the API credentials by making a test request
        
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            # Try to get user info as a simple verification
            response = self._make_request("GET", "/user")
            return "error" not in response
        except Exception as e:
            logger.error(f"Error verifying credentials: {e}")
            return False
            
    def get_assistant_info(self) -> Dict[str, Any]:
        """
        Get information about the assistant
        
        Returns:
            Assistant information as a dictionary
        """
        endpoint = f"/assistants/{self.assistant_id}"
        return self._make_request("GET", endpoint)
        
    def get_knowledge_base_id(self) -> Optional[str]:
        """
        Get the knowledge base ID associated with the assistant
        
        Returns:
            Knowledge base ID if found, None otherwise
        """
        assistant_info = self.get_assistant_info()
        
        if "error" in assistant_info:
            logger.error(f"Error getting assistant info: {assistant_info['error']}")
            return None
            
        # Look for knowledge base in assistant configuration
        knowledge_bases = assistant_info.get("knowledge_base_ids", [])
        
        if not knowledge_bases:
            logger.error("No knowledge bases found for this assistant")
            return None
            
        # Return the first knowledge base ID (most assistants only have one)
        return knowledge_bases[0]
        
    def list_documents(self, knowledge_base_id: str) -> List[Dict[str, Any]]:
        """
        List all documents in a knowledge base
        
        Args:
            knowledge_base_id: ID of the knowledge base
            
        Returns:
            List of documents
        """
        endpoint = f"/knowledge-bases/{knowledge_base_id}/documents"
        response = self._make_request("GET", endpoint)
        
        if "error" in response:
            logger.error(f"Error listing documents: {response['error']}")
            return []
            
        return response.get("documents", [])
        
    def add_text_to_knowledge_base(self, kb_id: str, document_name: str, text_content: str) -> Optional[str]:
        """
        Add text content to a knowledge base
        
        Args:
            kb_id: Knowledge base ID
            document_name: Name for the document
            text_content: Text content to add
            
        Returns:
            Document ID if successful, None otherwise
        """
        # First check if a similarly named document already exists
        existing_docs = self.list_documents(kb_id)
        existing_doc_names = [doc.get("name") for doc in existing_docs]
        
        # If document with same name exists, consider updating instead of creating
        similar_docs = [doc for doc in existing_docs if doc.get("name", "").startswith(document_name)]
        
        # If similar document exists, delete it first
        if similar_docs:
            logger.info(f"Found existing document '{similar_docs[0].get('name')}'. Deleting before upload.")
            self._delete_document(kb_id, similar_docs[0].get("id"))
        
        # Now add the new document
        endpoint = f"/knowledge-bases/{kb_id}/upload-text"
        
        data = {
            "name": document_name,
            "text": text_content
        }
        
        response = self._make_request("POST", endpoint, data)
        
        if "error" in response:
            logger.error(f"Error adding text to knowledge base: {response['error']}")
            return None
            
        # Return the document ID
        return response.get("document_id")
        
    def _delete_document(self, kb_id: str, document_id: str) -> bool:
        """
        Delete a document from a knowledge base
        
        Args:
            kb_id: Knowledge base ID
            document_id: Document ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        endpoint = f"/knowledge-bases/{kb_id}/documents/{document_id}"
        response = self._make_request("DELETE", endpoint)
        
        if "error" in response:
            logger.error(f"Error deleting document: {response['error']}")
            return False
            
        return True 