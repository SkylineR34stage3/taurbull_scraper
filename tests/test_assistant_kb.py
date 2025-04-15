"""
Script to test directly accessing an assistant's knowledge base.
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key and assistant ID
api_key = os.environ.get("ELEVENLABS_API_KEY")
assistant_id = os.environ.get("ELEVENLABS_ASSISTANT_ID")

if not api_key:
    print("❌ ERROR: No API key found in .env file")
    exit(1)

if not assistant_id:
    print("❌ ERROR: No assistant ID found in .env file")
    exit(1)

# Headers for API requests
headers = {
    "Accept": "application/json",
    "xi-api-key": api_key
}

# First, get detailed info about the assistant
try:
    print(f"Getting information about assistant ID: {assistant_id}")
    response = requests.get(f"https://api.elevenlabs.io/v1/convai/agents/{assistant_id}", headers=headers)
    response.raise_for_status()
    assistant_data = response.json()
    print(f"✅ Successfully retrieved assistant data:")
    print(json.dumps(assistant_data, indent=2))
except Exception as e:
    print(f"❌ Failed to get assistant data: {e}")
    
# Now try to access the assistant's knowledge base
try:
    print(f"\nGetting knowledge base for assistant ID: {assistant_id}")
    response = requests.get(f"https://api.elevenlabs.io/v1/convai/agents/{assistant_id}/knowledge-base", headers=headers)
    response.raise_for_status()
    kb_data = response.json()
    print(f"✅ Successfully retrieved knowledge base data:")
    print(json.dumps(kb_data, indent=2))
except Exception as e:
    print(f"❌ Failed to get knowledge base: {e}")
    
# Finally, try to add a test document to the assistant's knowledge base
try:
    print(f"\nAdding a test document to the knowledge base...")
    
    # First, create a new document
    content = "This is a test document for TaurBull scraper integration."
    doc_response = requests.post(
        "https://api.elevenlabs.io/v1/convai/knowledge-base/text",
        headers=headers,
        json={"text": content, "name": "Test Document - TaurBull Scraper"}
    )
    doc_response.raise_for_status()
    doc_data = doc_response.json()
    document_id = doc_data.get("id")
    
    if not document_id:
        print("❌ No document ID returned from document creation")
    else:
        print(f"✅ Created test document with ID: {document_id}")
        
        # Now associate the document with the assistant
        print(f"Associating document {document_id} with assistant {assistant_id}...")
        assoc_response = requests.post(
            f"https://api.elevenlabs.io/v1/convai/agents/{assistant_id}/knowledge-base",
            headers=headers,
            json={"document_ids": [document_id]}
        )
        assoc_response.raise_for_status()
        assoc_data = assoc_response.json()
        print(f"✅ Successfully associated document with assistant:")
        print(json.dumps(assoc_data, indent=2))
        
        # Clean up by deleting the test document
        print(f"Cleaning up by deleting test document {document_id}...")
        delete_response = requests.delete(
            f"https://api.elevenlabs.io/v1/convai/knowledge-base/{document_id}",
            headers=headers
        )
        delete_response.raise_for_status()
        print("✅ Successfully deleted test document")
except Exception as e:
    print(f"❌ Failed to add test document: {e}")
    
print("\nTest complete") 