#!/usr/bin/env python3
"""
Test script to verify personal budget feature is enabled after environment variable fix
"""

import requests
import sys

def test_personal_budget_endpoint():
    """Test if personal budget endpoint is working"""
    
    # Test health endpoint first
    print("1. Testing API health...")
    try:
        health_response = requests.get("https://api.aliran-tunai.com/api/health", timeout=10)
        if health_response.status_code == 200:
            print("✅ API is healthy")
        else:
            print(f"❌ API health check failed: {health_response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ API health check failed: {e}")
        return False
    
    # Test personal budget endpoint
    print("\n2. Testing personal budget endpoint...")
    test_wa_id = "60176757773"  # Using the wa_id from error logs
    
    try:
        pb_response = requests.get(
            f"https://api.aliran-tunai.com/api/personal/dashboard/{test_wa_id}", 
            timeout=10
        )
        
        print(f"Response Status: {pb_response.status_code}")
        
        if pb_response.status_code == 403:
            response_data = pb_response.json()
            if "not enabled" in response_data.get("error", "").lower():
                print("❌ Personal budget feature is still disabled")
                print("💡 Please set ENABLE_PERSONAL_BUDGET=true in your deployment environment variables")
                return False
            else:
                print(f"❌ 403 error but different reason: {response_data}")
                return False
                
        elif pb_response.status_code == 401:
            print("✅ Personal budget feature is enabled! (401 = missing auth token, which is expected)")
            print("💡 The feature is working, you just need to be authenticated to access it")
            return True
            
        elif pb_response.status_code == 200:
            print("✅ Personal budget feature is fully working!")
            return True
            
        else:
            print(f"⚠️ Unexpected response: {pb_response.status_code}")
            print(f"Response: {pb_response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Personal budget test failed: {e}")
        return False

def main():
    print("🧪 Testing Personal Budget Feature Fix")
    print("=" * 50)
    
    success = test_personal_budget_endpoint()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 PERSONAL BUDGET FEATURE IS WORKING!")
        print("You can now use the personal finance features in your app.")
    else:
        print("❌ PERSONAL BUDGET FEATURE STILL NEEDS CONFIGURATION")
        print("\n📋 Next Steps:")
        print("1. Add environment variable ENABLE_PERSONAL_BUDGET=true to your deployment")
        print("2. Wait for redeployment (1-2 minutes)")
        print("3. Run this test again")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)