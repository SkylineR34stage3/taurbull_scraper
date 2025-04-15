#!/usr/bin/env python3
"""
Test script for uploading content to Elevenlabs convai agent knowledge base
"""

import os
import logging
import sys
import pytest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_convai_upload")

# Add parent directory to path for imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

try:
    from src.elevenlabs_api import ElevenlabsAPI
except ImportError as e:
    logger.error(f"Error importing ElevenlabsAPI: {e}")
    logger.error(f"Python path: {sys.path}")
    raise

@pytest.mark.skip(reason="Requires actual Elevenlabs API credentials")
def test_convai_upload():
    """Test uploading content to a convai agent knowledge base."""
    
    # Set environment variable for convai agent type
    os.environ["ELEVENLABS_ASSISTANT_TYPE"] = "convai"
    
    # Create API client
    api = ElevenlabsAPI()
    
    # Print assistant info
    logger.info(f"Testing with assistant ID: {api.assistant_id}")
    logger.info(f"Assistant type set to: {api.assistant_type}")
    
    # Create a small test document
    test_content = """
    # TaurBull FAQ Test
    
    ## About
    
    ### What is this test?
    This is a test document for the convai agent knowledge base upload.
    
    ### Why is this important?
    It helps verify that the API integration is working correctly for convai agents.
    """
    
    # Upload the document
    logger.info("Uploading test document...")
    response = api.add_text_to_knowledge_base(
        text=test_content,
        name=f"TaurBull Test - Convai"
    )
    
    # Check the response
    document_id = response.get('id')
    assert document_id, f"Upload failed: {response}"
    logger.info(f"✅ Upload successful. Document ID: {document_id}")
    
    # Get knowledge base documents
    logger.info("Checking knowledge base documents...")
    documents = api.get_assistant_kb_documents()
    
    logger.info(f"Found {len(documents)} documents associated with assistant")
    for i, doc in enumerate(documents, 1):
        logger.info(f"  {i}. {doc.get('name', 'Unknown')} (ID: {doc.get('id', 'Unknown')})")
    
    assert len(documents) > 0, "No documents found associated with the assistant"

if __name__ == "__main__":
    success = test_convai_upload()
    sys.exit(0 if success else 1) 