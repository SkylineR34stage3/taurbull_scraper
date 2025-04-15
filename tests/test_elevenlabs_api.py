"""
Test the Elevenlabs API integration to ensure method signatures are correct.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.elevenlabs_api import ElevenlabsAPI

class TestElevenlabsAPI:
    """Test the ElevenlabsAPI class."""
    
    def setup_method(self):
        """Set up the test environment."""
        self.api = ElevenlabsAPI(
            api_key="dummy_key",
            assistant_id="dummy_assistant_id"
        )
    
    @patch('src.elevenlabs_api.requests.request')
    def test_add_text_to_knowledge_base_signature(self, mock_request):
        """Test the add_text_to_knowledge_base method signature."""
        # Setup the mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "test_document_id"}
        mock_request.return_value = mock_response
        
        # Mock the knowledge base ID retrieval
        with patch.object(self.api, 'get_knowledge_base_id', return_value="test_kb_id"):
            # Call the method with the expected parameters
            result = self.api.add_text_to_knowledge_base(
                text="Test content",
                name="Test Document"
            )
            
            # Verify the result
            assert "id" in result
            assert result["id"] == "test_document_id"
            
            # Verify the request was made with the right parameters
            mock_request.assert_called_once()
            _, kwargs = mock_request.call_args
            assert kwargs['json']['text'] == "Test content"
            assert kwargs['json']['name'] == "Test Document"
    
    @patch('src.elevenlabs_api.requests.request')
    def test_delete_knowledge_base_document_signature(self, mock_request):
        """Test the delete_knowledge_base_document method signature."""
        # Setup the mock
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_request.return_value = mock_response
        
        # Mock the knowledge base ID retrieval
        with patch.object(self.api, 'get_knowledge_base_id', return_value="test_kb_id"):
            # Call the method with the expected parameter
            result = self.api.delete_knowledge_base_document("test_document_id")
            
            # Verify the result
            assert result is True
            
            # Verify the request was made with the right URL
            mock_request.assert_called_once()
            args, _ = mock_request.call_args
            assert args[0] == "DELETE"
            assert "test_kb_id" in args[1]
            assert "test_document_id" in args[1]

if __name__ == "__main__":
    pytest.main() 