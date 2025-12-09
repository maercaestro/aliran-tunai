import os
import logging
import json
import base64
import io
import tempfile
import requests
import re
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageFilter, ImageEnhance
import pytesseract
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("OpenCV not available, using PIL for image processing")
from flask import Flask, request, Response
import asyncio
import threading
from contractor_claim import process_contractor_claim, verify_receipt_with_stamp, generate_myinvois_einvoice

# --- Setup ---
load_dotenv()

# Securely get your tokens and keys
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., "https://yourdomain.com/webhook"
WEBHOOK_PORT = int(os.getenv("PORT", os.getenv("WEBHOOK_PORT", "8443")))  # Railway uses PORT

# Set up basic logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app for webhook
app = Flask(__name__)

# Global application variable
telegram_app = None

# --- Initialize Clients ---
# OpenAI (initialized after loading environment variables)
openai_client = None

# MongoDB
mongo_client = None
db = None
collection = None
users_collection = None

def initialize_openai_client():
    """Initialize OpenAI client with API key from environment variables."""
    global openai_client
    
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY environment variable not set!")
        return False
    
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI client initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        return False

def connect_to_mongodb():
    """Connect to MongoDB with retry logic and better error handling."""
    global mongo_client, db, collection, users_collection
    
    if not MONGO_URI:
        logger.error("MONGO_URI environment variable not set!")
        return False
    
    try:
        logger.info("Attempting to connect to MongoDB...")
        
        # Try different SSL configurations to resolve the TLS error
        connection_options = [
            # Option 1: Default settings with Server API
            {
                "server_api": ServerApi('1'),
                "serverSelectionTimeoutMS": 5000,
                "connectTimeoutMS": 5000,
                "socketTimeoutMS": 5000
            },
            # Option 2: Basic settings without Server API
            {
                "serverSelectionTimeoutMS": 5000,
                "connectTimeoutMS": 5000,
                "socketTimeoutMS": 5000
            },
            # Option 3: Minimal settings
            {
                "serverSelectionTimeoutMS": 10000
            }
        ]
        
        for i, options in enumerate(connection_options, 1):
            try:
                logger.info(f"Trying connection option {i}...")
                mongo_client = MongoClient(MONGO_URI, **options)
                
                # Test the connection with a more comprehensive ping
                result = mongo_client.admin.command('ping')
                logger.info(f"MongoDB ping result: {result}")
                
                # Set up database and collections
                db = mongo_client.transactions_db
                collection = db.entries
                users_collection = db.users
                
                logger.info(f"Successfully connected to MongoDB using option {i}!")
                return True
                
            except Exception as e:
                logger.warning(f"Connection option {i} failed: {e}")
                mongo_client = None
                continue
        
        logger.error("All MongoDB connection options failed")
        return False
        
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        mongo_client = None
        db = None
        collection = None
        users_collection = None
        return False

# Initialize MongoDB connection
connect_to_mongodb()

# --- Utility Functions ---
def escape_markdown(text):
    """Escape special characters for Telegram Markdown V2."""
    if not text:
        return text
    
    # For Markdown parse_mode, we need to escape these characters
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    # Convert to string if not already
    text = str(text)
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def safe_markdown_text(text):
    """Create a safe markdown text by escaping special characters."""
    if not text:
        return "N/A"
    
    # Just escape the problematic characters for basic Markdown
    text = str(text)
    text = text.replace('*', '\\*')  # Escape asterisks
    text = text.replace('_', '\\_')  # Escape underscores
    text = text.replace('[', '\\[')  # Escape square brackets
    text = text.replace(']', '\\]')
    text = text.replace('`', '\\`')  # Escape backticks
    
    return text

# --- Conversation State Management ---
# Store pending transactions waiting for clarification
pending_transactions = {}

def store_pending_transaction(chat_id: int, transaction_data: dict, missing_fields: list) -> None:
    """Store a transaction that needs clarification."""
    pending_transactions[chat_id] = {
        'data': transaction_data,
        'missing_fields': missing_fields,
        'timestamp': datetime.now(timezone.utc)
    }
    logger.info(f"Stored pending transaction for chat_id {chat_id}: missing {missing_fields}")

def get_pending_transaction(chat_id: int) -> dict | None:
    """Get pending transaction for a user."""
    return pending_transactions.get(chat_id)

def clear_pending_transaction(chat_id: int) -> None:
    """Clear pending transaction for a user."""
    if chat_id in pending_transactions:
        del pending_transactions[chat_id]
        logger.info(f"Cleared pending transaction for chat_id {chat_id}")

def is_clarification_response(text: str, missing_fields: list) -> bool:
    """Check if the message is likely a clarification response."""
    # Simple heuristics to detect clarification responses
    text_lower = text.lower()
    
    # If user is providing vendor/customer info
    if 'customer/vendor' in missing_fields:
        vendor_keywords = ['dari', 'from', 'kepada', 'to', 'dengan', 'with']
        if any(keyword in text_lower for keyword in vendor_keywords):
            return True
    
    # If user is providing just an item name or amount (short responses)
    if len(text.split()) <= 5:  # Short responses are likely clarifications
        return True
    
    # If user is not using transaction keywords, likely a clarification
    transaction_keywords = ['beli', 'jual', 'bayar', 'buy', 'sell', 'pay', 'purchase', 'sale']
    if not any(keyword in text_lower for keyword in transaction_keywords):
        return True
    
    return False

# --- Streak Management Functions ---
def update_user_streak(chat_id: int) -> dict:
    """Update user's daily logging streak and return streak info."""
    global mongo_client, users_collection
    
    # Check if MongoDB client is available, if not try to reconnect
    if mongo_client is None or users_collection is None:
        logger.warning("MongoDB client not available for user streak, attempting to reconnect...")
        if not connect_to_mongodb():
            logger.error("Failed to connect to MongoDB for user streak.")
            return {"streak": 0, "is_new": False, "updated": False, "error": True}
    
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Check if users_collection is initialized
        if users_collection is None:
            logger.error("Users collection not initialized")
            return {"streak": 1, "is_new": True, "updated": False}
        
        # Find user's existing data
        user_data = users_collection.find_one({"chat_id": chat_id})
        
        if not user_data:
            # New user - start streak at 1
            new_user = {
                "chat_id": chat_id,
                "streak": 1,
                "last_log_date": today
            }
            users_collection.insert_one(new_user)
            logger.info(f"Created new user streak for chat_id {chat_id}")
            return {"streak": 1, "is_new": True, "updated": True}
        
        last_log_date = user_data.get("last_log_date", "")
        current_streak = user_data.get("streak", 0)
        
        if not last_log_date:
            # User exists but no last_log_date, treat as new
            users_collection.update_one(
                {"chat_id": chat_id},
                {"$set": {"streak": 1, "last_log_date": today}}
            )
            return {"streak": 1, "is_new": True, "updated": True}
        
        # Calculate date difference
        from datetime import datetime as dt
        last_date = dt.strptime(last_log_date, "%Y-%m-%d")
        today_date = dt.strptime(today, "%Y-%m-%d")
        day_diff = (today_date - last_date).days
        
        if day_diff == 0:
            # Already logged today, no update needed
            return {"streak": current_streak, "is_new": False, "updated": False}
        elif day_diff == 1:
            # Consecutive day, increment streak
            new_streak = current_streak + 1
            users_collection.update_one(
                {"chat_id": chat_id},
                {"$set": {"streak": new_streak, "last_log_date": today}}
            )
            logger.info(f"Incremented streak for chat_id {chat_id} to {new_streak}")
            return {"streak": new_streak, "is_new": False, "updated": True}
        else:
            # Streak broken, reset to 1
            users_collection.update_one(
                {"chat_id": chat_id},
                {"$set": {"streak": 1, "last_log_date": today}}
            )
            logger.info(f"Reset streak for chat_id {chat_id} (gap of {day_diff} days)")
            return {"streak": 1, "is_new": False, "updated": True, "was_broken": True}
            
    except Exception as e:
        logger.error(f"Error updating user streak for chat_id {chat_id}: {e}")
        return {"streak": 0, "is_new": False, "updated": False, "error": True}

def get_user_streak(chat_id: int) -> dict:
    """Get user's current streak information."""
    global mongo_client, users_collection
    
    # Check if MongoDB client is available, if not try to reconnect
    if mongo_client is None or users_collection is None:
        logger.warning("MongoDB client not available for getting user streak, attempting to reconnect...")
        if not connect_to_mongodb():
            logger.error("Failed to connect to MongoDB for getting user streak.")
            return {"streak": 0, "last_log_date": "", "exists": False, "error": True}
        
        # Check again after reconnection attempt
        if users_collection is None:
            logger.error("Users collection still not available after reconnection attempt")
            return {"streak": 0, "last_log_date": "", "exists": False, "error": True}
    
    try:
        user_data = users_collection.find_one({"chat_id": chat_id})
        if user_data:
            return {
                "streak": user_data.get("streak", 0),
                "last_log_date": user_data.get("last_log_date", ""),
                "exists": True
            }
        else:
            return {"streak": 0, "last_log_date": "", "exists": False}
    except Exception as e:
        logger.error(f"Error getting user streak for chat_id {chat_id}: {e}")
        return {"streak": 0, "last_log_date": "", "exists": False, "error": True}


# --- Core AI Function (Version 2) ---
def parse_transaction_with_ai(text: str) -> dict:
    logger.info(f"Sending text to OpenAI for parsing: '{text}'")
    
    # Check if OpenAI client is initialized
    if openai_client is None:
        logger.error("OpenAI client not initialized")
        return {"error": "OpenAI client not available"}
    
    system_prompt = """
    You are an expert bookkeeping assistant. Your task is to extract transaction details from a user's message.
    Extract the following fields: 'action', 'amount' (as a number), 'customer' (or 'vendor'), 'items' (what was bought/sold),
    'terms' (e.g., 'credit', 'cash', 'hutang'), and a brief 'description'.
    
    The 'action' field MUST BE one of the following exact values: "sale", "purchase", "payment_received", or "payment_made".
    
    Action guidelines:
    - "sale": Selling goods/services to customers
    - "purchase": Buying goods/services from suppliers
    - "payment_received": Receiving money from customers (collections)
    - "payment_made": Paying money to suppliers or for expenses
    
    Pay special attention to ITEMS - this is what was actually bought or sold. Examples:
    - "beli beras 5 kg" → items: "beras 5 kg"
    - "jual ayam 2 ekor" → items: "ayam 2 ekor" 
    - "azim beli nasi lemak" → items: "nasi lemak"
    - "sold 10 widgets to ABC" → items: "widgets (10 units)"
    - "bayar supplier ABC" → action: "payment_made"
    - "terima bayaran dari customer XYZ" → action: "payment_received"
    
    The items field should capture the actual product/service being transacted, including quantities if mentioned.
    
    If a value is not found, use null.
    Return the result ONLY as a JSON object.
    """
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"}
        )
        result_json = response.choices[0].message.content
        logger.info(f"Received JSON from OpenAI: {result_json}")
        
        if result_json is None:
            logger.error("OpenAI returned None as response content")
            return {"error": "No response from OpenAI"}
            
        return json.loads(result_json)
    except Exception as e:
        logger.error(f"Error calling OpenAI: {e}")
        return {"error": str(e)}

# --- Image Processing Functions ---
def preprocess_image_for_ocr(image_bytes: bytes):
    """Preprocess image to improve OCR accuracy using PIL only."""
    try:
        # Convert bytes to PIL Image
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        if CV2_AVAILABLE:
            # Use OpenCV if available
            import numpy as np
            # Convert PIL to OpenCV format
            opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply threshold to get binary image
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            return thresh
        else:
            # Use PIL for image processing
            # Convert to grayscale
            gray_image = pil_image.convert('L')
            
            # Apply contrast enhancement
            enhancer = ImageEnhance.Contrast(gray_image)
            enhanced_image = enhancer.enhance(2.0)
            
            # Apply sharpening filter
            sharpened_image = enhanced_image.filter(ImageFilter.SHARPEN)
            
            return sharpened_image
            
    except Exception as e:
        logger.error(f"Error preprocessing image: {e}")
        raise

def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract text from image using OCR."""
    try:
        # Preprocess the image
        processed_image = preprocess_image_for_ocr(image_bytes)
        
        # Use pytesseract to extract text
        custom_config = r'--oem 3 --psm 6'
        extracted_text = pytesseract.image_to_string(processed_image, config=custom_config)
        
        logger.info(f"Extracted text from image: {extracted_text[:200]}...")
        return extracted_text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from image: {e}")
        return ""

def parse_receipt_with_ai(extracted_text: str) -> dict:
    """Parse receipt text using AI to extract transaction details."""
    logger.info(f"Sending receipt text to OpenAI for parsing: '{extracted_text[:200]}...'")
    
    # Check if OpenAI client is initialized
    if openai_client is None:
        logger.error("OpenAI client not initialized")
        return {"error": "OpenAI client not available"}
    
    system_prompt = """
    You are an expert at parsing receipts and invoices. Extract transaction details from the receipt text provided.
    
    Extract the following fields:
    - 'action': Determine if this is a "sale", "purchase", or "payment" based on context
    - 'amount': The total amount (as a number, extract from total, grand total, etc.)
    - 'customer': Customer name if this is a sale, or store/vendor name if this is a purchase
    - 'vendor': Store/business name (for purchases) or customer name (for sales)
    - 'terms': Payment method if available (e.g., 'cash', 'credit', 'card')
    - 'items': List or description of items purchased (this is VERY important - extract all items with quantities/descriptions)
    - 'description': Brief description of the transaction
    - 'date': Transaction date if available
    
    Pay special attention to ITEMS - extract all the products/services listed on the receipt:
    - Look for item names, product descriptions, services
    - Include quantities, sizes, or other specifications
    - Examples: "Nasi Lemak (2x)", "Beras 5kg", "Coffee Large", "Roti Canai (3 pcs)"
    
    If a value is not found or unclear, use null.
    For the action field, if you see a receipt from a store/business, it's usually a "purchase".
    If it's an invoice sent to a customer, it's usually a "sale".
    
    Return the result ONLY as a JSON object.
    """
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Receipt text:\n{extracted_text}"}
            ],
            response_format={"type": "json_object"}
        )
        result_json = response.choices[0].message.content
        logger.info(f"Received JSON from OpenAI: {result_json}")
        
        if result_json is None:
            logger.error("OpenAI returned None as response content")
            return {"error": "No response from OpenAI"}
            
        return json.loads(result_json)
    except Exception as e:
        logger.error(f"Error calling OpenAI for receipt parsing: {e}")
        return {"error": str(e)}

# --- Financial Metrics Functions ---
def get_ccc_metrics(chat_id: int) -> dict:
    """Calculate Cash Conversion Cycle metrics with corrected logic."""
    global mongo_client, collection
    
    # Check if MongoDB client is available, if not try to reconnect
    if mongo_client is None or collection is None:
        logger.warning("MongoDB client not available for CCC metrics, attempting to reconnect...")
        if not connect_to_mongodb():
            logger.error("Failed to connect to MongoDB for CCC metrics.")
            return {'ccc': 0, 'dso': 0, 'dio': 0, 'dpo': 0, 'error': 'Database connection failed'}
        
        # Check again after reconnection attempt
        if collection is None:
            logger.error("Collection still not available after reconnection attempt")
            return {'ccc': 0, 'dso': 0, 'dio': 0, 'dpo': 0, 'error': 'Database collection not available'}
    
    try:
        from datetime import datetime, timedelta
        ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)
        period_days = 90
        
        # Get all transactions for the period
        transactions = list(collection.find({
            "timestamp": {"$gte": ninety_days_ago},
            "chat_id": chat_id
        }))
        
        if not transactions:
            return {'ccc': 0, 'dso': 0, 'dio': 0, 'dpo': 0, 'error': 'No transactions found'}
        
        # Separate transactions by type
        sales = [t for t in transactions if t['action'] == 'sale']
        purchases = [t for t in transactions if t['action'] == 'purchase']
        payments_received = [t for t in transactions if t['action'] == 'payment_received']
        payments_made = [t for t in transactions if t['action'] == 'payment_made']
        
        # FIXED DSO CALCULATION
        # Get credit sales (sales with terms indicating credit)
        credit_terms = ['credit', 'hutang', 'receivable', 'kredit']
        credit_sales = [s for s in sales if s.get('terms') in credit_terms]
        total_credit_sales = sum(sale['amount'] for sale in credit_sales)
        
        # Calculate actual outstanding receivables
        # Match payments received to credit customers
        credit_customers = [sale.get('customer') for sale in credit_sales if sale.get('customer')]
        payments_for_credit_sales = [p for p in payments_received if 
                                   p.get('customer') in credit_customers]
        total_payments_for_credit = sum(payment['amount'] for payment in payments_for_credit_sales)
        
        outstanding_receivables = max(0, total_credit_sales - total_payments_for_credit)
        
        if total_credit_sales > 0:
            dso = (outstanding_receivables / total_credit_sales) * period_days
        else:
            dso = 0  # No credit sales = immediate payment
        
        # FIXED DIO CALCULATION  
        total_purchases = sum(p['amount'] for p in purchases)
        total_sales = sum(s['amount'] for s in sales)
        
        # Use realistic COGS estimation instead of the often-empty 'cogs' field
        # For service/food business, COGS is typically 60-70% of sales
        estimated_cogs = total_sales * 0.7
        
        # Calculate remaining inventory
        remaining_inventory = max(0, total_purchases - estimated_cogs)
        
        if estimated_cogs > 0:
            dio = (remaining_inventory / estimated_cogs) * period_days
        else:
            # No sales recorded, estimate based on business type
            if total_purchases > 0:
                dio = 30  # Default for active inventory business
            else:
                dio = 0  # Service business with no inventory
        
        # FIXED DPO CALCULATION
        # Get credit purchases
        credit_purchases = [p for p in purchases if p.get('terms') in credit_terms]
        total_credit_purchases = sum(p['amount'] for p in credit_purchases)
        
        # Total payments made (assuming they pay down credit purchases)
        total_payments_made_amount = sum(p['amount'] for p in payments_made)
        
        outstanding_payables = max(0, total_credit_purchases - total_payments_made_amount)
        
        if total_credit_purchases > 0:
            dpo = (outstanding_payables / total_credit_purchases) * period_days
        else:
            dpo = 0  # No credit purchases = immediate payment
        
        # Calculate final CCC
        ccc = dso + dio - dpo
        
        # Enhanced transaction breakdown
        transaction_breakdown_list = []
        action_summary = {}
        for transaction in transactions:
            action = transaction['action']
            if action not in action_summary:
                action_summary[action] = {'count': 0, 'total_amount': 0}
            action_summary[action]['count'] += 1
            action_summary[action]['total_amount'] += transaction['amount']
        
        for action, data in action_summary.items():
            transaction_breakdown_list.append({
                '_id': action,
                'count': data['count'],
                'total_amount': data['total_amount']
            })
        
        logger.info(f"FIXED CCC calculation for chat_id {chat_id}:")
        logger.info(f"  DSO: {dso:.1f} days (credit sales: ${total_credit_sales:.2f}, outstanding: ${outstanding_receivables:.2f})")
        logger.info(f"  DIO: {dio:.1f} days (purchases: ${total_purchases:.2f}, est. COGS: ${estimated_cogs:.2f}, inventory: ${remaining_inventory:.2f})")
        logger.info(f"  DPO: {dpo:.1f} days (credit purchases: ${total_credit_purchases:.2f}, outstanding payables: ${outstanding_payables:.2f})")
        logger.info(f"  CCC: {ccc:.1f} days")
        
        return {
            'ccc': round(ccc, 1),
            'dso': round(dso, 1),
            'dio': round(dio, 1),
            'dpo': round(dpo, 1),
            'transaction_breakdown': transaction_breakdown_list,
            'financial_details': {
                'total_sales': total_sales,
                'total_purchases': total_purchases,
                'estimated_cogs': estimated_cogs,
                'remaining_inventory': remaining_inventory,
                'total_credit_sales': total_credit_sales,
                'outstanding_receivables': outstanding_receivables,
                'total_credit_purchases': total_credit_purchases,
                'outstanding_payables': outstanding_payables,
                'total_payments_received': sum(p['amount'] for p in payments_received),
                'total_payments_made': total_payments_made_amount
            }
        }
        
    except Exception as e:
        logger.error(f"Error in FIXED CCC calculation for chat_id {chat_id}: {e}")
        return {'ccc': 0, 'dso': 0, 'dio': 0, 'dpo': 0, 'error': str(e)}

def generate_actionable_advice(metrics: dict) -> str:
    """Generate actionable advice based on financial metrics."""
    dso = metrics.get('dso', 0)
    dio = metrics.get('dio', 0)
    dpo = metrics.get('dpo', 0)
    ccc = metrics.get('ccc', 0)
    transaction_breakdown = metrics.get('transaction_breakdown', [])
    
    # Create a breakdown summary
    breakdown_summary = ""
    if transaction_breakdown:
        for item in transaction_breakdown:
            action = item['_id']
            count = item['count']
            breakdown_summary += f"• {action.capitalize()}: {count} transactions\n"
    
    # Generate primary advice based on CCC components
    if ccc > 60:
        primary_advice = "🚨 **High Cash Conversion Cycle** - Your money is tied up for too long! Focus on the recommendations below."
    elif ccc > 30:
        primary_advice = "⚠️ **Moderate Cash Conversion Cycle** - There's room for improvement."
    elif ccc > 0:
        primary_advice = "✅ **Good Cash Conversion Cycle** - You're managing cash flow well!"
    else:
        primary_advice = "🔥 **Excellent Cash Flow** - You're getting paid before you pay suppliers!"
    
    # Generate specific recommendations
    recommendations = []
    
    if dso > 45:
        recommendations.append("📞 **Reduce DSO**: Follow up on overdue invoices more aggressively. Consider offering early payment discounts.")
    elif dso > 0:
        recommendations.append("💳 **DSO Optimization**: Your credit collection is reasonable, but consider tightening credit terms slightly.")
    
    if dio > 35:
        recommendations.append("📦 **Reduce DIO**: Your inventory is moving slowly. Consider promotions, bundling, or improving demand forecasting.")
    elif dio > 15:
        recommendations.append("🏪 **DIO Management**: Inventory turnover is moderate. Monitor slow-moving items closely.")
    elif dio > 0:
        recommendations.append("⚡ **DIO Excellent**: Your inventory turns over quickly - great job!")
    
    if dpo < 15:
        recommendations.append("⏰ **Extend DPO**: You're paying suppliers very quickly. Negotiate longer payment terms (30-45 days) to improve cash flow.")
    elif dpo < 30:
        recommendations.append("💰 **DPO Opportunity**: Consider negotiating slightly longer payment terms with suppliers.")
    else:
        recommendations.append("🤝 **DPO Good**: You're managing supplier payments well.")
    
    # Combine advice
    if recommendations:
        advice = primary_advice + "\n\n**Recommendations:**\n" + "\n".join(recommendations)
    else:
        advice = primary_advice + "\n\n**Keep up the excellent cash flow management!**"
    
    # Add transaction summary if available
    if breakdown_summary:
        advice += f"\n\n**Your Transaction Activity (last 90 days):**\n{breakdown_summary}"
    
    return advice

# --- Database Function ---
def save_to_mongodb(data: dict, chat_id: int, image_data: bytes | None = None) -> bool:
    """Saves the transaction data to MongoDB with user isolation."""
    global mongo_client, collection
    
    if "error" in data:
        logger.error("Data contains an error, cannot save to MongoDB.")
        return False
    
    # Check if MongoDB client is available, if not try to reconnect
    if mongo_client is None or collection is None:
        logger.warning("MongoDB client not available, attempting to reconnect...")
        if not connect_to_mongodb():
            logger.error("Failed to connect to MongoDB, cannot save data.")
            return False
    
    try:
        # Add user isolation with chat_id
        data['chat_id'] = chat_id
        
        # Add a timestamp to the record
        data['timestamp'] = datetime.now(timezone.utc)
        
        # Add COGS calculation for sales
        if data.get('action') == 'sale' and data.get('amount'):
            # Calculate COGS as 60% of sale amount
            data['cogs'] = round(float(data['amount']) * 0.6, 2)
            logger.info(f"Added COGS calculation for sale: {data['cogs']} (60% of {data['amount']})")
        
        # Add image data if provided
        if image_data:
            # Convert image to base64 for storage
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            data['receipt_image'] = image_base64
            data['has_image'] = True
        else:
            data['has_image'] = False
        
        # Check if MongoDB client and collection are available
        if mongo_client is None or collection is None:
            logger.error("MongoDB client or collection not initialized")
            return False
        
        # Test connection before inserting
        mongo_client.admin.command('ping')
        
        # Insert the data into the collection
        result = collection.insert_one(data)
        logger.info(f"Successfully inserted data into MongoDB for chat_id {chat_id}: {data.get('action', 'Unknown')} - {data.get('amount', 'N/A')} (ID: {result.inserted_id})")
        return True
        
    except Exception as e:
        logger.error(f"Error saving to MongoDB: {e}")
        # Try to reconnect for next time
        connect_to_mongodb()
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_text = """
Hi! I'm your financial assistant. 

You can:
📝 Send me a text message describing a transaction
📸 Send me a photo of a receipt to automatically extract transaction details
📊 Use /status to get your financial health report with actionable advice
📋 Use /summary to see your recent transactions
🔥 Use /streak to check your daily logging streak
🔧 Use /test_db to test database connection

All your data is kept private and separate from other users!
Build your daily logging streak by recording transactions every day! 💪
    """
    if update.message:
        await update.message.reply_text(welcome_text)

async def test_db(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Test database connection manually."""
    if not update.message:
        return
        
    try:
        chat_id = update.message.chat_id
        logger.info(f"Manual database test requested by chat_id {chat_id}")
        
        # Test connection
        if connect_to_mongodb() and collection is not None:
            # Try to perform a simple query
            test_result = collection.find_one({"chat_id": chat_id})
            count = collection.count_documents({"chat_id": chat_id})
            
            reply_text = f"""✅ **Database Connection Test Successful!**

🔗 **Connection Status**: Connected
📊 **Your Records Found**: {count} transactions
🗄️ **Database**: transactions_db
📋 **Collection**: entries
👥 **Users Collection**: Available

**MongoDB URI**: {(MONGO_URI[:20] + '...' + MONGO_URI[-10:]) if MONGO_URI and len(MONGO_URI) > 30 else (MONGO_URI or 'Not set')}

The database is working properly! 🎉"""
            
            if update.message:
                await update.message.reply_text(reply_text, parse_mode='Markdown')
        else:
            reply_text = f"""❌ **Database Connection Test Failed!**

🔗 **Connection Status**: Failed
📊 **Error**: Cannot connect to MongoDB

**Possible Issues:**
1. Check your IP address is whitelisted in MongoDB Atlas
2. Verify MONGO_URI environment variable is correct
3. Check network connectivity
4. Verify MongoDB cluster is running

**MongoDB URI**: {(MONGO_URI[:20] + '...' + MONGO_URI[-10:]) if MONGO_URI and len(MONGO_URI) > 30 else (MONGO_URI or 'Not set')}"""
            
            if update.message:
                await update.message.reply_text(reply_text, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Error in database test: {e}")
        if update.message:
            await update.message.reply_text(f"❌ Database test failed with error: {str(e)}")

# --- Telegram Bot Handlers ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Check if update has message
    if not update.message:
        logger.warning("Received update without message")
        return
    
    user_message = update.message.text
    chat_id = update.message.chat_id
    
    if user_message is None:
        logger.warning("Received message without text content")
        return
    
    logger.info(f"Received message from chat_id {chat_id}: '{user_message}'")
    
    # Contractor claim workflow - only images supported
    await update.message.reply_text(
        "📸 *Contractor Claim System*\n\n"
        "Please send me a scanned receipt with an official stamp to process your payment claim.\n\n"
        "✅ *Requirements:*\n"
        "• Clear image of receipt\n"
        "• Official stamp visible\n"
        "• All transaction details readable",
        parse_mode='Markdown'
    )
        missing_fields.append('customer/vendor')

    # If there are missing fields, store transaction and ask for clarification
    if clarification_questions:
        # Store the partial transaction
        store_pending_transaction(chat_id, parsed_data, missing_fields)
        
        # Safely get action with proper null handling
        action = parsed_data.get('action') or 'transaction'
        clarification_text = f"🤔 I understood this as a <b>{action}</b> but I need some clarification:\n\n"
        clarification_text += "\n".join(clarification_questions)
        clarification_text += "\n\nPlease provide the missing information and I'll log the complete transaction for you! 😊"
        
        await update.message.reply_text(clarification_text, parse_mode='HTML')
        return

    # Save the complete transaction
    success = save_to_mongodb(parsed_data, chat_id)
    
    if success:
        # Update user's daily logging streak
        streak_info = update_user_streak(chat_id)
        
        # Create a user-friendly confirmation message
        action = (parsed_data.get('action') or 'transaction').capitalize()
        amount = parsed_data.get('amount', 0)
        customer = safe_markdown_text(parsed_data.get('customer') or parsed_data.get('vendor', 'N/A'))
        items = safe_markdown_text(parsed_data.get('items', 'N/A'))
        
        reply_text = f"✅ Logged: {action} of <b>{amount}</b> with <b>{customer}</b>"
        if items and items != 'N/A':
            reply_text += f"\n📦 Items: {items}"
        
        # Add streak information if updated
        if streak_info.get('updated', False) and not streak_info.get('error', False):
            streak = streak_info.get('streak', 0)
            if streak_info.get('is_new', False):
                reply_text += f"\n\n🔥 Welcome! Your daily logging streak starts now: <b>{streak} day</b>!"
            elif streak_info.get('was_broken', False):
                reply_text += f"\n\n🔥 Streak reset! Your daily logging streak is now <b>{streak} day</b>. Keep it up!"
            else:
                day_word = "day" if streak == 1 else "days"
                reply_text += f"\n\n🔥 Your daily streak is now <b>{streak} {day_word}</b>! Keep it up!"
        elif not streak_info.get('updated', False) and not streak_info.get('error', False):
            # Already logged today
            streak = streak_info.get('streak', 0)
            day_word = "day" if streak == 1 else "days"
            reply_text += f"\n\n🔥 You've already logged today! Current streak: <b>{streak} {day_word}</b>"
        
        await update.message.reply_text(reply_text, parse_mode='HTML')
    else:
        await update.message.reply_text("❌ There was an error saving your transaction to the database.")

async def handle_clarification_response(update: Update, context: ContextTypes.DEFAULT_TYPE, user_message: str, pending: dict) -> None:
    """Handle user's clarification response to complete the transaction."""
    if not update.message:
        return
        
    chat_id = update.message.chat_id
    transaction_data = pending['data'].copy()
    missing_fields = pending['missing_fields']
    
    logger.info(f"Processing clarification for chat_id {chat_id}: '{user_message}' for fields {missing_fields}")
    
    # Try to extract missing information from the clarification
    user_message_lower = user_message.lower()
    
    # Handle vendor/customer clarification
    if 'customer/vendor' in missing_fields:
        # Extract vendor/customer name from clarification
        vendor_patterns = ['dari', 'from', 'kepada', 'to', 'dengan', 'with']
        extracted_name = user_message.strip()
        
        # Remove common prepositions
        for pattern in vendor_patterns:
            if extracted_name.lower().startswith(pattern + ' '):
                extracted_name = extracted_name[len(pattern):].strip()
        
        action = transaction_data.get('action') or ''
        if action == 'purchase':
            transaction_data['vendor'] = extracted_name
        elif action in ['payment_made']:
            transaction_data['vendor'] = extracted_name  # Who we paid
        elif action in ['payment_received']:
            transaction_data['customer'] = extracted_name  # Who paid us
        else:
            transaction_data['customer'] = extracted_name
        
        missing_fields.remove('customer/vendor')
    
    # Handle items clarification
    if 'items' in missing_fields and not transaction_data.get('items'):
        transaction_data['items'] = user_message.strip()
        missing_fields.remove('items')
    
    # Handle amount clarification
    if 'amount' in missing_fields and not transaction_data.get('amount'):
        # Try to extract number from the message
        import re
        numbers = re.findall(r'\d+(?:\.\d+)?', user_message)
        if numbers:
            transaction_data['amount'] = float(numbers[0])
            missing_fields.remove('amount')
    
    # Check if we still have missing fields
    if missing_fields:
        # Update pending transaction and ask for remaining info
        store_pending_transaction(chat_id, transaction_data, missing_fields)
        
        clarification_questions = []
        for field in missing_fields:
            if field == 'items':
                action = transaction_data.get('action') or 'transaction'
                if action == 'purchase':
                    clarification_questions.append("🛒 What item did you buy?")
                elif action == 'sale':
                    clarification_questions.append("🏪 What item did you sell?")
                else:
                    clarification_questions.append("📦 What item was involved?")
            elif field == 'amount':
                clarification_questions.append("💰 What was the amount?")
            elif field == 'customer/vendor':
                action = transaction_data.get('action') or 'transaction'
                if action == 'purchase':
                    clarification_questions.append("🏪 Who did you buy from?")
                elif action == 'sale':
                    clarification_questions.append("👤 Who did you sell to?")
                elif action == 'payment_made':
                    clarification_questions.append("💸 Who did you pay?")
                elif action == 'payment_received':
                    clarification_questions.append("💰 Who paid you?")
                else:
                    clarification_questions.append("👥 Who was the other party?")
        
        clarification_text = "👍 Got it! I still need:\n\n"
        clarification_text += "\n".join(clarification_questions)
        
        await update.message.reply_text(clarification_text, parse_mode='Markdown')
        return
    
    # All fields completed, save the transaction
    clear_pending_transaction(chat_id)
    success = save_to_mongodb(transaction_data, chat_id)
    
    if success:
        # Update user's daily logging streak
        streak_info = update_user_streak(chat_id)
        
        action = (transaction_data.get('action') or 'transaction').capitalize()
        amount = transaction_data.get('amount', 0)
        customer = safe_markdown_text(transaction_data.get('customer') or transaction_data.get('vendor', 'N/A'))
        items = safe_markdown_text(transaction_data.get('items', 'N/A'))
        
        reply_text = f"✅ **Transaction completed!** {action} of **{amount}** with **{customer}**"
        if items and items != 'N/A':
            reply_text += f"\n📦 Items: {items}"
        
        # Add streak information if updated
        if streak_info.get('updated', False) and not streak_info.get('error', False):
            streak = streak_info.get('streak', 0)
            if streak_info.get('is_new', False):
                reply_text += f"\n\n🔥 Welcome! Your daily logging streak starts now: **{streak} day**!"
            elif streak_info.get('was_broken', False):
                reply_text += f"\n\n🔥 Streak reset! Your daily logging streak is now **{streak} day**. Keep it up!"
            else:
                day_word = "day" if streak == 1 else "days"
                reply_text += f"\n\n🔥 Your daily streak is now **{streak} {day_word}**! Keep it up!"
        elif not streak_info.get('updated', False) and not streak_info.get('error', False):
            # Already logged today
            streak = streak_info.get('streak', 0)
            day_word = "day" if streak == 1 else "days"
            reply_text += f"\n\n🔥 You've already logged today! Current streak: **{streak} {day_word}**"
        
        await update.message.reply_text(reply_text, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ There was an error saving your transaction to the database.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send financial health status report to user."""
    if not update.message:
        return
        
    try:
        chat_id = update.message.chat_id
        logger.info(f"Generating status report for chat_id {chat_id}")
        
        # Get the financial metrics for this specific user
        metrics = get_ccc_metrics(chat_id=chat_id)
        
        # Generate actionable advice
        advice = generate_actionable_advice(metrics)
        
        # Create the formatted report
        report = f"""💡 **Your Financial Health Status** (last 90 days)

Your Cash Conversion Cycle is **{metrics['ccc']} days**.
_This is how long your money is tied up in operations before becoming cash again._

**Component Analysis:**
🤝 Days Sales Outstanding (DSO): **{metrics['dso']} days**
   _Time to collect money from credit sales_

📦 Days Inventory Outstanding (DIO): **{metrics['dio']} days**
   _Time inventory sits before being sold_

💸 Days Payable Outstanding (DPO): **{metrics['dpo']} days**
   _Time you take to pay suppliers_

**Formula:** CCC = DSO + DIO - DPO = {metrics['dso']} + {metrics['dio']} - {metrics['dpo']} = **{metrics['ccc']} days**

---
{advice}"""
        
        await update.message.reply_text(report, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error generating status report: {e}")
        await update.message.reply_text("❌ Sorry, there was an error generating your financial status report.")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a summary of user's transactions."""
    if not update.message:
        return
        
    try:
        chat_id = update.message.chat_id
        logger.info(f"Generating summary for chat_id {chat_id}")
        
        # Check if collection is available
        if collection is None:
            await update.message.reply_text("❌ Database not available. Please try again later.")
            return
        
        # Query only this user's transactions
        user_transactions = list(collection.find({'chat_id': chat_id}).sort('timestamp', -1).limit(10))
        
        if not user_transactions:
            await update.message.reply_text("📭 You don't have any transactions recorded yet. Start by sending me a transaction or receipt photo!")
            return
        
        # Format the summary
        summary_text = f"📊 **Your Recent Transactions Summary**\n\n"
        total_amount = 0
        
        for i, transaction in enumerate(user_transactions[:5], 1):
            action = transaction.get('action', 'N/A').capitalize()
            amount = transaction.get('amount', 0)
            vendor = safe_markdown_text(transaction.get('vendor') or transaction.get('customer', 'N/A'))
            items = safe_markdown_text(transaction.get('items', ''))
            date = transaction.get('timestamp', datetime.now()).strftime('%m/%d') if transaction.get('timestamp') else 'N/A'
            
            # Format the line with items if available
            line = f"{i}. **{action}** - {amount} with {vendor}"
            if items and items != 'N/A':
                line += f" ({items})"
            line += f" ({date})\n"
            
            summary_text += line
            
            if isinstance(amount, (int, float)):
                total_amount += amount
        
        summary_text += f"\n💰 **Total Amount**: {total_amount}"
        summary_text += f"\n📝 **Total Transactions**: {len(user_transactions)}"
        
        if len(user_transactions) > 5:
            summary_text += f"\n\n_Showing latest 5 of {len(user_transactions)} transactions_"
        
        await update.message.reply_text(summary_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error generating summary for chat_id {chat_id}: {e}")
        await update.message.reply_text("❌ Sorry, there was an error generating your transaction summary.")

async def streak(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send user's current daily logging streak."""
    if not update.message:
        return
        
    try:
        chat_id = update.message.chat_id
        logger.info(f"Getting streak for chat_id {chat_id}")
        
        streak_info = get_user_streak(chat_id)
        
        if streak_info.get('exists', False):
            streak = streak_info.get('streak', 0)
            last_log_date = streak_info.get('last_log_date', '')
            
            # Check if streak is current (logged today or yesterday)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if last_log_date:
                from datetime import datetime as dt
                last_date = dt.strptime(last_log_date, "%Y-%m-%d")
                today_date = dt.strptime(today, "%Y-%m-%d")
                day_diff = (today_date - last_date).days
                
                if day_diff == 0:
                    status = "You've logged today! 🎉"
                elif day_diff == 1:
                    status = "Log a transaction today to continue your streak! ⏰"
                else:
                    status = "Your streak has been broken. Log a transaction to start a new one! 💪"
            else:
                status = "Log a transaction to start your streak! 🚀"
            
            day_word = "day" if streak == 1 else "days"
            reply_text = f"""🔥 **Your Daily Logging Streak**

Current streak: **{streak} {day_word}**
Last logged: {last_log_date if last_log_date else 'Never'}

{status}

Keep logging every day to build up your streak! 📈"""
            
            await update.message.reply_text(reply_text, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                "You don't have a streak yet. Log your first transaction to start one! 🚀\n\n"
                "Just send me a message about any purchase, sale, or payment to begin your daily logging streak! 💪"
            )
        
    except Exception as e:
        logger.error(f"Error getting streak for chat_id {chat_id}: {e}")
        await update.message.reply_text("❌ Sorry, there was an error getting your streak information.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo messages - Contractor claim workflow with stamp verification."""
    if not update.message:
        return
        
    try:
        chat_id = update.message.chat_id
        logger.info(f"Processing contractor claim receipt from chat_id {chat_id}")
        
        # Check if photo exists
        if not update.message.photo:
            await update.message.reply_text("❌ No photo found in the message.")
            return
        
        # Send initial processing message
        processing_msg = await update.message.reply_text(
            "🔍 Processing your contractor claim...\n\n"
            "• Verifying stamp\n"
            "• Extracting receipt details\n"
            "• Generating e-invoice\n"
            "• Saving to database\n\n"
            "Please wait..."
        )
        
        # Get the largest photo (best quality)
        photo = update.message.photo[-1]
        
        # Get file info
        file = await context.bot.get_file(photo.file_id)
        
        # Download the image directly using the telegram file object
        image_data = await file.download_as_bytearray()
        
        # Get user info from database (if available)
        user_info = None
        if users_collection:
            try:
                user_doc = users_collection.find_one({"chat_id": chat_id})
                if user_doc:
                    user_info = {
                        'user_type': user_doc.get('user_type', 'unknown'),
                        'name': user_doc.get('owner_name') or user_doc.get('name', ''),
                        'company': user_doc.get('company_name') or user_doc.get('company', '')
                    }
            except Exception as e:
                logger.warning(f"Could not fetch user info: {e}")
        
        # Process contractor claim with full workflow (including MongoDB storage)
        logger.info("Processing contractor claim workflow...")
        success, message, einvoice = process_contractor_claim(
            bytes(image_data),
            wa_id=str(chat_id),  # Use chat_id as identifier for Telegram
            user_info=user_info
        )
        
        if success and einvoice:
            # Save e-invoice to file for backup
            invoice_id = einvoice['Invoice']['ID']
            try:
                einvoice_dir = 'einvoices'
                os.makedirs(einvoice_dir, exist_ok=True)
                einvoice_path = os.path.join(einvoice_dir, f'{invoice_id}.json')
                with open(einvoice_path, 'w') as f:
                    json.dump(einvoice, f, indent=2)
                logger.info(f"E-invoice also saved to file: {einvoice_path}")
                
                # Optionally send the e-invoice JSON as a document
                with open(einvoice_path, 'rb') as f:
                    await update.message.reply_document(
                        document=f,
                        filename=f'{invoice_id}.json',
                        caption='📄 MyInvois E-Invoice (UBL 2.1 Compliant)'
                    )
            except Exception as e:
                logger.warning(f"Could not save/send e-invoice file: {e}")
            
            # Send success message
            await processing_msg.edit_text(message)
        else:
            # Send rejection message
            await processing_msg.edit_text(message)
            
    except Exception as e:
        logger.error(f"Error processing contractor claim: {e}")
        await update.message.reply_text("❌ Sorry, there was an error processing your contractor claim. Please try again.")
            # Create detailed confirmation message
            action = (parsed_data.get('action') or 'transaction').capitalize()
            amount = parsed_data.get('amount', 'N/A')
            vendor = parsed_data.get('vendor') or parsed_data.get('customer', 'N/A')
            date = parsed_data.get('date', 'N/A')
            items = parsed_data.get('items', 'N/A')
            description = parsed_data.get('description', 'N/A')
            
            reply_text = f"""✅ <b>Receipt processed successfully!</b>

📋 <b>Details extracted:</b>
• Action: {action}
• Amount: {amount}
• Vendor/Customer: {vendor}
• Items: {items}
• Date: {date}
• Description: {description}

💾 Saved to database with receipt image attached."""
            
            await processing_msg.edit_text(reply_text, parse_mode='HTML')
        else:
            await processing_msg.edit_text("❌ There was an error saving your receipt to the database.")
            
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        await update.message.reply_text("❌ Sorry, there was an error processing your receipt. Please try again.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle document uploads (in case user sends image as document)."""
    if not update.message or not update.message.document:
        return
        
    document = update.message.document
    
    # Check if it's an image document
    if document.mime_type and document.mime_type.startswith('image/'):
        # Treat it as a photo
        await handle_photo_document(update, context)
    else:
        await update.message.reply_text("📄 I can only process image files. Please send your receipt as a photo.")

async def handle_photo_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle image documents - Contractor claim workflow with stamp verification."""
    if not update.message or not update.message.document:
        return
        
    try:
        chat_id = update.message.chat_id
        processing_msg = await update.message.reply_text(
            "🔍 Processing your contractor claim...\n\n"
            "• Verifying stamp\n"
            "• Extracting receipt details\n"
            "• Generating e-invoice\n"
            "• Saving to database\n\n"
            "Please wait..."
        )
        
        document = update.message.document
        file = await context.bot.get_file(document.file_id)
        
        # Download the image directly using the telegram file object
        image_data = await file.download_as_bytearray()
        
        # Get user info from database (if available)
        user_info = None
        if users_collection:
            try:
                user_doc = users_collection.find_one({"chat_id": chat_id})
                if user_doc:
                    user_info = {
                        'user_type': user_doc.get('user_type', 'unknown'),
                        'name': user_doc.get('owner_name') or user_doc.get('name', ''),
                        'company': user_doc.get('company_name') or user_doc.get('company', '')
                    }
            except Exception as e:
                logger.warning(f"Could not fetch user info: {e}")
        
        # Process contractor claim with full workflow (including MongoDB storage)
        logger.info("Processing contractor claim workflow from document...")
        success, message, einvoice = process_contractor_claim(
            bytes(image_data),
            wa_id=str(chat_id),  # Use chat_id as identifier for Telegram
            user_info=user_info
        )
        
        if success and einvoice:
            # Save e-invoice to file for backup
            invoice_id = einvoice['Invoice']['ID']
            try:
                einvoice_dir = 'einvoices'
                os.makedirs(einvoice_dir, exist_ok=True)
                einvoice_path = os.path.join(einvoice_dir, f'{invoice_id}.json')
                with open(einvoice_path, 'w') as f:
                    json.dump(einvoice, f, indent=2)
                logger.info(f"E-invoice also saved to file: {einvoice_path}")
                
                # Optionally send the e-invoice JSON as a document
                with open(einvoice_path, 'rb') as f:
                    await update.message.reply_document(
                        document=f,
                        filename=f'{invoice_id}.json',
                        caption='📄 MyInvois E-Invoice (UBL 2.1 Compliant)'
                    )
            except Exception as e:
                logger.warning(f"Could not save/send e-invoice file: {e}")
            
            # Send success message
            await processing_msg.edit_text(message)
        else:
            # Send rejection message
            await processing_msg.edit_text(message)
            
    except Exception as e:
        logger.error(f"Error processing contractor claim document: {e}")
        await processing_msg.edit_text("❌ Sorry, there was an error processing your contractor claim. Please try again.")
                logger.warning(f"Could not save/send e-invoice file: {e}")
            
            # Send success message
            await processing_msg.edit_text(message)
        else:
            # Send rejection message
            await processing_msg.edit_text(message)
            
    except Exception as e:
        logger.error(f"Error processing contractor claim document: {e}")
        await processing_msg.edit_text("❌ Sorry, there was an error processing your contractor claim. Please try again.")

# --- Webhook Routes ---
@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook updates from Telegram."""
    try:
        # Get the JSON data from the request
        json_data = request.get_json()
        
        if not json_data:
            logger.warning("Received empty webhook data")
            return Response(status=200)
        # Check if telegram_app is initialized
        if telegram_app is None:
            logger.error("Telegram app not initialized")
            return Response("Telegram app not initialized", status=500)
        
        # Create Update object from JSON
        update = Update.de_json(json_data, telegram_app.bot)
        
        if update:
            # Create a new event loop for this thread if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Process the update
            loop.run_until_complete(telegram_app.process_update(update))
        
        return Response(status=200)
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return Response(status=500)

@app.route('/', methods=['GET'])
def root():
    """Root endpoint."""
    return {
        "message": "Telegram Bot is running",
        "status": "active",
        "mode": "webhook" if WEBHOOK_URL else "polling",
        "endpoints": {
            "health": "/health",
            "webhook": "/webhook",
            "set_webhook": "/set_webhook",
            "delete_webhook": "/delete_webhook"
        }
    }, 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    logger.info("Health check requested")
    try:
        # Basic health check without dependencies
        response = {
            "status": "healthy", 
            "service": "telegram-bot",
            "mode": "webhook" if WEBHOOK_URL else "polling",
            "port": WEBHOOK_PORT
        }
        
        # Optional: Test MongoDB connection (non-blocking)
        try:
            if mongo_client:
                # Quick ping to test connection
                mongo_client.admin.command('ping')
                response["database"] = "connected"
            else:
                response["database"] = "not_initialized"
        except Exception as db_error:
            response["database"] = f"error: {str(db_error)}"
            
        logger.info(f"Health check successful: {response}")
        return response, 200
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}, 503

@app.route('/set_webhook', methods=['POST'])
def set_webhook():
    """Set the webhook URL."""
    try:
        if not WEBHOOK_URL:
            return {"error": "WEBHOOK_URL not configured"}, 400
        
        if telegram_app is None:
            return {"error": "Telegram app not initialized"}, 500
            
        webhook_url = f"{WEBHOOK_URL}/webhook"
        result = asyncio.run(telegram_app.bot.set_webhook(url=webhook_url))
        
        if result:
            logger.info(f"Webhook set successfully to {webhook_url}")
            return {"status": "success", "webhook_url": webhook_url}, 200
        else:
            return {"error": "Failed to set webhook"}, 500
            
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return {"error": str(e)}, 500

@app.route('/delete_webhook', methods=['POST'])
def delete_webhook():
    """Delete the webhook."""
    try:
        if telegram_app is None:
            return {"error": "Telegram app not initialized"}, 500
            
        result = asyncio.run(telegram_app.bot.delete_webhook())
        
        if result:
            logger.info("Webhook deleted successfully")
            return {"status": "success", "message": "Webhook deleted"}, 200
        else:
            return {"error": "Failed to delete webhook"}, 500
            
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
        return {"error": str(e)}, 500

def main() -> None:
    """Start the bot in either polling or webhook mode based on configuration."""
    global telegram_app
    
    # Initialize OpenAI client
    if not initialize_openai_client():
        logger.error("Failed to initialize OpenAI client. Exiting.")
        return
    
    # Try to connect to MongoDB (non-blocking for webhook mode)
    try:
        connect_to_mongodb()
        logger.info("✅ MongoDB connection established")
    except Exception as e:
        logger.error(f"⚠️ MongoDB connection failed: {e}")
        logger.warning("Bot will continue without database features")
    
    # Create the application
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN environment variable not set!")
        return None
        
    telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("status", status))
    telegram_app.add_handler(CommandHandler("summary", summary))
    telegram_app.add_handler(CommandHandler("streak", streak))
    telegram_app.add_handler(CommandHandler("test_db", test_db))
    telegram_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    telegram_app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # For Railway deployment, always start Flask server for health checks
    # Check if we're in a production environment (Railway sets PORT)
    is_production = os.getenv("PORT") is not None
    
    # Check if webhook mode is configured
    if WEBHOOK_URL or is_production:
        # WEBHOOK MODE or PRODUCTION MODE
        mode_type = "WEBHOOK" if WEBHOOK_URL else "PRODUCTION (health check only)"
        logger.info(f"🔗 Starting bot in {mode_type} mode...")
        
        # Initialize the application for webhook in a non-blocking way
        try:
            asyncio.run(telegram_app.initialize())
            logger.info("✅ Telegram app initialized successfully")
        except Exception as e:
            logger.error(f"⚠️ Failed to initialize telegram app: {e}")
            # Continue anyway to allow health checks
        
        if WEBHOOK_URL:
            logger.info("Bot is running with webhook mode, multi-user support, image processing, financial status, and streak capabilities...")
            logger.info(f"Webhook will be available at: {WEBHOOK_URL}/webhook")
        else:
            logger.info("Bot is running with health check support for Railway deployment...")
            
        logger.info(f"Health check available at: http://0.0.0.0:{WEBHOOK_PORT}/health")
        logger.info(f"Set webhook endpoint: http://0.0.0.0:{WEBHOOK_PORT}/set_webhook")
        logger.info(f"Delete webhook endpoint: http://0.0.0.0:{WEBHOOK_PORT}/delete_webhook")
        
        if not WEBHOOK_URL:
            logger.info("📝 Note: WEBHOOK_URL not set, bot will run in polling mode alongside Flask server")
            
            # Start telegram app in polling mode in a separate thread
            def run_telegram_polling():
                try:
                    if telegram_app is None:
                        logger.error("❌ Telegram app not initialized, cannot start polling")
                        return
                    logger.info("🔄 Starting Telegram polling in background...")
                    telegram_app.run_polling()
                except Exception as e:
                    logger.error(f"❌ Telegram polling failed: {e}")
            
            # Start polling in background thread
            polling_thread = threading.Thread(target=run_telegram_polling, daemon=True)
            polling_thread.start()
        
        # Start Flask app for webhook with better error handling
        try:
            logger.info(f"🚀 Starting Flask app on 0.0.0.0:{WEBHOOK_PORT}")
            app.run(host='0.0.0.0', port=WEBHOOK_PORT, debug=False, threaded=True)
        except Exception as e:
            logger.error(f"❌ Failed to start Flask app: {e}")
            raise
        
    else:
        # POLLING MODE
        logger.info("🔄 Starting bot in POLLING mode...")
        logger.info("Bot is running with polling mode, multi-user support, image processing, financial status, and streak capabilities...")
        logger.info("💡 To use webhook mode, set WEBHOOK_URL in your .env file")
        
        # Run with polling
        telegram_app.run_polling()

if __name__ == '__main__':
    main()