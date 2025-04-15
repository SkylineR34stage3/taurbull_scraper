"""
Simple script to test Elevenlabs API key permissions.
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.environ.get("ELEVENLABS_API_KEY")
if not api_key:
    print("❌ ERROR: No API key found in .env file")
    exit(1)

# Display the API key partially masked for security
masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
print(f"Testing API key: {masked_key}")

# Headers for API requests
headers = {
    "Accept": "application/json",
    "xi-api-key": api_key
}

# Try to get user information
try:
    print("\n1. Testing user information endpoint...")
    response = requests.get("https://api.elevenlabs.io/v1/user", headers=headers)
    response.raise_for_status()
    user_data = response.json()
    print(f"✅ Success! Connected to account with subscription tier: {user_data.get('subscription', {}).get('tier', 'Unknown')}")
except Exception as e:
    print(f"❌ Failed to access user information: {e}")

# Try to list voices (a basic permission that most API keys should have)
try:
    print("\n2. Testing voices endpoint (basic permission)...")
    response = requests.get("https://api.elevenlabs.io/v1/voices", headers=headers)
    response.raise_for_status()
    voices_data = response.json()
    print(f"✅ Success! Found {len(voices_data.get('voices', []))} voices")
except Exception as e:
    print(f"❌ Failed to access voices: {e}")

# Try to access knowledge base
try:
    print("\n3. Testing knowledge base endpoint...")
    response = requests.get("https://api.elevenlabs.io/v1/convai/knowledge-base", headers=headers)
    response.raise_for_status()
    kb_data = response.json()
    print(f"✅ Success! Found {len(kb_data.get('documents', []))} knowledge base documents")
except Exception as e:
    print(f"❌ Failed to access knowledge base: {e}")

# Try to access regular assistants
try:
    print("\n4. Testing regular assistants endpoint...")
    response = requests.get("https://api.elevenlabs.io/v1/convai/agents", headers=headers)
    response.raise_for_status()
    agents_data = response.json()
    print(f"✅ Success! Found {len(agents_data.get('agents', []))} regular assistants")
except Exception as e:
    print(f"❌ Failed to access regular assistants: {e}")

# Try to access phone assistants
try:
    print("\n5. Testing phone assistants endpoint...")
    response = requests.get("https://api.elevenlabs.io/v1/phone-assistants", headers=headers)
    response.raise_for_status()
    phone_data = response.json()
    print(f"✅ Success! Found {len(phone_data.get('phone_assistants', []))} phone assistants")
except Exception as e:
    print(f"❌ Failed to access phone assistants: {e}")

# Try to access the specific phone assistant
assistant_id = os.environ.get("ELEVENLABS_ASSISTANT_ID")
if assistant_id:
    try:
        print(f"\n6. Testing specific phone assistant: {assistant_id}...")
        response = requests.get(f"https://api.elevenlabs.io/v1/phone-assistants/{assistant_id}", headers=headers)
        response.raise_for_status()
        assistant_data = response.json()
        print(f"✅ Success! Found phone assistant with name: {assistant_data.get('name', 'Unknown')}")
    except Exception as e:
        print(f"❌ Failed to access specific phone assistant: {e}")
else:
    print("\n6. Testing specific phone assistant: No assistant ID configured")

print("\nAPI Key Test Complete") 