#!/usr/bin/env python3
"""
Webhook management script for AliranTunai Telegram Bot
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8443"))
BASE_URL = f"http://localhost:{WEBHOOK_PORT}"

def set_webhook():
    """Set the webhook URL."""
    try:
        response = requests.post(f"{BASE_URL}/set_webhook")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Webhook set successfully: {data.get('webhook_url')}")
        else:
            print(f"❌ Failed to set webhook: {response.text}")
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")

def delete_webhook():
    """Delete the webhook."""
    try:
        response = requests.post(f"{BASE_URL}/delete_webhook")
        if response.status_code == 200:
            print("✅ Webhook deleted successfully")
        else:
            print(f"❌ Failed to delete webhook: {response.text}")
    except Exception as e:
        print(f"❌ Error deleting webhook: {e}")

def check_health():
    """Check bot health."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Bot is healthy and running")
        else:
            print(f"❌ Bot health check failed: {response.text}")
    except Exception as e:
        print(f"❌ Error checking health: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python webhook_manager.py [set|delete|health]")
        print("  set    - Set the webhook URL")
        print("  delete - Delete the webhook")
        print("  health - Check bot health")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "set":
        set_webhook()
    elif command == "delete":
        delete_webhook()
    elif command == "health":
        check_health()
    else:
        print("Unknown command. Use 'set', 'delete', or 'health'")
