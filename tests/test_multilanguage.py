#!/usr/bin/env python3
"""
Simple test script to verify the multi-language functionality.
This tests the language detection and localized message functions.
"""

import sys
import os

# Add the current directory to the path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '/Users/abuhuzaifahbidin/Documents/GitHub/aliran-tunai'
sys.path.insert(0, current_dir)

# Import the functions we want to test
from whatsapp_business_api import detect_language, get_localized_message, is_transaction_query

def test_language_detection():
    """Test the language detection function."""
    print("🧪 Testing Language Detection...")
    
    test_cases = [
        # Malay examples
        ("saya beli nasi lemak rm 5", "ms"),
        ("jual ayam 2 ekor kepada Ahmad", "ms"),
        ("bayar supplier rm 100", "ms"),
        ("terima bayaran daripada customer", "ms"),
        ("apa itu aliran tunai?", "ms"),
        ("bagaimana untuk guna aplikasi ini?", "ms"),
        ("saya mahu tahu tentang status", "ms"),
        
        # English examples  
        ("I bought rice for $10", "en"),
        ("sold 5 chickens to restaurant", "en"),
        ("paid the vendor $200", "en"),
        ("received payment from customer", "en"),
        ("what is cash flow?", "en"),
        ("how to use this app?", "en"),
        ("I want to know about status", "en"),
        
        # Mixed/unclear cases (should default to English)
        ("hello", "en"),
        ("ok", "en"),
        ("", "en"),
    ]
    
    for text, expected in test_cases:
        result = detect_language(text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{text}' -> {result} (expected: {expected})")
    
    print()

def test_localized_messages():
    """Test the localized message system."""
    print("🗣️ Testing Localized Messages...")
    
    # Test welcome message
    welcome_en = get_localized_message('welcome', 'en')
    welcome_ms = get_localized_message('welcome', 'ms')
    
    print("English welcome message:")
    print(welcome_en[:100] + "..." if len(welcome_en) > 100 else welcome_en)
    print()
    
    print("Malay welcome message:")
    print(welcome_ms[:100] + "..." if len(welcome_ms) > 100 else welcome_ms)
    print()
    
    # Test error messages
    error_en = get_localized_message('error_parse', 'en')
    error_ms = get_localized_message('error_parse', 'ms')
    
    print(f"English error: {error_en}")
    print(f"Malay error: {error_ms}")
    print()

def test_transaction_detection():
    """Test transaction vs query detection."""
    print("💳 Testing Transaction Detection...")
    
    test_cases = [
        # Should be detected as transactions
        ("beli nasi lemak rm 5", True),
        ("sold chicken to Ahmad", True),
        ("bayar supplier rm 100", True),  
        ("I bought rice for $10", True),
        ("jual ayam 2 ekor", True),
        
        # Should be detected as general queries
        ("what is cash flow?", False),
        ("apa itu aliran tunai?", False),
        ("how to use this app?", False),
        ("bagaimana untuk guna?", False),
        ("can you help me?", False),
        ("boleh bantu saya?", False),
    ]
    
    for text, expected in test_cases:
        result = is_transaction_query(text)
        status = "✅" if result == expected else "❌"
        query_type = "Transaction" if result else "Query"
        expected_type = "Transaction" if expected else "Query"
        print(f"{status} '{text}' -> {query_type} (expected: {expected_type})")
    
    print()

if __name__ == "__main__":
    print("🌍 Multi-Language WhatsApp Bot Test\n")
    
    test_language_detection()
    test_localized_messages()  
    test_transaction_detection()
    
    print("🎉 Test completed!")