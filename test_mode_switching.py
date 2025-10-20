#!/usr/bin/env python3
"""
Test script for the new WhatsApp mode switching functionality
"""

from dotenv import load_dotenv
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_mode_switching():
    """Test the mode switching functionality"""
    print("🔄 Testing WhatsApp Mode Switching Implementation...")
    print("=" * 50)
    
    # Test environment variables
    print("📋 Environment Configuration:")
    print(f"  ENABLE_PERSONAL_BUDGET: {os.getenv('ENABLE_PERSONAL_BUDGET', 'false')}")
    print(f"  ENABLE_BUSINESS: {os.getenv('ENABLE_BUSINESS', 'false')}")
    print(f"  DEFAULT_MODE: {os.getenv('DEFAULT_MODE', 'not set')}")
    print(f"  ALLOW_MODE_SWITCHING: {os.getenv('ALLOW_MODE_SWITCHING', 'false')}")
    print()
    
    # Test imports and functions
    try:
        from whatsapp_business_api import (
            get_user_mode, set_user_mode, handle_mode_command, 
            handle_set_mode_command, suggest_mode_switch,
            ENABLE_PERSONAL_BUDGET, ENABLE_BUSINESS, DEFAULT_MODE
        )
        print("✅ Successfully imported mode switching functions")
        print(f"📊 Configuration loaded:")
        print(f"  Personal Budget Enabled: {ENABLE_PERSONAL_BUDGET}")
        print(f"  Business Mode Enabled: {ENABLE_BUSINESS}")
        print(f"  Default Mode: {DEFAULT_MODE}")
        print()
        
        # Test default mode for a test user
        test_user_id = "test_user_60123456789"
        default_mode = get_user_mode(test_user_id)
        print(f"🧪 Test User Mode: {default_mode}")
        
        # Test mode command responses
        print("\n🎯 Testing Command Responses:")
        print("=" * 30)
        
        # Test /mode command
        mode_response = handle_mode_command(test_user_id)
        print("📱 /mode command response:")
        print(mode_response)
        print("\n" + "-" * 50 + "\n")
        
        # Test mode switching
        if ENABLE_BUSINESS:
            switch_response = handle_set_mode_command(test_user_id, "business")
            print("📱 /setbusiness command response:")
            print(switch_response)
            print("\n" + "-" * 50 + "\n")
        
        # Test mode suggestions
        print("💡 Testing Smart Suggestions:")
        print("=" * 30)
        
        # Test business-like transaction in personal mode
        business_transaction = {
            'action': 'sale',
            'amount': 1500,
            'description': 'jual produk kepada customer',
            'customer': 'Customer A'
        }
        suggestion = suggest_mode_switch(test_user_id, business_transaction)
        if suggestion:
            print("🔍 Business transaction suggestion:")
            print(suggestion.strip())
        else:
            print("ℹ️  No suggestion for business transaction")
        
        print("\n✅ All tests completed successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_mode_switching()
    sys.exit(0 if success else 1)