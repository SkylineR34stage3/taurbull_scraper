"""
Simple test script to upload a document to the knowledge base and associate it with an assistant.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.elevenlabs_api import ElevenlabsAPI

def create_and_associate_test_document():
    """Create a test document and associate it with the assistant."""
    api = ElevenlabsAPI()
    
    # Create a test document
    test_content = """
    # TaurBull FAQ
    
    ## About Taurbull
    
    ### What is TaurBull?
    TaurBull is a premium supplier of Black Angus steaks from free-range cattle.
    
    ### Where are TaurBull cattle raised?
    TaurBull cattle are raised on 2,000 hectares of pasture land, ensuring humane and sustainable farming practices.
    
    ## Products
    
    ### What cuts of steak do you offer?
    We offer various premium cuts including Tomahawk, Ribeye, T-Bone, Filet, Rump steak, and specialty cuts.
    
    ### Are your steaks dry-aged?
    Yes, all our steaks are dry-aged for 21 days for maximum flavor and tenderness.
    
    ## Ordering
    
    ### How are the steaks delivered?
    Our steaks are delivered frozen in special insulated packaging to ensure they arrive in perfect condition.
    
    ### Do you ship internationally?
    Currently, we only ship within Germany and selected European countries.
    """
    
    print("Creating test document...")
    response = api.add_text_to_knowledge_base(
        text=test_content,
        name="TaurBull Test FAQ"
    )
    
    document_id = response.get('id')
    if not document_id:
        print("❌ Failed to create document")
        return
    
    print(f"✅ Created document with ID: {document_id}")
    
    # Check if assistant ID is configured
    if not api.assistant_id:
        print("❌ No assistant ID configured")
        return
    
    # Associate the document with the assistant
    print(f"Associating document with assistant ID: {api.assistant_id}...")
    associate_response = api.associate_document_with_assistant(document_id, api.assistant_id)
    
    print("Response:", associate_response)
    
    # Get assistant's knowledge base
    print("Getting assistant's knowledge base...")
    kb_docs = api.get_assistant_knowledge_base()
    
    print(f"Assistant has {len(kb_docs)} associated knowledge base documents:")
    for i, doc in enumerate(kb_docs, 1):
        print(f"  {i}. {doc.get('name', 'Unnamed')} (ID: {doc.get('id', 'Unknown')})")

if __name__ == "__main__":
    create_and_associate_test_document() 