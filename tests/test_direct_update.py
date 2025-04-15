#!/usr/bin/env python3
"""
Test script for directly updating convai agent document content
This bypasses knowledge base APIs and updates the agent configuration directly.
"""

import os
import logging
import sys
import time
import pytest
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_direct_update")

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
def test_direct_update():
    """Test directly updating the document content in a convai agent."""
    
    # Set environment variable for convai agent type
    os.environ["ELEVENLABS_ASSISTANT_TYPE"] = "convai"
    
    # Create API client with debug logging
    api = ElevenlabsAPI()
    
    # Get current time for document name
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Print assistant info
    logger.info(f"Testing with assistant ID: {api.assistant_id}")
    logger.info(f"Assistant type set to: {api.assistant_type}")
    
    # Create test content
    test_content = f"""
    # TaurBull FAQ - Updated {timestamp}
    
    ## About TaurBull
    
    ### What is TaurBull?
    TaurBull is a premium supplier of Black Angus steaks from free-range cattle raised in Romania.
    
    ### What makes TaurBull special?
    Our cattle are raised on 2,000 hectares of natural pasture in Transylvania, allowing them to roam freely and develop exceptional meat quality.
    
    ### How can I order from TaurBull?
    You can order directly from our website at taurbull.com or contact us at hello@taurbull.com.
    
    ## Test Update
    This document was updated via direct agent configuration update at {timestamp}.
    """
    
    # Create document name with timestamp
    document_name = f"TaurBull FAQ - {datetime.now().strftime('%Y-%m-%d')}"
    
    # Try the direct update method
    logger.info(f"Updating document: {document_name}")
    start_time = time.time()
    response = api._update_convai_agent_document(
        text=test_content,
        name=document_name
    )
    
    # Check the response
    assert "error" not in response, f"Update failed: {response}"
    document_id = response.get("id")
    logger.info(f"✅ Update successful. Document ID: {document_id}")
    logger.info(f"Update completed in {time.time() - start_time:.2f} seconds")
    
    # Try to get assistant info to verify the update
    logger.info("Verifying update...")
    assistant_info = api.get_assistant_info()
    
    assert "error" not in assistant_info, f"Failed to get assistant info: {assistant_info}"
    prompt = assistant_info.get("conversation_config", {}).get("agent", {}).get("prompt", {})
    kb_list = prompt.get("knowledge_base", [])
    
    assert kb_list, "No knowledge base entries found in prompt"
    logger.info(f"Found {len(kb_list)} knowledge base entries:")
    for i, kb in enumerate(kb_list, 1):
        logger.info(f"  {i}. {kb.get('name', 'Unknown')} (ID: {kb.get('id', 'Unknown')})")

if __name__ == "__main__":
    test_direct_update()
    sys.exit(0) 