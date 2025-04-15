"""
Elevenlabs Integration Test Script

This script tests the connection to the Elevenlabs API and verifies
that the scraper can properly integrate with the knowledge base and assistants.
"""

import os
import json
import logging
import argparse
import requests
import sys
import pytest
from dotenv import load_dotenv

# Add parent directory to path for imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

try:
    from src.elevenlabs_api import ElevenlabsAPI
except ImportError as e:
    logging.error(f"Error importing ElevenlabsAPI: {e}")
    logging.error(f"Python path: {sys.path}")
    raise

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_integration")

# Load environment variables
load_dotenv()

@pytest.fixture
def api():
    """Create an API connection fixture for tests."""
    try:
        api_instance = ElevenlabsAPI()
        logger.info("✅ API Connection: Successfully connected to Elevenlabs API")
        return api_instance
    except Exception as e:
        logger.error(f"❌ API Connection: Failed to connect to Elevenlabs API - {str(e)}")
        return None

def test_api_connection():
    """Test the connection to the Elevenlabs API."""
    api_instance = ElevenlabsAPI()
    assert api_instance is not None, "Failed to create API connection"
    logger.info("✅ API Connection: Successfully connected to Elevenlabs API")

def test_knowledge_base_access(api):
    """Test access to the knowledge base."""
    if not api:
        logger.error("⏩ Knowledge Base Access: Skipped due to API connection failure")
        return

    try:
        kb_docs = api.list_knowledge_base()
        count = len(kb_docs.get('documents', []))
        logger.info(f"✅ Knowledge Base Access: Successfully retrieved {count} documents")
        
        # Print document names if any exist
        if count > 0:
            logger.info("📄 Knowledge Base Documents:")
            for i, doc in enumerate(kb_docs.get('documents', []), 1):
                logger.info(f"  {i}. {doc.get('name', 'Unnamed')} (ID: {doc.get('id', 'Unknown')})")
    except Exception as e:
        logger.error(f"❌ Knowledge Base Access: Failed to access knowledge base - {str(e)}")

def test_assistant_integration(api):
    """Test the integration with the assistant."""
    if not api:
        logger.error("⏩ Assistant Integration: Skipped due to API connection failure")
        return

    if not api.assistant_id:
        logger.warning("⚠️ Assistant Integration: No assistant ID configured in .env file or environment")
        return

    try:
        # Get assistant's knowledge base documents
        assistant_docs = api.get_assistant_knowledge_base()
        count = len(assistant_docs)
        logger.info(f"✅ Assistant Integration: Successfully retrieved {count} documents for assistant {api.assistant_id}")
        
        # Print document names if any exist
        if count > 0:
            logger.info("📄 Assistant Knowledge Base Documents:")
            for i, doc in enumerate(assistant_docs, 1):
                logger.info(f"  {i}. {doc.get('name', 'Unnamed')} (ID: {doc.get('id', 'Unknown')})")
    except Exception as e:
        logger.error(f"❌ Assistant Integration: Failed to access assistant's knowledge base - {str(e)}")

def test_small_update(api):
    """Test creating a small knowledge base document."""
    if not api:
        logger.error("⏩ Small Update Test: Skipped due to API connection failure")
        return

    try:
        # Create a small test document
        test_content = "# Test Document\n\nThis is a test document created by the TaurBull Scraper integration test."
        response = api.add_text_to_knowledge_base(
            text=test_content,
            name=f"Test Document - TaurBull Scraper"
        )
        
        document_id = response.get('id')
        if document_id:
            logger.info(f"✅ Small Update Test: Successfully created test document with ID {document_id}")
            
            # Clean up by deleting the test document
            api.delete_knowledge_base_document(document_id)
            logger.info(f"✅ Cleanup: Successfully deleted test document with ID {document_id}")
        else:
            logger.error("❌ Small Update Test: Failed to get document ID from API response")
    except Exception as e:
        logger.error(f"❌ Small Update Test: Failed to create test document - {str(e)}")

def test_api_key_permissions(api):
    """Test the permissions of the API key."""
    if not api:
        logger.error("⏩ API Key Permissions Test: Skipped due to API connection failure")
        return

    try:
        # Test API key permissions by hitting a simple endpoint
        response = requests.get(
            "https://api.elevenlabs.io/v1/user",
            headers={"xi-api-key": api.api_key}
        )
        response.raise_for_status()
        user_data = response.json()
        
        # Log user subscription info
        subscription = user_data.get("subscription", {})
        tier = subscription.get("tier", "Unknown")
        logger.info(f"✅ API Key Permissions: Valid key for account with tier: {tier}")
        
        # Check if account has phone assistant capabilities
        has_phone_assistants = subscription.get("phone_ai", False)
        if has_phone_assistants:
            logger.info(f"✅ Phone Assistants: Account has phone assistant capabilities")
        else:
            logger.warning(f"⚠️ Phone Assistants: Account may not have phone assistant capabilities")
            
    except Exception as e:
        logger.error(f"❌ API Key Permissions: Failed to check API key permissions - {str(e)}")

def test_phone_assistant(api):
    """Test specific phone assistant functionality."""
    if not api:
        logger.error("⏩ Phone Assistant Test: Skipped due to API connection failure")
        return

    if not api.assistant_id:
        logger.warning("⚠️ Phone Assistant Test: No assistant ID configured")
        return
        
    if len(api.assistant_id) >= 36:
        logger.warning(f"⚠️ Phone Assistant Test: ID format ({api.assistant_id}) doesn't appear to be a phone assistant ID")
        return

    try:
        # Try to get phone assistant info
        response = requests.get(
            f"https://api.elevenlabs.io/v1/phone-assistants/{api.assistant_id}",
            headers=api.headers
        )
        response.raise_for_status()
        assistant_data = response.json()
        
        logger.info(f"✅ Phone Assistant: Found phone assistant with name: {assistant_data.get('name', 'Unknown')}")
        
        # Check if the assistant has phone numbers
        if "phone_numbers" in assistant_data:
            numbers = assistant_data.get("phone_numbers", [])
            logger.info(f"✅ Phone Assistant: Has {len(numbers)} phone numbers assigned")
        
        return assistant_data
    except Exception as e:
        logger.error(f"❌ Phone Assistant: Failed to get phone assistant info - {str(e)}")
        return None

def display_configuration():
    """Display the current configuration."""
    logger.info("==== Current Configuration ====")
    logger.info(f"API Key: {'✅ Set' if os.environ.get('ELEVENLABS_API_KEY') else '❌ Not Set'}")
    logger.info(f"Assistant ID: {os.environ.get('ELEVENLABS_ASSISTANT_ID') or '❌ Not Set'}")
    logger.info(f"Update Interval: {os.environ.get('UPDATE_INTERVAL') or '24 (default)'} hours")
    logger.info("=============================")

def main():
    """Run all tests."""
    parser = argparse.ArgumentParser(description="Test Elevenlabs integration")
    parser.add_argument("--list-assistants", action="store_true", help="List all available assistants")
    args = parser.parse_args()
    
    logger.info("==== TaurBull Scraper - Elevenlabs Integration Test ====")
    
    # Display configuration
    display_configuration()
    
    # Connect to API
    api = test_api_connection()
    
    # If --list-assistants flag is used, list all assistants and exit
    if args.list_assistants and api:
        try:
            # Try to list regular assistants first
            try:
                response = requests.get(
                    "https://api.elevenlabs.io/v1/convai/agents",
                    headers=api.headers
                )
                response.raise_for_status()
                assistants = response.json().get("agents", [])
                if assistants:
                    logger.info(f"Found {len(assistants)} regular assistants:")
                    for i, assistant in enumerate(assistants, 1):
                        logger.info(f"  {i}. {assistant.get('name', 'Unnamed')} (ID: {assistant.get('id', 'Unknown')})")
            except Exception as e:
                logger.error(f"Failed to list regular assistants: {str(e)}")
            
            # Try to list phone assistants
            try:
                response = requests.get(
                    "https://api.elevenlabs.io/v1/phone-assistants",
                    headers=api.headers
                )
                response.raise_for_status()
                phone_assistants = response.json().get("phone_assistants", [])
                if phone_assistants:
                    logger.info(f"Found {len(phone_assistants)} phone assistants:")
                    for i, assistant in enumerate(phone_assistants, 1):
                        logger.info(f"  {i}. {assistant.get('name', 'Unnamed')} (ID: {assistant.get('id', 'Unknown')})")
            except Exception as e:
                logger.error(f"Failed to list phone assistants: {str(e)}")
                
        except Exception as e:
            logger.error(f"Failed to list assistants: {str(e)}")
        return
    
    # Run tests
    if api:
        # Run tests
        test_knowledge_base_access(api)
        test_api_key_permissions(api)
        test_phone_assistant(api)
        test_assistant_integration(api)
        test_small_update(api)
    
    logger.info("==== Test Complete ====")

if __name__ == "__main__":
    main() 