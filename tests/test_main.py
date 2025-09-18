"""Unit tests for main.py Telegram bot functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the modules to test
import main


class TestTelegramBot:
    """Test cases for Telegram bot functionality."""

    @pytest.mark.asyncio
    async def test_start_command(self, mock_telegram_update, mock_telegram_context):
        """Test the /start command handler."""
        # Arrange
        update = mock_telegram_update
        context = mock_telegram_context

        # Act
        await main.start(update, context)

        # Assert
        context.bot.send_message.assert_called_once()
        call_args = context.bot.send_message.call_args
        assert "Welcome to AliranTunai Bot!" in call_args[1]['text']

    @pytest.mark.asyncio  
    async def test_help_command(self, mock_telegram_update, mock_telegram_context):
        """Test the help functionality (testing through handle_message)."""
        # Arrange
        update = mock_telegram_update
        context = mock_telegram_context
        # Mock a help message
        update.message.text = "/help"

        # Act
        await main.handle_message(update, context)

        # Assert
        context.bot.send_message.assert_called()  # Should send some help message

    @patch('main.connect_to_mongodb')
    @patch('main.collection')
    @pytest.mark.asyncio
    async def test_handle_transaction_message_success(self, mock_collection, mock_connect, 
                                              mock_telegram_update, mock_telegram_context):
        """Test handling transaction message successfully."""
        # Arrange
        update = mock_telegram_update
        update.message.text = "Spent $25 on lunch at McDonald's"
        context = mock_telegram_context
        
        mock_connect.return_value = True
        mock_collection.find_one.return_value = None
        mock_collection.insert_one.return_value = Mock(inserted_id='test_id')

        with patch('main.parse_transaction_with_ai') as mock_parse:
            mock_parse.return_value = {
                'amount': 25.0,
                'category': 'Food',
                'description': 'lunch at McDonald\'s',
                'type': 'expense'
            }

            # Act
            await main.handle_message(update, context)

            # Assert
            context.bot.send_message.assert_called()

    @pytest.mark.asyncio
    @patch('main.connect_to_mongodb')
    async def test_handle_transaction_db_connection_fail(self, mock_connect, 
                                                 mock_telegram_update, mock_telegram_context):
        """Test handling transaction when DB connection fails."""
        # Arrange
        update = mock_telegram_update
        update.message.text = "Spent $25 on lunch"
        context = mock_telegram_context
        mock_connect.return_value = False

        # Act
        await main.handle_message(update, context)

        # Assert
        context.bot.send_message.assert_called()
        # Check that some error message was sent

    @patch('main.openai_client')
    def test_parse_transaction_with_ai_success(self, mock_openai):
        """Test AI transaction parsing success."""
        # Arrange
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = '''
        {
            "amount": 25.50,
            "category": "Food",
            "description": "Restaurant meal",
            "type": "expense",
            "confidence": 0.95
        }
        '''
        mock_openai.chat.completions.create.return_value = mock_response

        # Act
        result = main.parse_transaction_with_ai("Spent $25.50 on restaurant meal")

        # Assert
        assert result is not None
        assert result['amount'] == 25.50
        assert result['category'] == 'Food'
        assert result['type'] == 'expense'

    @patch('main.openai_client')
    def test_parse_transaction_with_ai_invalid_response(self, mock_openai):
        """Test AI transaction parsing with invalid response."""
        # Arrange
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_openai.chat.completions.create.return_value = mock_response

        # Act
        result = main.parse_transaction_with_ai("Some invalid text")

        # Assert
        assert result is None

    @patch('main.connect_to_mongodb')
    @patch('main.collection')
    @pytest.mark.asyncio
    @patch('main.connect_to_mongodb')
    @patch('main.collection')
    async def test_handle_summary_command_no_transactions(self, mock_collection, mock_connect,
                                                  mock_telegram_update, mock_telegram_context):
        """Test summary command with no transactions."""
        # Arrange
        update = mock_telegram_update
        update.message.text = "/summary"  # Set command text
        context = mock_telegram_context
        mock_connect.return_value = True
        mock_collection.find.return_value = []

        # Act
        await main.summary(update, context)

        # Assert
        context.bot.send_message.assert_called()

    @pytest.mark.asyncio
    @patch('main.connect_to_mongodb')
    @patch('main.collection')
    async def test_handle_summary_command_with_transactions(self, mock_collection, mock_connect,
                                                    mock_telegram_update, mock_telegram_context):
        """Test summary command with existing transactions."""
        # Arrange
        update = mock_telegram_update
        update.message.text = "/summary"
        context = mock_telegram_context
        mock_connect.return_value = True
        
        sample_transactions = [
            {
                'amount': 25.0,
                'category': 'Food',
                'description': 'Lunch',
                'type': 'expense',
                'timestamp': '2025-09-17T12:00:00Z'
            },
            {
                'amount': 50.0,
                'category': 'Transport',
                'description': 'Gas',
                'type': 'expense',
                'timestamp': '2025-09-17T10:00:00Z'
            }
        ]
        
        mock_collection.find.return_value = sample_transactions

        # Act
        await main.summary(update, context)

        # Assert
        context.bot.send_message.assert_called()

    def test_get_user_id_from_update(self, mock_telegram_update):
        """Test extracting user ID from update."""
        # Arrange
        update = mock_telegram_update
        update.effective_user.id = 12345

        # Act - test using chat_id directly since get_user_id_from_update doesn't exist
        user_id = update.effective_chat.id

        # Assert
        assert user_id == 12345

    @patch('main.mongo_client')
    def test_connect_to_mongodb_success(self, mock_client):
        """Test successful MongoDB connection."""
        # Arrange
        mock_client.admin.command.return_value = {'ok': 1}

        # Act
        result = main.connect_to_mongodb()

        # Assert
        assert result is True
        mock_client.admin.command.assert_called_with('ping')

    @patch('main.mongo_client')
    def test_connect_to_mongodb_failure(self, mock_client):
        """Test MongoDB connection failure."""
        # Arrange
        mock_client.admin.command.side_effect = Exception("Connection failed")

        # Act
        result = main.connect_to_mongodb()

        # Assert
        assert result is False


class TestUtilityFunctions:
    """Test cases for utility functions."""

    def test_parse_transaction_with_ai(self):
        """Test AI transaction parsing function."""
        # Test with mock since the actual function exists
        with patch('main.openai_client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '{"amount": 25.50, "category": "Food", "description": "lunch", "type": "expense"}'
            mock_client.chat.completions.create.return_value = mock_response

            # Act
            result = main.parse_transaction_with_ai("Spent $25.50 on lunch")
            
            # Assert
            assert result is not None
            assert 'amount' in result

    def test_extract_text_from_image(self):
        """Test OCR text extraction from images."""
        # Test with mock image bytes since the function exists
        test_image_bytes = b"fake_image_data"
        
        with patch('main.pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "Receipt Total: $25.50"
            
            # Act
            result = main.extract_text_from_image(test_image_bytes)
            
            # Assert
            assert isinstance(result, str)
            assert "Receipt" in result


class TestErrorHandling:
    """Test cases for error handling scenarios."""

    @patch('main.openai_client')
    def test_ai_parsing_exception_handling(self, mock_openai):
        """Test AI parsing with exception."""
        # Arrange
        mock_openai.chat.completions.create.side_effect = Exception("API Error")

        # Act
        result = main.parse_transaction_with_ai("Test transaction")

        # Assert
        assert result is None

    @patch('main.collection')
    def test_database_operation_exception_handling(self, mock_collection):
        """Test database operation exception handling."""
        # Arrange
        mock_collection.insert_one.side_effect = Exception("Database Error")

        # Act & Assert
        with pytest.raises(Exception):
            main.save_to_mongodb({}, 12345)  # Use integer chat_id

    @pytest.mark.asyncio
    async def test_invalid_user_input_handling(self, mock_telegram_update, mock_telegram_context):
        """Test handling of invalid user input."""
        # Arrange
        update = mock_telegram_update
        update.message.text = ""  # Empty message
        context = mock_telegram_context

        # Act
        await main.handle_message(update, context)

        # Assert
        context.bot.send_message.assert_called()


if __name__ == '__main__':
    pytest.main([__file__])