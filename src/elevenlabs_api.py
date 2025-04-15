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
from datetime import datetime

logger = logging.getLogger(__name__)

class ElevenlabsAPI:
    """
    Class to handle interactions with the Elevenlabs API
    """
    BASE_URL = "https://api.elevenlabs.io/v1"
    
    def __init__(self, api_key: str = None, assistant_id: str = None):
        """
        Initialize the Elevenlabs API client
        
        Args:
            api_key: The Elevenlabs API key
            assistant_id: The ID of the assistant to update the knowledge base for
        """
        # Use environment variables as fallback if not provided
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        self.assistant_id = assistant_id or os.environ.get("ELEVENLABS_ASSISTANT_ID")
        
        # Check for assistant type environment variable
        self.assistant_type = os.environ.get("ELEVENLABS_ASSISTANT_TYPE", "").lower()
        
        if not self.api_key:
            logger.error("No API key provided and ELEVENLABS_API_KEY environment variable not set")
            
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
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
            
    def get_assistant_info(self, assistant_id: str = None) -> Dict[str, Any]:
        """
        Get information about the assistant
        
        Args:
            assistant_id: Optional assistant ID, falls back to self.assistant_id if not provided
            
        Returns:
            Assistant information as a dictionary
        """
        # Use provided assistant_id or fallback to instance variable
        assistant_id = assistant_id or self.assistant_id
        if not assistant_id:
            logger.error("No assistant ID provided")
            return {"error": "No assistant ID provided"}
        
        # Try multiple endpoints to handle different assistant types
        endpoints = []
        
        # Prioritize endpoints based on assistant type if set
        if self.assistant_type == "convai":
            endpoints = [
                f"/convai/agents/{assistant_id}",  # Check convai endpoints first
                f"/assistants/{assistant_id}",
                f"/phone-assistants/{assistant_id}"
            ]
        else:
            endpoints = [
                f"/assistants/{assistant_id}",  # Standard assistants
                f"/convai/agents/{assistant_id}",  # Regular assistants
                f"/phone-assistants/{assistant_id}"  # Phone assistants
            ]
        
        for endpoint in endpoints:
            response = self._make_request("GET", endpoint)
            if "error" not in response:
                return response
            
        # If all endpoints failed, return the last error
        logger.error(f"Error getting assistant info: {response}")
        return response
        
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
            
        # Look for knowledge base IDs in various places in the assistant configuration
        knowledge_bases = []
        
        # For convai agents, check the prompt's knowledge_base field first if that's our type
        if self.assistant_type == "convai":
            try:
                # Get knowledge base info from prompt (for convai agents)
                prompt = assistant_info.get("conversation_config", {}).get("agent", {}).get("prompt", {})
                if prompt and "knowledge_base" in prompt:
                    kb_list = prompt.get("knowledge_base", [])
                    if kb_list and isinstance(kb_list, list) and len(kb_list) > 0:
                        # Extract IDs from knowledge base items
                        knowledge_bases = [kb.get("id") for kb in kb_list if kb.get("id")]
                        if knowledge_bases:
                            logger.info(f"Found knowledge base IDs in prompt section: {knowledge_bases}")
                            return knowledge_bases[0]
            except Exception as e:
                logger.error(f"Error parsing knowledge base from conversation config: {e}")

        # 1. Standard field for regular assistants
        if not knowledge_bases:
            knowledge_bases = assistant_info.get("knowledge_base_ids", [])
        
        # 2. Alternative field for some assistant types
        if not knowledge_bases:
            knowledge_bases = assistant_info.get("knowledge_base", {}).get("ids", [])
        
        # 3. Check in conversation_config > agent > prompt > knowledge_base (for convai agents)
        if not knowledge_bases:
            try:
                # Navigate through the nested structure
                prompt = assistant_info.get("conversation_config", {}).get("agent", {}).get("prompt", {})
                if prompt and "knowledge_base" in prompt:
                    kb_list = prompt.get("knowledge_base", [])
                    if kb_list and isinstance(kb_list, list) and len(kb_list) > 0:
                        # Extract IDs from knowledge base items
                        knowledge_bases = [kb.get("id") for kb in kb_list if kb.get("id")]
                        logger.info(f"Found knowledge base IDs in prompt section: {knowledge_bases}")
            except Exception as e:
                logger.error(f"Error parsing knowledge base from conversation config: {e}")
        
        # 4. Check in prompt > items for knowledge_base type (for newer assistants)
        if not knowledge_bases:
            try:
                prompt_items = assistant_info.get("prompt", {}).get("items", [])
                for item in prompt_items:
                    if item.get("type") == "knowledge_base":
                        kb_id = item.get("knowledge_base_id")
                        if kb_id:
                            knowledge_bases.append(kb_id)
                            logger.info(f"Found knowledge base ID in prompt items: {kb_id}")
            except Exception as e:
                logger.error(f"Error parsing knowledge base from prompt items: {e}")
        
        if not knowledge_bases:
            logger.error("No knowledge bases found for this assistant")
            return None
            
        # Return the first knowledge base ID (most assistants only have one)
        return knowledge_bases[0]
        
    def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """
        List all knowledge bases
        
        Returns:
            List of knowledge bases
        """
        # Try multiple endpoints
        endpoints = []
        
        # Prioritize endpoints based on assistant type
        if self.assistant_type == "convai":
            endpoints = [
                "/convai/knowledge-base",
                "/knowledge-bases"
            ]
        else:
            endpoints = [
                "/knowledge-bases",
                "/convai/knowledge-base"
            ]
        
        for endpoint in endpoints:
            response = self._make_request("GET", endpoint)
            if "error" not in response:
                # Handle different response formats
                if "knowledge_bases" in response:
                    return response.get("knowledge_bases", [])
                elif isinstance(response, list):
                    return response
                else:
                    return [response]  # Single knowledge base in response
                
        logger.error("Failed to list knowledge bases")
        return []
        
    # Keep for backwards compatibility
    def list_knowledge_base(self) -> Dict[str, Any]:
        """
        List all knowledge bases (legacy method)
        
        Returns:
            Dictionary with knowledge base info
        """
        kbs = self.list_knowledge_bases()
        if kbs:
            return {"knowledge_bases": kbs}
        return {"error": "Failed to list knowledge bases", "documents": []}
        
    def get_assistant_kb_documents(self, assistant_id: str = None) -> List[Dict[str, Any]]:
        """
        Get the knowledge base documents associated with the assistant
        
        Args:
            assistant_id: Optional assistant ID, falls back to self.assistant_id if not provided
            
        Returns:
            List of knowledge base documents
        """
        # Use provided assistant_id or fallback to instance variable
        assistant_id = assistant_id or self.assistant_id
        if not assistant_id:
            logger.error("No assistant ID provided")
            return []
            
        # First try to get knowledge base ID
        kb_id = self.get_knowledge_base_id()
        if kb_id:
            # If we have a KB ID, list its documents
            documents = self.list_kb_documents(kb_id)
            if documents:
                return documents
        
        # If that fails, try endpoints for different assistant types
        endpoints = [
            f"/assistants/{assistant_id}/knowledge-base",
            f"/convai/agents/{assistant_id}/knowledge-base",
            f"/phone-assistants/{assistant_id}/knowledge-base"
        ]
        
        for endpoint in endpoints:
            response = self._make_request("GET", endpoint)
            if "error" not in response:
                return response.get("documents", [])
        
        # If all direct attempts fail, try to extract from assistant info
        assistant_info = self.get_assistant_info(assistant_id)
        if "error" not in assistant_info:
            try:
                # Get knowledge base info from prompt (for convai agents)
                prompt = assistant_info.get("conversation_config", {}).get("agent", {}).get("prompt", {})
                if prompt and "knowledge_base" in prompt:
                    kb_list = prompt.get("knowledge_base", [])
                    if kb_list and isinstance(kb_list, list):
                        # Return the knowledge base items directly
                        return kb_list
                
                # Try newer assistant format with items array
                prompt_items = assistant_info.get("prompt", {}).get("items", [])
                kb_entries = [item for item in prompt_items if item.get("type") == "knowledge_base"]
                if kb_entries:
                    # Get knowledge base ID from the first KB entry
                    for entry in kb_entries:
                        if "knowledge_base_id" in entry:
                            kb_id = entry["knowledge_base_id"]
                            documents = self.list_kb_documents(kb_id)
                            if documents:
                                return documents
            except Exception as e:
                logger.error(f"Error extracting knowledge base from assistant info: {e}")
        
        logger.error("Failed to get assistant knowledge base documents")
        return []
    
    # Keep for backwards compatibility
    def get_assistant_knowledge_base(self) -> List[Dict[str, Any]]:
        """
        Get the knowledge base documents associated with the assistant (legacy method)
        
        Returns:
            List of knowledge base documents
        """
        return self.get_assistant_kb_documents()
        
    def list_kb_documents(self, knowledge_base_id: str) -> List[Dict[str, Any]]:
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
            # Try alternative endpoint format
            endpoint = f"/convai/knowledge-base/{knowledge_base_id}/documents"
            response = self._make_request("GET", endpoint)
            
            if "error" in response:
                logger.error(f"Error listing documents: {response.get('error')}")
                return []
        
        # Handle different response formats
        if "documents" in response:
            return response.get("documents", [])
        elif isinstance(response, list):
            return response
        else:
            return []
            
    # Keep for backwards compatibility
    def list_documents(self, knowledge_base_id: str) -> List[Dict[str, Any]]:
        """
        List all documents in a knowledge base (legacy method)
        
        Args:
            knowledge_base_id: ID of the knowledge base
            
        Returns:
            List of documents
        """
        return self.list_kb_documents(knowledge_base_id)
        
    def add_text_to_knowledge_base(self, text: str, name: str) -> Dict[str, Any]:
        """
        Add text content to a knowledge base
        
        Args:
            text: Text content to add
            name: Name for the document
            
        Returns:
            Response containing the document ID
        """
        # For convai agents, try to directly update the document in the agent's prompt
        if self.assistant_type == "convai":
            return self._update_convai_agent_document(text, name)
        
        # Continue with normal knowledge base upload for other assistant types
        # First try with existing endpoint methods
        kb_id = self.get_knowledge_base_id()
        
        # If we have a knowledge base ID, try to use standard upload methods
        if kb_id:
            # Try different endpoint formats for uploading
            endpoints = []
            
            endpoints = [
                f"/knowledge-bases/{kb_id}/upload-text",
                f"/convai/knowledge-base/{kb_id}/upload-text"
            ]
            
            data = {
                "name": name,
                "text": text
            }
            
            for endpoint in endpoints:
                response = self._make_request("POST", endpoint, data)
                if "error" not in response:
                    logger.info(f"Successfully added text to knowledge base using endpoint: {endpoint}")
                    return response
                else:
                    logger.error(f"Failed to add text using endpoint {endpoint}: {response.get('error', 'Unknown error')}")
        else:
            logger.error("No knowledge base ID found, trying alternative methods")
        
        # If standard methods failed, try to find existing documents
        kb_response = self.list_knowledge_base()
        if "error" not in kb_response:
            # For convai API
            documents = kb_response.get("documents", [])
            if documents:
                # Use document ID directly
                document_id = self._update_existing_document(documents[0].get("id"), text, name)
                if document_id:
                    logger.info(f"Successfully updated existing document: {document_id}")
                    return {"id": document_id}
        
        # Try a direct upload to a knowledge base (without specifying a KB ID)
        try:
            endpoint = "/convai/knowledge-base/upload-text"
            data = {
                "name": name,
                "text": text
            }
            response = self._make_request("POST", endpoint, data)
            if "error" not in response:
                doc_id = response.get("id")
                if doc_id:
                    logger.info(f"Successfully created document with ID: {doc_id}")
                    
                    # Try to associate with the assistant
                    if self.assistant_id:
                        self._associate_convai_document(doc_id)
                        
                    return {"id": doc_id}
        except Exception as e:
            logger.error(f"Error with direct upload: {e}")
        
        # If all methods have failed, log the error
        logger.error("Failed to add text to knowledge base using any available method")
        return {"error": "Failed to add text to knowledge base"}
        
    def _update_convai_agent_document(self, text: str, name: str) -> Dict[str, Any]:
        """
        Update document content directly in a convai agent by updating the agent configuration.
        This is a direct approach that bypasses knowledge base endpoints.
        
        Args:
            text: Document text content
            name: Document name
            
        Returns:
            Dictionary with document ID if successful
        """
        logger.info("Attempting to directly update convai agent document")
        try:
            # Get the assistant info first
            assistant_info = self.get_assistant_info()
            if "error" in assistant_info:
                logger.error(f"Failed to get assistant info: {assistant_info}")
                return {"error": "Failed to get assistant info"}
            
            # Get the knowledge base entries from the prompt
            prompt = assistant_info.get("conversation_config", {}).get("agent", {}).get("prompt", {})
            kb_list = prompt.get("knowledge_base", [])
            
            # Extract document type from name (e.g., "TaurBull_FAQ", "TaurBull_Products")
            # This allows for different document types to be managed separately
            doc_type = None
            if "_" in name:
                doc_type = name.split("_")[1].split(" ")[0].lower()  # Extract type (FAQ, Products, etc.)
            
            # If there's an existing document with the same type, use its ID
            document_id = None
            for kb in kb_list:
                kb_name = kb.get("name", "")
                
                # Check if this is the same type of document
                if doc_type and "_" in kb_name and doc_type.lower() in kb_name.lower():
                    document_id = kb.get("id")
                    logger.info(f"Found existing document ID for {doc_type}: {document_id}")
                    break
                # Fallback to exact name match
                elif kb_name == name:
                    document_id = kb.get("id")
                    logger.info(f"Found existing document ID with exact name match: {document_id}")
                    break
            
            # If no document found, generate a placeholder ID 
            if not document_id:
                # Use a timestamp-based ID if none exists
                import uuid
                document_id = f"placeholder_{str(uuid.uuid4())[:8]}"
                logger.info(f"Created placeholder document ID: {document_id}")
            
            # Create updated knowledge base entry
            new_kb_entry = {
                "type": "text",
                "name": name,
                "id": document_id,
                "usage_mode": "auto"
            }
            
            # Create a new knowledge base list with our updated document
            new_kb_list = []
            
            # Add our updated document first
            new_kb_list.append(new_kb_entry)
            
            # Keep other entries that don't match our document type or ID
            for kb in kb_list:
                kb_name = kb.get("name", "")
                
                # Only skip documents with the same ID or same document type
                if kb.get("id") == document_id:
                    continue
                elif doc_type and "_" in kb_name and doc_type.lower() in kb_name.lower():
                    logger.info(f"Replacing document with same type: {kb_name}")
                    continue
                else:
                    # Keep all other documents
                    new_kb_list.append(kb)
            
            # Create the update data
            update_data = {
                "conversation_config": {
                    "agent": {
                        "prompt": {
                            "knowledge_base": new_kb_list,
                            "rag": {
                                "enabled": True
                            }
                        }
                    }
                },
                "knowledge_base_text": {
                    document_id: text
                }
            }
            
            # Send the update
            logger.info(f"Updating agent with new document content (ID: {document_id}, Type: {doc_type or 'Unknown'})")
            update_endpoint = f"/convai/agents/{self.assistant_id}"
            response = self._make_request("PATCH", update_endpoint, update_data)
            
            if "error" not in response:
                logger.info(f"Successfully updated convai agent document content")
                return {"id": document_id}
            else:
                logger.error(f"Failed to update agent: {response}")
                return {"error": f"Failed to update agent: {response}"}
                
        except Exception as e:
            logger.error(f"Error updating convai agent document: {e}")
            return {"error": f"Error updating convai agent document: {e}"}
        
    def _update_existing_document(self, document_id: str, text: str, name: str) -> Optional[str]:
        """
        Update an existing document instead of creating a new one
        
        Args:
            document_id: ID of the document to update
            text: New text content
            name: New name
            
        Returns:
            Document ID if successful, None otherwise
        """
        try:
            # Get current KB ID 
            kb_response = self.list_knowledge_base()
            if "error" in kb_response:
                return None
                
            # Try the update endpoint
            endpoint = f"/convai/knowledge-base/documents/{document_id}"
            data = {
                "name": name,
                "text": text
            }
            
            response = self._make_request("PATCH", endpoint, data)
            if "error" not in response:
                logger.info(f"Successfully updated existing document: {document_id}")
                return document_id
                
            logger.error(f"Failed to update document: {response.get('error')}")
            return None
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return None
            
    def delete_knowledge_base_document(self, document_id: str) -> bool:
        """
        Delete a document from a knowledge base
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        # Try different endpoint formats
        endpoints = [
            f"/knowledge-bases/{self.get_knowledge_base_id()}/documents/{document_id}",
            f"/convai/knowledge-base/documents/{document_id}"
        ]
        
        for endpoint in endpoints:
            response = self._make_request("DELETE", endpoint)
            if "error" not in response:
                return True
            
        logger.error(f"Error deleting document: {response.get('error')}")
        return False
        
    def _update_assistant_knowledge_base(self, new_doc_id: str, old_doc_id: str = None) -> bool:
        """
        Update the assistant's knowledge base configuration
        
        Args:
            new_doc_id: New document ID to use
            old_doc_id: Old document ID to replace (if applicable)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the assistant info
            assistant_info = self.get_assistant_info()
            if "error" in assistant_info:
                return False
                
            # Check if we're dealing with a convai agent
            if "conversation_config" in assistant_info:
                # Build the update data
                update_data = {
                    "conversation_config": {
                        "agent": {
                            "prompt": {
                                "knowledge_base": [
                                    {
                                        "type": "text",
                                        "name": f"TaurBull FAQ - {datetime.now().strftime('%Y-%m-%d')}",
                                        "id": new_doc_id,
                                        "usage_mode": "auto"
                                    }
                                ]
                            }
                        }
                    }
                }
                
                # Send the update
                update_endpoint = f"/convai/agents/{self.assistant_id}"
                response = self._make_request("PATCH", update_endpoint, update_data)
                
                if "error" not in response:
                    logger.info(f"Successfully updated assistant knowledge base to use document: {new_doc_id}")
                    return True
                    
                logger.error(f"Failed to update assistant knowledge base: {response.get('error')}")
                return False
                
            # For standard assistants
            elif "knowledge_base_ids" in assistant_info:
                # Get current IDs
                kb_ids = assistant_info.get("knowledge_base_ids", [])
                
                # Replace old ID with new one if it exists
                if old_doc_id and old_doc_id in kb_ids:
                    kb_ids = [new_doc_id if id == old_doc_id else id for id in kb_ids]
                else:
                    kb_ids.append(new_doc_id)
                
                # Build update data
                update_data = {
                    "knowledge_base_ids": kb_ids
                }
                
                # Send the update
                update_endpoint = f"/assistants/{self.assistant_id}"
                response = self._make_request("PATCH", update_endpoint, update_data)
                
                if "error" not in response:
                    logger.info(f"Successfully updated assistant knowledge base IDs: {kb_ids}")
                    return True
                
                logger.error(f"Failed to update assistant knowledge base IDs: {response.get('error')}")
                return False
                
            logger.error("Unsupported assistant type for updating knowledge base")
            return False
            
        except Exception as e:
            logger.error(f"Error updating assistant knowledge base: {e}")
            return False
            
    def _associate_convai_document(self, document_id: str) -> bool:
        """
        Associate a document with a convai agent
        
        Args:
            document_id: ID of the document to associate
            
        Returns:
            True if successful, False otherwise
        """
        if not self.assistant_id:
            logger.error("No assistant ID provided for association")
            return False
            
        try:
            # Get the assistant info
            assistant_info = self.get_assistant_info()
            if "error" in assistant_info:
                logger.error(f"Failed to get assistant info: {assistant_info.get('error')}")
                return False
                
            # Check if this is a convai agent
            if "conversation_config" in assistant_info:
                # Build the update data - careful not to overwrite existing fields
                prompt = assistant_info.get("conversation_config", {}).get("agent", {}).get("prompt", {})
                kb_list = prompt.get("knowledge_base", [])
                
                # Prepare new knowledge base list with the new document added
                new_kb_list = [
                    {
                        "type": "text",
                        "name": f"TaurBull FAQ - {datetime.now().strftime('%Y-%m-%d')}",
                        "id": document_id,
                        "usage_mode": "auto"
                    }
                ]
                
                # Keep existing documents except if they have the same name pattern
                for kb in kb_list:
                    if kb.get("id") != document_id and not kb.get("name", "").startswith("TaurBull FAQ"):
                        new_kb_list.append(kb)
                
                # Build the update data
                update_data = {
                    "conversation_config": {
                        "agent": {
                            "prompt": {
                                "knowledge_base": new_kb_list
                            }
                        }
                    }
                }
                
                # Send the update
                update_endpoint = f"/convai/agents/{self.assistant_id}"
                response = self._make_request("PATCH", update_endpoint, update_data)
                
                if "error" not in response:
                    logger.info(f"Successfully associated document {document_id} with assistant {self.assistant_id}")
                    return True
                else:
                    logger.error(f"Failed to associate document: {response.get('error')}")
                    
            return False
            
        except Exception as e:
            logger.error(f"Error associating document with assistant: {e}")
            return False

    def associate_document_with_assistant(self, document_id: str, assistant_id: str = None) -> Dict[str, Any]:
        """
        Associate a document with an assistant
        
        Args:
            document_id: ID of the document to associate
            assistant_id: Optional assistant ID, falls back to self.assistant_id if not provided
            
        Returns:
            Response from the API
        """
        assistant_id = assistant_id or self.assistant_id
        if not assistant_id:
            logger.error("No assistant ID provided")
            return {"error": "No assistant ID provided"}
            
        # For convai agents, use the special method
        if self.assistant_type == "convai":
            if self._associate_convai_document(document_id):
                return {"success": True}
            else:
                return {"error": "Failed to associate document with convai agent"}
                
        # Try different endpoints based on assistant type
        endpoints = []
        
        if self.assistant_type == "phone":
            endpoints.append(f"/phone-assistants/{assistant_id}/knowledge-base/documents/{document_id}")
        else:
            endpoints.extend([
                f"/assistants/{assistant_id}/knowledge-base/documents/{document_id}",
                f"/convai/agents/{assistant_id}/knowledge-base/documents/{document_id}"
            ])
            
        for endpoint in endpoints:
            response = self._make_request("POST", endpoint, {})
            if "error" not in response:
                logger.info(f"Successfully associated document {document_id} with assistant {assistant_id}")
                return response
        
        logger.error(f"Failed to associate document with assistant using standard endpoints")
        return {"error": "Failed to associate document with assistant"} 