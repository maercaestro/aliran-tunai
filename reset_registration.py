#!/usr/bin/env python3
"""
Reset User Registration Script
Deletes a user from MongoDB to allow re-registration for testing
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def reset_user_registration():
    """Reset user registration by deleting from MongoDB."""
    
    # Get MongoDB connection
    MONGO_URI = os.getenv("MONGO_URI")
    if not MONGO_URI:
        print("❌ MONGO_URI not found in environment variables")
        return False
    
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI)
        db = client.get_default_database()
        users_collection = db.users
        
        print("🔗 Connected to MongoDB successfully!")
        
        # Get WhatsApp ID to delete
        wa_id = input("📱 Enter WhatsApp number to reset (without +): ").strip()
        
        if not wa_id:
            print("❌ No WhatsApp number provided")
            return False
        
        # Check if user exists
        user = users_collection.find_one({"wa_id": wa_id})
        if user:
            print(f"\n👤 Found user record:")
            if 'mode' in user:
                print(f"   Mode: {user['mode']}")
            if 'name' in user:
                print(f"   Name: {user['name']}")
            elif 'owner_name' in user:
                print(f"   Owner: {user['owner_name']}")
            if 'email' in user:
                print(f"   Email: {user['email']}")
            if 'company_name' in user:
                print(f"   Company: {user['company_name']}")
            if 'monthly_budget' in user:
                print(f"   Budget: RM {user['monthly_budget']}")
            
            # Confirm deletion
            confirm = input("\n⚠️  Delete this user? (yes/no): ").strip().lower()
            
            if confirm in ['yes', 'y']:
                # Delete user
                result = users_collection.delete_one({"wa_id": wa_id})
                
                if result.deleted_count > 0:
                    print(f"✅ Successfully deleted user {wa_id}")
                    print("🎯 You can now register again with the bot!")
                    return True
                else:
                    print("❌ Failed to delete user")
                    return False
            else:
                print("❌ Deletion cancelled")
                return False
        else:
            print(f"❌ No user found with WhatsApp ID: {wa_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if 'client' in locals():
            client.close()

def list_all_users():
    """List all registered users for reference."""
    MONGO_URI = os.getenv("MONGO_URI")
    if not MONGO_URI:
        print("❌ MONGO_URI not found in environment variables")
        return
    
    try:
        client = MongoClient(MONGO_URI)
        db = client.get_default_database()
        users_collection = db.users
        
        print("📋 All registered users:")
        users = list(users_collection.find({}, {"wa_id": 1, "mode": 1, "name": 1, "owner_name": 1, "email": 1}))
        
        if users:
            for i, user in enumerate(users, 1):
                mode = user.get('mode', 'unknown')
                name = user.get('name') or user.get('owner_name', 'N/A')
                print(f"{i}. {user['wa_id']} - {mode} - {name}")
        else:
            print("No users found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    print("🎯 AliranTunai Registration Reset Tool")
    print("=" * 40)
    
    choice = input("""
Choose action:
1. Reset specific user registration
2. List all users
3. Exit

Enter choice (1-3): """).strip()
    
    if choice == '1':
        reset_user_registration()
    elif choice == '2':
        list_all_users()
    elif choice == '3':
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")