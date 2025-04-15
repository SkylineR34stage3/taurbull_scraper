# Finding Your Elevenlabs Assistant ID

This guide will help you locate your Elevenlabs Assistant ID, which is required for the TaurBull Scraper to associate documents with your assistant.

## Method 1: From the Elevenlabs Dashboard

1. Log in to your Elevenlabs account at [https://elevenlabs.io/](https://elevenlabs.io/)
2. Navigate to the "AI" section
3. Select "Assistants" from the menu
4. Find your assistant in the list and click on it
5. Look at the URL in your browser's address bar. The Assistant ID is the alphanumeric string at the end of the URL.
   
   Example: `https://elevenlabs.io/ai/assistants/01234567-89ab-cdef-0123-456789abcdef`
   
   In this example, the Assistant ID is: `01234567-89ab-cdef-0123-456789abcdef`

## Method 2: Using the API

If you prefer to use the API to find your Assistant ID:

1. Make sure you have your Elevenlabs API key
2. Run the following curl command (replace `YOUR_API_KEY` with your actual API key):

```bash
curl -X GET "https://api.elevenlabs.io/v1/assistants" \
     -H "Accept: application/json" \
     -H "xi-api-key: YOUR_API_KEY"
```

3. The response will be a JSON object containing a list of your assistants, including their IDs:

```json
{
  "assistants": [
    {
      "assistant_id": "01234567-89ab-cdef-0123-456789abcdef",
      "name": "Your Assistant Name",
      "description": "Your Assistant Description",
      // other assistant properties...
    },
    // other assistants...
  ]
}
```

4. Find your assistant by name in the list and copy the corresponding `assistant_id` value.

## Method 3: Using the Test Integration Script

The TaurBull Scraper includes a test integration script that can display your assistants:

1. Make sure you've set up your `.env` file with your Elevenlabs API key
2. Run the test integration script:

```bash
python test_integration.py --list-assistants
```

3. The script will display a list of your assistants with their IDs.

## Adding the Assistant ID to Your Configuration

Once you have your Assistant ID, add it to your `.env` file:

```
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_ASSISTANT_ID=your_assistant_id_here
```

Or provide it directly when running the scraper:

```bash
python main.py --assistant-id YOUR_ASSISTANT_ID
```

## Troubleshooting

If you can't find your Assistant ID:

1. Make sure you've created an assistant in your Elevenlabs account
2. Verify that your API key has the necessary permissions
3. Check that your Elevenlabs account plan includes API access to assistants
4. Contact Elevenlabs support if you continue to have issues

## Verifying the Integration

After running the scraper with your Assistant ID configured, you can verify the integration:

1. Log in to Elevenlabs and navigate to your assistant.
2. Check the "Knowledge Base" section of your assistant.
3. You should see your website content (e.g., FAQs) listed as knowledge base documents.

## Notes About Elevenlabs Knowledge Base

- Each Elevenlabs assistant can have multiple knowledge base documents.
- The same knowledge base document can be associated with multiple assistants.
- There are limits to how many knowledge base documents you can have based on your subscription plan.
- Non-enterprise accounts typically have a limit of 5 knowledge base items, with a maximum of 20MB or 300k characters.

For more information about Elevenlabs knowledge base features, refer to the [official Elevenlabs documentation](https://elevenlabs.io/docs/). 