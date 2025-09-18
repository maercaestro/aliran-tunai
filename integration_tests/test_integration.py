"""Integration tests for the complete application workflow."""

import pytest
import requests
import time
import json
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestAPIEndpoints:
    """Test cases for API endpoint integration."""

    @pytest.fixture(scope='class')
    def api_base_url(self):
        """Base URL for API testing."""
        return "http://localhost:5000"

    def test_health_endpoint(self, api_base_url):
        """Test the health check endpoint."""
        try:
            response = requests.get(f"{api_base_url}/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")

    def test_whatsapp_webhook_verification(self, api_base_url):
        """Test WhatsApp webhook verification endpoint."""
        try:
            params = {
                'hub.mode': 'subscribe',
                'hub.verify_token': 'test_verify_token',
                'hub.challenge': 'test_challenge'
            }
            response = requests.get(f"{api_base_url}/whatsapp/webhook", params=params, timeout=5)
            
            # Should return the challenge if verification succeeds, or 403 if it fails
            assert response.status_code in [200, 403]
            
            if response.status_code == 200:
                assert response.text == 'test_challenge'
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")

    def test_whatsapp_webhook_post_endpoint(self, api_base_url):
        """Test WhatsApp webhook POST endpoint."""
        try:
            # Sample WhatsApp webhook payload
            payload = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "test_entry_id",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "1234567890",
                                "phone_number_id": "test_phone_id"
                            },
                            "messages": [{
                                "from": "test_user_id",
                                "id": "test_message_id",
                                "timestamp": "1234567890",
                                "text": {
                                    "body": "Hello test message"
                                },
                                "type": "text"
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            response = requests.post(
                f"{api_base_url}/whatsapp/webhook",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            # Should return 200 for successful webhook processing
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")


class TestDatabaseIntegration:
    """Test cases for database integration."""

    @pytest.fixture(autouse=True)
    def setup_test_database(self):
        """Set up test database for integration tests."""
        # Import here to avoid import errors if modules aren't available
        try:
            import whatsapp_business_api
            # Clean up test data before and after tests
            if whatsapp_business_api.connect_to_mongodb():
                if whatsapp_business_api.collection is not None:
                    whatsapp_business_api.collection.delete_many({"wa_id": "integration_test_user"})
            yield
            # Cleanup after test
            if whatsapp_business_api.connect_to_mongodb():
                if whatsapp_business_api.collection is not None:
                    whatsapp_business_api.collection.delete_many({"wa_id": "integration_test_user"})
        except ImportError:
            pytest.skip("WhatsApp API module not available")

    def test_complete_transaction_flow(self):
        """Test complete transaction processing flow."""
        try:
            import whatsapp_business_api
            
            # Test data
            test_user = "integration_test_user"
            test_message = "Spent $25.50 on lunch at McDonald's"
            
            # Process the transaction
            result = whatsapp_business_api.handle_message(test_user, test_message)
            
            # Verify the response indicates success
            assert "recorded" in result.lower() or "processed" in result.lower()
            
            # Verify the transaction was saved to database
            if whatsapp_business_api.connect_to_mongodb() and whatsapp_business_api.collection is not None:
                saved_transaction = whatsapp_business_api.collection.find_one({"wa_id": test_user})
                assert saved_transaction is not None
                assert saved_transaction['wa_id'] == test_user
                assert saved_transaction['amount'] > 0
                
        except ImportError:
            pytest.skip("Required modules not available")

    def test_summary_generation_integration(self):
        """Test summary generation with real database data."""
        try:
            import whatsapp_business_api
            
            test_user = "integration_test_user"
            
            # First, add some test transactions
            test_transactions = [
                {
                    "wa_id": test_user,
                    "amount": 25.50,
                    "category": "Food",
                    "description": "Lunch",
                    "type": "expense",
                    "timestamp": "2025-09-17T12:00:00Z"
                },
                {
                    "wa_id": test_user,
                    "amount": 15.00,
                    "category": "Transport",
                    "description": "Bus fare",
                    "type": "expense",
                    "timestamp": "2025-09-17T10:00:00Z"
                }
            ]
            
            if whatsapp_business_api.connect_to_mongodb() and whatsapp_business_api.collection is not None:
                whatsapp_business_api.collection.insert_many(test_transactions)
                
                # Generate summary
                summary = whatsapp_business_api.handle_message(test_user, "/summary")
                
                # Verify summary contains expected information
                assert "Summary" in summary
                assert "25.5" in summary or "$25" in summary
                assert "15" in summary or "$15" in summary
                
        except ImportError:
            pytest.skip("Required modules not available")

    def test_database_connection_resilience(self):
        """Test database connection resilience."""
        try:
            import whatsapp_business_api
            
            # Test multiple connection attempts
            for i in range(3):
                result = whatsapp_business_api.connect_to_mongodb()
                # Should be consistent
                assert isinstance(result, bool)
                time.sleep(0.1)  # Brief pause between attempts
                
        except ImportError:
            pytest.skip("Required modules not available")


class TestExternalServiceIntegration:
    """Test cases for external service integration."""

    @patch('whatsapp_business_api.openai_client')
    def test_openai_integration_with_fallback(self, mock_openai):
        """Test OpenAI integration with fallback handling."""
        try:
            import whatsapp_business_api
            
            # Test successful AI parsing
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
            
            result = whatsapp_business_api.parse_transaction_with_ai("Spent $25.50 on dinner")
            
            assert result is not None
            assert result['amount'] == 25.50
            assert result['category'] == 'Food'
            
            # Test API failure scenario
            mock_openai.chat.completions.create.side_effect = Exception("API Error")
            
            result = whatsapp_business_api.parse_transaction_with_ai("Test transaction")
            assert result is None  # Should handle gracefully
            
        except ImportError:
            pytest.skip("Required modules not available")

    def test_whatsapp_api_media_download(self):
        """Test WhatsApp media download integration."""
        try:
            import whatsapp_business_api
            
            # Mock a successful media download
            with patch('whatsapp_business_api.requests') as mock_requests:
                mock_response = Mock()
                mock_response.content = b'fake_image_data'
                mock_response.status_code = 200
                mock_requests.get.return_value = mock_response
                
                result = whatsapp_business_api.download_whatsapp_media("test_media_id")
                assert result == b'fake_image_data'
                
                # Test download failure
                mock_response.status_code = 404
                result = whatsapp_business_api.download_whatsapp_media("invalid_media_id")
                assert result is None
                
        except ImportError:
            pytest.skip("Required modules not available")


class TestEndToEndWorkflow:
    """Test cases for complete end-to-end workflows."""

    def test_complete_whatsapp_message_processing(self):
        """Test complete WhatsApp message processing workflow."""
        try:
            import whatsapp_business_api
            
            # Simulate a complete WhatsApp webhook payload processing
            test_user = "e2e_test_user"
            
            # Clean up any existing test data
            if whatsapp_business_api.connect_to_mongodb() and whatsapp_business_api.collection is not None:
                whatsapp_business_api.collection.delete_many({"wa_id": test_user})
            
            # Process different types of messages
            test_scenarios = [
                ("Spent $15 on coffee", "expense"),
                ("Earned $100 from freelance work", "income"),
                ("/summary", "command"),
                ("/help", "command")
            ]
            
            for message, expected_type in test_scenarios:
                # Use handle_message for all message types
                result = whatsapp_business_api.handle_message(test_user, message)
                
                # Verify we get a response
                assert isinstance(result, str)
                assert len(result) > 0
            
            # Cleanup
            if whatsapp_business_api.connect_to_mongodb() and whatsapp_business_api.collection is not None:
                whatsapp_business_api.collection.delete_many({"wa_id": test_user})
                
        except ImportError:
            pytest.skip("Required modules not available")

    def test_error_recovery_workflow(self):
        """Test error recovery in various failure scenarios."""
        try:
            import whatsapp_business_api
            
            test_user = "error_test_user"
            
            # Test database connection failure handling
            with patch('whatsapp_business_api.connect_to_mongodb') as mock_connect:
                mock_connect.return_value = False
                
                result = whatsapp_business_api.handle_message(test_user, "Test message")
                assert "database" in result.lower() or "error" in result.lower()
            
            # Test AI service failure handling
            with patch('whatsapp_business_api.parse_transaction_with_ai') as mock_ai:
                mock_ai.return_value = None
                
                result = whatsapp_business_api.handle_message(test_user, "Test message")
                assert isinstance(result, str)  # Should still return a response
                
        except ImportError:
            pytest.skip("Required modules not available")


class TestPerformanceIntegration:
    """Test cases for performance and load testing."""

    def test_concurrent_message_processing(self):
        """Test concurrent message processing."""
        try:
            import whatsapp_business_api
            import threading
            import time
            
            results = []
            errors = []
            
            def process_message(user_id, message):
                try:
                    result = whatsapp_business_api.handle_message(f"perf_test_{user_id}", f"Test transaction {message}")
                    results.append(result)
                except Exception as e:
                    errors.append(str(e))
            
            # Create multiple threads to simulate concurrent requests
            threads = []
            for i in range(5):
                thread = threading.Thread(target=process_message, args=(i, f"message_{i}"))
                threads.append(thread)
            
            # Start all threads
            start_time = time.time()
            for thread in threads:
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            end_time = time.time()
            
            # Verify all messages were processed
            assert len(results) == 5
            assert len(errors) == 0
            
            # Verify reasonable performance (should complete within 30 seconds)
            assert (end_time - start_time) < 30
            
            # Cleanup
            if whatsapp_business_api.connect_to_mongodb() and whatsapp_business_api.collection is not None:
                for i in range(5):
                    whatsapp_business_api.collection.delete_many({"wa_id": f"perf_test_{i}"})
                    
        except ImportError:
            pytest.skip("Required modules not available")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])