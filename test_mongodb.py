#!/usr/bin/env python3
"""
MongoDB Connection Test Script
Run this to diagnose MongoDB connectivity issues
"""

import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import ssl

def test_mongodb_connection():
    """Test MongoDB connection with different configurations."""
    
    # Load environment variables
    load_dotenv()
    
    MONGO_URI = os.getenv("MONGO_URI")
    
    if not MONGO_URI:
        print("❌ MONGO_URI environment variable not found!")
        print("📝 Make sure your .env file contains MONGO_URI=your_connection_string")
        return False
    
    print(f"🔗 Testing MongoDB connection...")
    print(f"📍 URI: {MONGO_URI[:50]}...{MONGO_URI[-20:] if len(MONGO_URI) > 70 else MONGO_URI}")
    
    # Test different connection configurations
    test_configs = [
        {
            "name": "Standard Connection with Server API",
            "config": {"server_api": ServerApi('1')}
        },
        {
            "name": "Connection with SSL settings",
            "config": {
                "server_api": ServerApi('1'),
                "ssl": True,
                "ssl_cert_reqs": ssl.CERT_NONE,
                "serverSelectionTimeoutMS": 10000
            }
        },
        {
            "name": "Basic connection without Server API",
            "config": {
                "serverSelectionTimeoutMS": 10000,
                "connectTimeoutMS": 10000,
                "socketTimeoutMS": 10000
            }
        },
        {
            "name": "Connection with TLS disabled",
            "config": {
                "tls": False,
                "serverSelectionTimeoutMS": 10000
            }
        }
    ]
    
    for i, test in enumerate(test_configs, 1):
        print(f"\n🧪 Test {i}: {test['name']}")
        try:
            client = MongoClient(MONGO_URI, **test['config'])
            
            # Test ping
            result = client.admin.command('ping')
            print(f"✅ Ping successful: {result}")
            
            # Test database access
            db = client.transactions_db
            collection = db.entries
            
            # Try to count documents (should work even if empty)
            count = collection.count_documents({})
            print(f"✅ Database access successful, found {count} documents")
            
            # Try a simple insert and delete test
            test_doc = {"test": True, "connection_test": True}
            insert_result = collection.insert_one(test_doc)
            print(f"✅ Insert test successful: {insert_result.inserted_id}")
            
            # Clean up test document
            collection.delete_one({"_id": insert_result.inserted_id})
            print(f"✅ Delete test successful")
            
            print(f"🎉 Connection test {i} PASSED!")
            client.close()
            return True
            
        except Exception as e:
            print(f"❌ Connection test {i} failed: {str(e)}")
            continue
    
    print("\n💡 Troubleshooting suggestions:")
    print("1. Check if your IP address is whitelisted in MongoDB Atlas")
    print("2. Verify the connection string is correct")
    print("3. Check if MongoDB cluster is running")
    print("4. Try connecting from a different network")
    print("5. Check MongoDB Atlas status page")
    
    return False

if __name__ == "__main__":
    success = test_mongodb_connection()
    sys.exit(0 if success else 1)
