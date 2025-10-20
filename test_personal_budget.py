#!/usr/bin/env python3
"""
Personal Budget Flow Test
Tests the end-to-end personal budget functionality
"""

import requests
import json
from datetime import datetime

# Test configuration
API_BASE = "http://localhost:5001"
TEST_WA_ID = "601234567890"  # Test WhatsApp ID

def test_personal_budget_flow():
    """Test the complete personal budget flow"""
    
    print("🧪 Testing Personal Budget Flow")
    print("=" * 50)
    
    # Test 1: Personal Dashboard (should work even with no data)
    print("\n1️⃣ Testing Personal Dashboard API...")
    try:
        response = requests.get(f"{API_BASE}/api/personal/dashboard/{TEST_WA_ID}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Dashboard API working: {data['summary']}")
        else:
            print(f"❌ Dashboard API failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Dashboard API error: {e}")
    
    # Test 2: Personal Expenses API
    print("\n2️⃣ Testing Personal Expenses API...")
    try:
        response = requests.get(f"{API_BASE}/api/personal/expenses/{TEST_WA_ID}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Expenses API working: {len(data['transactions'])} transactions found")
        else:
            print(f"❌ Expenses API failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Expenses API error: {e}")
    
    # Test 3: Budget Management API (POST)
    print("\n3️⃣ Testing Budget Management API...")
    try:
        budget_data = {
            "budgets": {
                "FOOD_DINING": 500.0,
                "TRANSPORTATION": 200.0,
                "SHOPPING": 300.0,
                "BILLS_UTILITIES": 400.0
            }
        }
        response = requests.post(
            f"{API_BASE}/api/personal/budget/{TEST_WA_ID}",
            json=budget_data,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print(f"✅ Budget API working: {response.json()}")
        else:
            print(f"❌ Budget API failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Budget API error: {e}")
    
    # Test 4: Budget Retrieval API (GET)
    print("\n4️⃣ Testing Budget Retrieval API...")
    try:
        response = requests.get(f"{API_BASE}/api/personal/budget/{TEST_WA_ID}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Budget Retrieval working: {len(data['budget_status'])} categories tracked")
        else:
            print(f"❌ Budget Retrieval failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Budget Retrieval error: {e}")
    
    # Test 5: Personal Goals API
    print("\n5️⃣ Testing Personal Goals API...")
    try:
        response = requests.get(f"{API_BASE}/api/personal/goals/{TEST_WA_ID}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Goals API working: {len(data['goals'])} goals found")
        else:
            print(f"❌ Goals API failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Goals API error: {e}")
    
    # Test 6: Feature Flag Check
    print("\n6️⃣ Testing Feature Flag Integration...")
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    enable_personal = os.getenv('ENABLE_PERSONAL_BUDGET', 'false').lower()
    default_mode = os.getenv('DEFAULT_MODE', 'business')
    
    print(f"✅ ENABLE_PERSONAL_BUDGET: {enable_personal}")
    print(f"✅ DEFAULT_MODE: {default_mode}")
    
    if enable_personal == 'true' and default_mode == 'personal':
        print("✅ Personal budget mode is properly configured!")
    else:
        print("⚠️  Personal budget mode may not be enabled. Check .env file.")
    
    print("\n" + "=" * 50)
    print("🎉 Personal Budget Flow Test Complete!")
    print("\nNext steps:")
    print("- Test WhatsApp integration with personal transactions")
    print("- Verify frontend dashboard shows real data")
    print("- Test mode switching between personal and business")

if __name__ == "__main__":
    test_personal_budget_flow()