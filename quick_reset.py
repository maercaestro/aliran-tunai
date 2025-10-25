#!/usr/bin/env python3
"""Quick one-liner to delete user registration"""

# Replace YOUR_WA_ID with your actual WhatsApp number (without +)
# Example: if your number is +60123456789, use "60123456789"

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
YOUR_WA_ID = "YOUR_WA_ID_HERE"  # ⚠️ CHANGE THIS

if MONGO_URI and YOUR_WA_ID != "60176757773":
    client = MongoClient(MONGO_URI)
    db = client.get_default_database()
    result = db.users.delete_one({"wa_id": YOUR_WA_ID})
    print(f"✅ Deleted {result.deleted_count} user(s) for {YOUR_WA_ID}")
    client.close()
else:
    print("❌ Please set MONGO_URI and YOUR_WA_ID")