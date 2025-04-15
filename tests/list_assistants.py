"""
Script to list available Elevenlabs assistants.
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.environ.get("ELEVENLABS_API_KEY")
if not api_key:
    print("❌ ERROR: No API key found in .env file")
    exit(1)

# Headers for API requests
headers = {
    "Accept": "application/json",
    "xi-api-key": api_key
}

# List all regular assistants
try:
    print("Listing all regular assistants...")
    response = requests.get("https://api.elevenlabs.io/v1/convai/agents", headers=headers)
    response.raise_for_status()
    
    # Print the raw JSON response
    print("\nRaw JSON response:")
    print(json.dumps(response.json(), indent=2))
    
    agents_data = response.json()
    agents = agents_data.get("agents", [])
    
    if not agents:
        print("No regular assistants found.")
    else:
        print(f"\nFound {len(agents)} regular assistants:\n")
        
        # Print details for each assistant
        for i, agent in enumerate(agents, 1):
            print(f"Assistant {i}:")
            for key, value in agent.items():
                print(f"  {key}: {value}")
            print()
            
        print("\nTo use a regular assistant, update your .env file with:")
        print("ELEVENLABS_ASSISTANT_ID=the-assistant-id-you-want-to-use")
except Exception as e:
    print(f"❌ Failed to list regular assistants: {e}")

print("\nListing complete") 