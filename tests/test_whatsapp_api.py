"""Unit tests for whatsapp_business_api.py functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the modules to test
import whatsapp_business_api


class TestWhatsAppAPI:
    """Test cases for WhatsApp Business API functionality."""

    def test_whatsapp_webhook_verify_success(self):
        """Test successful WhatsApp webhook verification."""
        with patch.object(whatsapp_business_api, 'app') as mock_app:
            with patch('whatsapp_business_api.request') as mock_request:
                with patch('whatsapp_business_api.os') as mock_os:
                    # Arrange
                    mock_request.args.get.side_effect = lambda key: {
                        'hub.mode': 'subscribe',
                        'hub.verify_token': 'test_token',
                        'hub.challenge': 'test_challenge'
                    }.get(key)
                    mock_os.getenv.return_value = 'test_token'

                    # Act
                    result = whatsapp_business_api.whatsapp_webhook_verify()

                    # Assert
                    assert result == 'test_challenge'

    def test_whatsapp_webhook_verify_failure(self):
        """Test failed WhatsApp webhook verification."""
        with patch.object(whatsapp_business_api, 'app') as mock_app:
            with patch('whatsapp_business_api.request') as mock_request:
                with patch('whatsapp_business_api.os') as mock_os:
                    # Arrange
                    mock_request.args.get.side_effect = lambda key: {
                        'hub.mode': 'subscribe',
                        'hub.verify_token': 'wrong_token',
                        'hub.challenge': 'test_challenge'
                    }.get(key)
                    mock_os.getenv.return_value = 'correct_token'

                    # Act
                    result = whatsapp_business_api.whatsapp_webhook_verify()

                    # Assert
                    assert result == ('Verification failed', 403)

    @patch('whatsapp_business_api.connect_to_mongodb')
    @patch('whatsapp_business_api.collection')
    def test_handle_text_message_success(self, mock_collection, mock_connect):
        """Test handling text message successfully."""
        # Arrange
        mock_connect.return_value = True
        mock_collection.insert_one.return_value = Mock(inserted_id='test_id')
        
        with patch('whatsapp_business_api.parse_transaction_with_ai') as mock_parse:
            mock_parse.return_value = {
                'amount': 25.0,
                'category': 'Food',
                'description': 'lunch',
                'type': 'expense'
            }

            # Act
            result = whatsapp_business_api.handle_message("test_user", "Spent $25 on lunch")

            # Assert
            assert "recorded" in result.lower() or "saved" in result.lower()
            mock_collection.insert_one.assert_called_once()

    @patch('whatsapp_business_api.connect_to_mongodb')
    def test_handle_text_message_db_failure(self, mock_connect):
        """Test handling text message when DB connection fails."""
        # Arrange
        mock_connect.return_value = False

        # Act
        result = whatsapp_business_api.handle_message("test_user", "Test message")

        # Assert
        assert "database connection" in result.lower() or "connection" in result.lower()

    @patch('whatsapp_business_api.openai_client')
    def test_parse_transaction_with_ai_success(self, mock_openai):
        """Test AI transaction parsing success."""
        # Arrange
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "amount": 25.50,
            "category": "Food",
            "description": "Restaurant meal",
            "type": "expense",
            "confidence": 0.95
        })
        mock_openai.chat.completions.create.return_value = mock_response

        # Act
        result = whatsapp_business_api.parse_transaction_with_ai("Spent $25.50 on restaurant meal")

        # Assert
        assert result is not None
        assert result['amount'] == 25.50
        assert result['category'] == 'Food'
        assert result['type'] == 'expense'

    @patch('whatsapp_business_api.connect_to_mongodb')
    @patch('whatsapp_business_api.collection')
    def test_handle_summary_command_success(self, mock_collection, mock_connect):
        """Test summary command with transactions."""
        # Arrange
        mock_connect.return_value = True
        sample_transactions = [
            {
                'amount': 25.0,
                'category': 'Food',
                'description': 'Lunch',
                'type': 'expense',
                'timestamp': '2025-09-17T12:00:00Z'
            }
        ]
        mock_collection.find.return_value = sample_transactions

        # Act
        result = whatsapp_business_api.handle_summary_command("test_user")

        # Assert
        assert "Summary" in result
        assert "25.0" in result or "$25" in result

    @patch('whatsapp_business_api.connect_to_mongodb')
    @patch('whatsapp_business_api.collection')
    def test_handle_summary_command_no_transactions(self, mock_collection, mock_connect):
        """Test summary command with no transactions."""
        # Arrange
        mock_connect.return_value = True
        mock_collection.find.return_value = []

        # Act
        result = whatsapp_business_api.handle_summary_command("test_user")

        # Assert
        assert "don't have any transactions" in result

    @patch('whatsapp_business_api.connect_to_mongodb')
    @patch('whatsapp_business_api.collection')
    @patch('whatsapp_business_api.mongo_client')
    def test_handle_test_db_command_success(self, mock_client, mock_collection, mock_connect):
        """Test database test command success."""
        # Arrange
        mock_connect.return_value = True
        mock_collection.find_one.return_value = None
        mock_collection.count_documents.return_value = 5

        # Act
        result = whatsapp_business_api.handle_test_db_command("test_user")

        # Assert
        assert "Database Connection Test Successful" in result
        assert "5 transactions" in result

    @patch('whatsapp_business_api.connect_to_mongodb')
    def test_handle_test_db_command_failure(self, mock_connect):
        """Test database test command failure."""
        # Arrange
        mock_connect.return_value = False

        # Act
        result = whatsapp_business_api.handle_test_db_command("test_user")

        # Assert
        assert "Database Connection Test Failed" in result

    def test_download_whatsapp_media_success(self, sample_image_data):
        """Test successful media download."""
        with patch('whatsapp_business_api.requests') as mock_requests:
            # Arrange
            mock_response = Mock()
            mock_response.content = sample_image_data
            mock_response.status_code = 200
            mock_requests.get.return_value = mock_response

            # Act
            result = whatsapp_business_api.download_whatsapp_media("test_media_id")

            # Assert
            assert result == sample_image_data
            mock_requests.get.assert_called_once()

    def test_download_whatsapp_media_failure(self):
        """Test failed media download."""
        with patch('whatsapp_business_api.requests') as mock_requests:
            # Arrange
            mock_response = Mock()
            mock_response.status_code = 404
            mock_requests.get.return_value = mock_response

            # Act
            result = whatsapp_business_api.download_whatsapp_media("invalid_media_id")

            # Assert
            assert result is None

    @patch('whatsapp_business_api.connect_to_mongodb')
    @patch('whatsapp_business_api.collection')
    def test_save_to_mongodb_success(self, mock_collection, mock_connect):
        """Test successful data saving to MongoDB."""
        # Arrange
        mock_connect.return_value = True
        mock_collection.insert_one.return_value = Mock(inserted_id='test_id')
        
        test_data = {
            'wa_id': 'test_user',
            'amount': 25.0,
            'category': 'Food',
            'type': 'expense'
        }

        # Act
        result = whatsapp_business_api.save_to_mongodb(test_data, "test_user")

        # Assert
        assert result is True
        mock_collection.insert_one.assert_called_once()

    @patch('whatsapp_business_api.connect_to_mongodb')
    def test_save_to_mongodb_failure(self, mock_connect):
        """Test failed data saving to MongoDB."""
        # Arrange
        mock_connect.return_value = False

        # Act
        result = whatsapp_business_api.save_to_mongodb({}, "test_user")

        # Assert
        assert result is False


class TestImageProcessing:
    """Test cases for image processing functionality."""

    @patch('whatsapp_business_api.openai_client')
    def test_parse_receipt_with_ai_success(self, mock_openai, sample_image_data):
        """Test successful receipt parsing with AI."""
        # Arrange
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "amount": 45.99,
            "merchant": "Test Store",
            "category": "Shopping",
            "items": ["Item 1", "Item 2"],
            "type": "expense"
        })
        mock_openai.chat.completions.create.return_value = mock_response

        # Act
        result = whatsapp_business_api.parse_receipt_with_ai(sample_image_data)

        # Assert
        assert result is not None
        assert result['amount'] == 45.99
        assert result['merchant'] == 'Test Store'
        assert result['type'] == 'expense'

    @patch('whatsapp_business_api.openai_client')
    def test_parse_receipt_with_ai_failure(self, mock_openai, sample_image_data):
        """Test failed receipt parsing with AI."""
        # Arrange
        mock_openai.chat.completions.create.side_effect = Exception("API Error")

        # Act
        result = whatsapp_business_api.parse_receipt_with_ai(sample_image_data)

        # Assert
        assert result is None

    def test_handle_image_message_success(self, sample_image_data):
        """Test successful image message handling."""
        with patch('whatsapp_business_api.download_whatsapp_media') as mock_download:
            with patch('whatsapp_business_api.parse_receipt_with_ai') as mock_parse:
                with patch('whatsapp_business_api.save_to_mongodb') as mock_save:
                    # Arrange
                    mock_download.return_value = sample_image_data
                    mock_parse.return_value = {
                        'amount': 25.0,
                        'merchant': 'Test Store',
                        'category': 'Shopping',
                        'type': 'expense'
                    }
                    mock_save.return_value = True

                    # Act
                    result = whatsapp_business_api.handle_media_message("test_user", "test_media_id", "image")

                    # Assert
                    assert "processed" in result.lower() or "recorded" in result.lower()
                    mock_download.assert_called_once_with("test_media_id")

    def test_handle_image_message_download_failure(self):
        """Test image message handling when download fails."""
        with patch('whatsapp_business_api.download_whatsapp_media') as mock_download:
            # Arrange
            mock_download.return_value = None

            # Act
            result = whatsapp_business_api.handle_media_message("test_user", "invalid_media_id", "image")

            # Assert
            assert "download" in result.lower() or "error" in result.lower()


class TestCommandHandlers:
    """Test cases for command handlers."""

    def test_handle_help_command(self):
        """Test help command handler through handle_message."""
        # Act - test help command through message handler
        result = whatsapp_business_api.handle_message("test_user", "/help")

        # Assert
        assert "help" in result.lower() or "command" in result.lower()

    def test_handle_start_command(self):
        """Test start command handler."""
        # Act
        result = whatsapp_business_api.handle_start_command("test_user")

        # Assert
        assert "Welcome" in result
        assert "AliranTunai" in result

    @patch('whatsapp_business_api.connect_to_mongodb')
    @patch('whatsapp_business_api.collection')
    def test_handle_delete_command_success(self, mock_collection, mock_connect):
        """Test delete functionality through handle_message."""
        # Arrange
        mock_connect.return_value = True
        mock_collection.delete_many.return_value = Mock(deleted_count=5)

        # Act - test delete through message handler
        result = whatsapp_business_api.handle_message("test_user", "/delete")

        # Assert
        assert "delete" in result.lower() or "clear" in result.lower()

    @patch('whatsapp_business_api.connect_to_mongodb')
    @patch('whatsapp_business_api.collection')
    def test_handle_delete_command_no_transactions(self, mock_collection, mock_connect):
        """Test delete command with no transactions."""
        # Arrange
        mock_connect.return_value = True
        mock_collection.delete_many.return_value = Mock(deleted_count=0)

        # Act - test delete through message handler  
        result = whatsapp_business_api.handle_message("test_user", "/delete")

        # Assert
        assert "delete" in result.lower() or "clear" in result.lower()


class TestErrorHandling:
    """Test cases for error handling scenarios."""

    def test_webhook_with_invalid_json(self):
        """Test webhook handling with invalid JSON."""
        with patch.object(whatsapp_business_api, 'app') as mock_app:
            with patch('whatsapp_business_api.request') as mock_request:
                # Arrange
                mock_request.get_json.side_effect = Exception("Invalid JSON")

                # Act & Assert
                # This should not crash the application
                try:
                    whatsapp_business_api.whatsapp_webhook()
                except Exception as e:
                    pytest.fail(f"Webhook should handle invalid JSON gracefully: {e}")

    @patch('whatsapp_business_api.openai_client')
    def test_ai_api_rate_limiting(self, mock_openai):
        """Test handling of OpenAI API rate limiting."""
        # Arrange
        mock_openai.chat.completions.create.side_effect = Exception("Rate limit exceeded")

        # Act
        result = whatsapp_business_api.parse_transaction_with_ai("Test transaction")

        # Assert
        assert result is None

    @patch('whatsapp_business_api.mongo_client')
    def test_mongodb_connection_timeout(self, mock_client):
        """Test handling of MongoDB connection timeout."""
        # Arrange
        mock_client.admin.command.side_effect = Exception("Connection timeout")

        # Act
        result = whatsapp_business_api.connect_to_mongodb()

        # Assert
        assert result is False


if __name__ == '__main__':
    pytest.main([__file__])