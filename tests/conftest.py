"""Test configuration and fixtures for the test suite."""

import pytest
import os
from unittest.mock import Mock, MagicMock
from pymongo import MongoClient
import tempfile
import shutil
from dotenv import load_dotenv

# Load test environment variables
load_dotenv('.env.test')

@pytest.fixture(scope='session')
def test_env():
    """Set up test environment variables."""
    return {
        'MONGO_URI': os.getenv('MONGO_URI', 'mongodb://localhost:27017/test_db'),
        'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', 'test_token'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', 'test_openai_key'),
        'WHATSAPP_VERIFY_TOKEN': os.getenv('WHATSAPP_VERIFY_TOKEN', 'test_verify_token'),
        'WHATSAPP_ACCESS_TOKEN': os.getenv('WHATSAPP_ACCESS_TOKEN', 'test_access_token'),
        'WHATSAPP_PHONE_NUMBER_ID': os.getenv('WHATSAPP_PHONE_NUMBER_ID', 'test_phone_id'),
    }

@pytest.fixture
def mock_mongo_client():
    """Mock MongoDB client for testing."""
    client = Mock(spec=MongoClient)
    database = Mock()
    collection = Mock()
    
    # Setup mock chain
    client.__getitem__.return_value = database
    database.__getitem__.return_value = collection
    client.list_database_names.return_value = ['test_db']
    database.list_collection_names.return_value = ['entries', 'users']
    
    # Mock collection methods
    collection.find_one.return_value = None
    collection.find.return_value = []
    collection.insert_one.return_value = Mock(inserted_id='test_id')
    collection.count_documents.return_value = 0
    collection.update_one.return_value = Mock(modified_count=1)
    collection.delete_many.return_value = Mock(deleted_count=0)
    
    # Mock admin command for ping
    client.admin.command.return_value = {'ok': 1}
    
    return client, database, collection

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = Mock()
    
    # Mock response structure
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
    
    client.chat.completions.create.return_value = mock_response
    return client

@pytest.fixture
def mock_telegram_update():
    """Mock Telegram update object."""
    update = Mock()
    update.effective_user = Mock()
    update.effective_user.id = 12345
    update.effective_user.first_name = "Test User"
    update.effective_chat = Mock()
    update.effective_chat.id = 12345
    update.message = Mock()
    update.message.text = "/start"
    update.message.photo = []
    update.message.document = None
    return update

@pytest.fixture
def mock_telegram_context():
    """Mock Telegram context object."""
    context = Mock()
    context.bot = Mock()
    context.bot.send_message = Mock()
    context.bot.send_photo = Mock()
    context.job_queue = Mock()
    return context

@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing."""
    return {
        'wa_id': 'test_user_123',
        'amount': 25.50,
        'category': 'Food',
        'description': 'Restaurant meal',
        'type': 'expense',
        'timestamp': '2025-09-17T10:30:00Z',
        'has_image': False,
        'confidence': 0.95
    }

@pytest.fixture
def sample_image_data():
    """Sample image data for testing."""
    # Create a simple test image (1x1 pixel PNG)
    return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'

@pytest.fixture(autouse=True)
def clean_environment():
    """Clean up environment after each test."""
    yield
    # Clean up any test artifacts if needed
    pass