from datetime import datetime, timezone
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("dotenv not available, using system environment variables")
from openai import OpenAI
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from flask import Flask, request, Response, jsonify
import json
import os
import logging
import base64
import io
import re
import requests
from PIL import Image, ImageFilter, ImageEnhance

try:
    CV2_AVAILABLE = True
    import cv2
    import numpy as np
except ImportError:
    CV2_AVAILABLE = False
    print("OpenCV not available, using PIL for image processing")

try:
    import pytesseract
except ImportError:
    pytesseract = None
    print("pytesseract not available, OCR functionality disabled")

# --- Setup ---
load_dotenv()

# WhatsApp Business API Configuration
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v18.0")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")

# Set up basic logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app for WhatsApp webhooks
app = Flask(__name__)

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
        logger.error(f"Current OPENAI_API_KEY value: {OPENAI_API_KEY}")
        return False

    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI client initialized successfully")
        logger.info(f"OpenAI API key starts with: {OPENAI_API_KEY[:7]}...")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        logger.error(f"API key length: {len(OPENAI_API_KEY) if OPENAI_API_KEY else 0}")
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
                mongo_client = MongoClient(MONGO_URI, **options)
                # Test the connection
                mongo_client.admin.command('ping')
                logger.info(f"MongoDB connected successfully with option {i}")

                db = mongo_client['transactions_db']
                collection = db['entries']
                users_collection = db['users']

                return True
            except Exception as e:
                logger.warning(f"MongoDB connection option {i} failed: {e}")
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

# --- Language Detection ---
def detect_language(text: str) -> str:
    """
    Detect if the text is in Malay or English based on keywords and patterns.
    Returns 'ms' for Malay, 'en' for English.
    """
    if not text:
        return 'en'
    
    text_lower = text.lower().strip()
    
    # Common Malay indicators
    malay_indicators = [
        # Common Malay words
        'beli', 'jual', 'bayar', 'terima', 'hutang', 'tunai', 'kredit',
        'ringgit', 'rm', 'sen', 'kepada', 'daripada', 'untuk', 'dari',
        'dan', 'atau', 'dengan', 'pada', 'di', 'ke', 'dalam', 'oleh',
        'aku', 'saya', 'kami', 'kita', 'dia', 'mereka', 'ini', 'itu',
        'yang', 'adalah', 'ada', 'tidak', 'tak', 'belum', 'sudah', 'akan',
        'makan', 'minum', 'beras', 'ayam', 'ikan', 'sayur', 'buah',
        'kedai', 'pasar', 'restoran', 'warung', 'gerai',
        'hari', 'minggu', 'bulan', 'tahun', 'pagi', 'petang', 'malam',
        'supplier', 'customer', 'pelanggan', 'pembeli', 'penjual',
        # Malay transaction terms
        'untung', 'rugi', 'modal', 'jualan', 'pembelian', 'pendapatan',
        'perbelanjaan', 'kos', 'harga', 'diskaun', 'potongan'
    ]
    
    # Common English indicators
    english_indicators = [
        # Common English words
        'buy', 'sell', 'pay', 'receive', 'debt', 'cash', 'credit',
        'dollar', 'cent', 'price', 'cost', 'total', 'amount',
        'to', 'from', 'for', 'with', 'at', 'in', 'on', 'by',
        'the', 'and', 'or', 'but', 'if', 'then', 'when', 'where',
        'what', 'why', 'how', 'who', 'which', 'this', 'that',
        'have', 'has', 'had', 'will', 'would', 'can', 'could',
        'food', 'drink', 'rice', 'chicken', 'fish', 'vegetable',
        'shop', 'market', 'restaurant', 'store', 'outlet',
        'day', 'week', 'month', 'year', 'morning', 'evening', 'night',
        'supplier', 'customer', 'buyer', 'seller', 'vendor',
        # English transaction terms
        'profit', 'loss', 'capital', 'sales', 'purchase', 'income',
        'expense', 'discount', 'invoice', 'receipt'
    ]
    
    # Count occurrences of language indicators
    malay_count = sum(1 for word in malay_indicators if word in text_lower)
    english_count = sum(1 for word in english_indicators if word in text_lower)
    
    # Additional pattern matching for mixed language detection
    # Check for common Malay sentence patterns
    malay_patterns = [
        r'\b(saya|aku)\s+(beli|jual|bayar)',
        r'\brm\s*\d+',
        r'\bringgit\b',
        r'\bkepada\s+',
        r'\bdaripada\s+',
        r'\btidak\s+(ada|boleh|mahu)',
        r'\bsudah\s+(beli|jual|bayar)',
    ]
    
    # Check for common English sentence patterns  
    english_patterns = [
        r'\bi\s+(buy|sell|pay|bought|sold|paid)',
        r'\$\d+',
        r'\bdollar[s]?\b',
        r'\bto\s+buy\b',
        r'\bfrom\s+\w+',
        r'\bdon\'t\s+',
        r'\bcan\'t\s+',
        r'\bwon\'t\s+',
    ]
    
    # Check patterns
    for pattern in malay_patterns:
        if re.search(pattern, text_lower):
            malay_count += 2  # Give patterns higher weight
    
    for pattern in english_patterns:
        if re.search(pattern, text_lower):
            english_count += 2  # Give patterns higher weight
    
    # Determine language based on counts
    if malay_count > english_count:
        return 'ms'
    elif english_count > malay_count:
        return 'en'
    else:
        # Default to English if unclear
        return 'en'

def get_localized_message(message_key: str, language: str = 'en', **kwargs) -> str:
    """
    Get localized messages for static bot responses.
    
    Args:
        message_key: The key for the message type
        language: 'en' for English, 'ms' for Malay
        **kwargs: Variables to format into the message
    
    Returns:
        Formatted message string in the requested language
    """
    messages = {
        'welcome': {
            'en': """Hi! I'm your financial assistant for WhatsApp. 🤖💰

You can:
📝 Send me a text message describing a transaction
📸 Send me a photo of a receipt to automatically extract transaction details
📊 Use *status* to get your financial health report with actionable advice
📋 Use *summary* to see your recent transactions
🔥 Use *streak* to check your daily logging streak
🔧 Use *test_db* to test database connection

All your data is kept private and separate from other users!
Build your daily logging streak by recording transactions every day! 💪""",
            'ms': """Hai! Saya adalah pembantu kewangan anda untuk WhatsApp. 🤖💰

Anda boleh:
📝 Hantar mesej teks yang menerangkan transaksi
📸 Hantar foto resit untuk ekstrak butiran transaksi secara automatik
📊 Guna *status* untuk laporan kesihatan kewangan dengan nasihat berguna
📋 Guna *summary* untuk lihat transaksi terkini
🔥 Guna *streak* untuk semak streak pencatatan harian
🔧 Guna *test_db* untuk uji sambungan pangkalan data

Semua data anda dijaga secara peribadi dan berasingan dari pengguna lain!
Bina streak pencatatan harian dengan merekod transaksi setiap hari! 💪"""
        },
        'error_parse': {
            'en': "🤖 Sorry, I couldn't understand that. Please try rephrasing.",
            'ms': "🤖 Maaf, saya tidak faham. Sila cuba tulis semula."
        },
        'error_db': {
            'en': "❌ Database connection failed. Please try again later.",
            'ms': "❌ Sambungan pangkalan data gagal. Sila cuba lagi nanti."
        },
        'clarification_items': {
            'en': "🛒 What item did you buy?",
            'ms': "🛒 Barang apa yang anda beli?"
        },
        'clarification_items_sell': {
            'en': "🏪 What item did you sell?",
            'ms': "🏪 Barang apa yang anda jual?"
        },
        'clarification_amount': {
            'en': "💰 What was the amount?",
            'ms': "💰 Berapakah jumlahnya?"
        },
        'clarification_customer_buy': {
            'en': "🏪 Who did you buy from?",
            'ms': "🏪 Anda beli daripada siapa?"
        },
        'clarification_customer_sell': {
            'en': "👤 Who did you sell to?",
            'ms': "👤 Anda jual kepada siapa?"
        },
        'clarification_payment_to': {
            'en': "💸 Who did you pay?",
            'ms': "💸 Anda bayar kepada siapa?"
        },
        'clarification_payment_from': {
            'en': "💰 Who paid you?",
            'ms': "💰 Siapa yang bayar anda?"
        },
        'clarification_prefix': {
            'en': "I need a bit more information to record this transaction:",
            'ms': "Saya perlukan sedikit maklumat tambahan untuk merekod transaksi ini:"
        },
        'clarification_suffix': {
            'en': "Please provide the missing details, and I'll record the transaction for you! 📝",
            'ms': "Sila berikan butiran yang hilang, dan saya akan rekodkan transaksi untuk anda! 📝"
        },
        'transaction_saved': {
            'en': "✅ Transaction recorded successfully!\n\n{summary}",
            'ms': "✅ Transaksi berjaya direkodkan!\n\n{summary}"
        },
        'transaction_error': {
            'en': "❌ Error saving transaction: {error}",
            'ms': "❌ Ralat menyimpan transaksi: {error}"
        }
    }
    
    # Get the message for the specified language, fallback to English
    message_dict = messages.get(message_key, {})
    message = message_dict.get(language, message_dict.get('en', ''))
    
    # Format the message with provided variables
    if kwargs:
        try:
            message = message.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing variable {e} for message key '{message_key}'")
    
    return message

# --- WhatsApp Business API Functions ---
def send_whatsapp_message(to_number: str, message: str) -> bool:
    """Send a WhatsApp message using the Business API."""
    try:
        url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"

        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {
                "body": message
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        logger.info(f"WhatsApp message sent successfully to {to_number}")
        return True

    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {e}")
        return False

def mark_message_as_read(message_id: str) -> bool:
    """Mark a WhatsApp message as read."""
    try:
        url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"

        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        return True

    except Exception as e:
        logger.error(f"Failed to mark message as read: {e}")
        return False

def download_whatsapp_media(media_id: str) -> bytes | None:
    """Download media from WhatsApp."""
    try:
        # First get the media URL
        url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{media_id}"

        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        media_url = response.json().get("url")

        # Download the actual media
        response = requests.get(media_url, headers=headers)
        response.raise_for_status()

        return response.content

    except Exception as e:
        logger.error(f"Failed to download WhatsApp media: {e}")
        return None

# --- Utility Functions ---
def escape_markdown(text):
    """Escape special characters for WhatsApp Markdown."""
    if not text:
        return text

    # WhatsApp supports basic formatting but let's keep it simple
    text = str(text)
    return text

def safe_text(text):
    """Create a safe text by handling null values."""
    if not text:
        return "N/A"

    return str(text)

# --- Conversation State Management ---
# Store pending transactions waiting for clarification
pending_transactions = {}

def store_pending_transaction(wa_id: str, transaction_data: dict, missing_fields: list) -> None:
    """Store a transaction that needs clarification."""
    pending_transactions[wa_id] = {
        'data': transaction_data,
        'missing_fields': missing_fields,
        'timestamp': datetime.now(timezone.utc)
    }
    logger.info(f"Stored pending transaction for wa_id {wa_id}: missing {missing_fields}")

def get_pending_transaction(wa_id: str) -> dict | None:
    """Get pending transaction for a user."""
    return pending_transactions.get(wa_id)

def clear_pending_transaction(wa_id: str) -> None:
    """Clear pending transaction for a user."""
    if wa_id in pending_transactions:
        del pending_transactions[wa_id]
        logger.info(f"Cleared pending transaction for wa_id {wa_id}")

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
def update_user_streak(wa_id: str) -> dict:
    """Update user's daily logging streak and return streak info."""
    global mongo_client, users_collection

    # Check if MongoDB client is available, if not try to reconnect
    if mongo_client is None or users_collection is None:
        logger.warning("MongoDB client not available for user streak, attempting to reconnect...")
        if not connect_to_mongodb():
            logger.error("Failed to connect to MongoDB for user streak.")
            return {"streak": 0, "is_new": False, "updated": False, "error": True}
        
        # Check again after reconnection attempt
        if users_collection is None:
            logger.error("Users collection still not available after reconnection attempt")
            return {"streak": 0, "is_new": False, "updated": False, "error": True}

    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Find user's existing data
        user_data = users_collection.find_one({"wa_id": wa_id})

        if not user_data:
            # New user - start streak at 1
            new_user = {
                "wa_id": wa_id,
                "streak": 1,
                "last_log_date": today
            }
            users_collection.insert_one(new_user)
            logger.info(f"Created new user streak for wa_id {wa_id}")
            return {"streak": 1, "is_new": True, "updated": True}

        last_log_date = user_data.get("last_log_date", "")
        current_streak = user_data.get("streak", 0)

        if not last_log_date:
            # User exists but no last_log_date, treat as new
            users_collection.update_one(
                {"wa_id": wa_id},
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
                {"wa_id": wa_id},
                {"$set": {"streak": new_streak, "last_log_date": today}}
            )
            logger.info(f"Incremented streak for wa_id {wa_id} to {new_streak}")
            return {"streak": new_streak, "is_new": False, "updated": True}
        else:
            # Streak broken, reset to 1
            users_collection.update_one(
                {"wa_id": wa_id},
                {"$set": {"streak": 1, "last_log_date": today}}
            )
            logger.info(f"Reset streak for wa_id {wa_id} (gap of {day_diff} days)")
            return {"streak": 1, "is_new": False, "updated": True, "was_broken": True}

    except Exception as e:
        logger.error(f"Error updating user streak for wa_id {wa_id}: {e}")
        return {"streak": 0, "is_new": False, "updated": False, "error": True}

def get_user_streak(wa_id: str) -> dict:
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
        user_data = users_collection.find_one({"wa_id": wa_id})
        if user_data:
            return {
                "streak": user_data.get("streak", 0),
                "last_log_date": user_data.get("last_log_date", ""),
                "exists": True
            }
        else:
            return {"streak": 0, "last_log_date": "", "exists": False}
    except Exception as e:
        logger.error(f"Error getting user streak for wa_id {wa_id}: {e}")
        return {"streak": 0, "last_log_date": "", "exists": False, "error": True}

# --- Core AI Function ---
def parse_transaction_with_ai(text: str) -> dict:
    logger.info(f"Sending text to OpenAI for parsing: '{text}'")
    
    # Check if OpenAI client is initialized
    if openai_client is None:
        logger.error("OpenAI client not initialized")
        return {"error": "OpenAI client not available"}
    
    # Detect the language of the input text
    user_language = detect_language(text)
    
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

    IMPORTANT LANGUAGE INSTRUCTION:
    The user has written their message in LANGUAGE_TOKEN. You must respond with the 'description' field in the SAME LANGUAGE:
    - If LANGUAGE_TOKEN is "ms" (Malay), provide the description in Bahasa Malaysia
    - If LANGUAGE_TOKEN is "en" (English), provide the description in English
    
    For other fields (action, amount, customer, items, terms), extract them as-is but ensure consistency.

    If a value is not found, use null.
    Return the result ONLY as a JSON object.
    """.replace("LANGUAGE_TOKEN", user_language)
    
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
            
        result = json.loads(result_json)
        
        # Add the detected language to the result for later use
        result['detected_language'] = user_language
        
        return result
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
    if pytesseract is None:
        logger.warning("OCR not available - pytesseract not installed")
        return ""

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
    
    # Detect the language of the receipt text
    user_language = detect_language(extracted_text)
    
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

    IMPORTANT LANGUAGE INSTRUCTION:
    The receipt text appears to be in LANGUAGE_TOKEN. You must provide the 'description' field in the SAME LANGUAGE:
    - If LANGUAGE_TOKEN is "ms" (Malay), provide the description in Bahasa Malaysia
    - If LANGUAGE_TOKEN is "en" (English), provide the description in English

    If a value is not found or unclear, use null.
    For the action field, if you see a receipt from a store/business, it's usually a "purchase".
    If it's an invoice sent to a customer, it's usually a "sale".

    Return the result ONLY as a JSON object.
    """.replace("LANGUAGE_TOKEN", user_language)
    
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
            
        result = json.loads(result_json)
        
        # Add the detected language to the result for later use
        result['detected_language'] = user_language
        
        return result
    except Exception as e:
        logger.error(f"Error calling OpenAI for receipt parsing: {e}")
        return {"error": str(e)}

def generate_ai_response(text: str, wa_id: str) -> str:
    """Generate AI response for general queries in the user's language."""
    logger.info(f"Generating AI response for general query from wa_id {wa_id}: '{text}'")
    
    # Check if OpenAI client is initialized
    if openai_client is None:
        logger.error("OpenAI client not initialized")
        user_language = detect_language(text)
        if user_language == 'ms':
            return "🤖 Maaf, perkhidmatan AI tidak tersedia sekarang. Sila cuba lagi nanti."
        else:
            return "🤖 Sorry, AI service is not available right now. Please try again later."
    
    # Detect the language of the user's query
    user_language = detect_language(text)
    
    # Create appropriate system prompt based on detected language
    if user_language == 'ms':
        system_prompt = """
        Anda adalah pembantu kewangan yang ramah dan membantu untuk aplikasi aliran tunai WhatsApp.
        Pengguna menghantar mesej dalam Bahasa Malaysia, jadi anda MESTI membalas dalam Bahasa Malaysia.
        
        Anda boleh membantu dengan:
        - Soalan umum tentang pengurusan kewangan
        - Nasihat tentang pencatatan transaksi
        - Penjelasan tentang ciri-ciri aplikasi
        - Tips untuk menguruskan perniagaan kecil
        
        Berikan jawapan yang berguna, ringkas, dan ramah. Gunakan emoji yang sesuai.
        Jika pengguna bertanya tentang transaksi tertentu, ingatkan mereka untuk menghantar butiran transaksi tersebut.
        """
    else:
        system_prompt = """
        You are a helpful and friendly financial assistant for a WhatsApp cash flow app.
        The user has written in English, so you MUST respond in English.
        
        You can help with:
        - General questions about financial management
        - Advice about transaction recording
        - Explanations about app features
        - Tips for managing small businesses
        
        Provide helpful, concise, and friendly responses. Use appropriate emojis.
        If the user asks about specific transactions, remind them to send the transaction details.
        """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
        )
        
        ai_response = response.choices[0].message.content
        logger.info(f"Generated AI response: {ai_response}")
        
        if ai_response is None:
            logger.error("OpenAI returned None as response content")
            if user_language == 'ms':
                return "🤖 Maaf, saya tidak dapat menjana respons sekarang. Sila cuba lagi."
            else:
                return "🤖 Sorry, I couldn't generate a response right now. Please try again."
            
        return ai_response
        
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        if user_language == 'ms':
            return "🤖 Maaf, terdapat masalah dengan perkhidmatan AI. Sila cuba lagi nanti."
        else:
            return "🤖 Sorry, there was an issue with the AI service. Please try again later."

def is_transaction_query(text: str) -> bool:
    """
    Determine if the user's message is likely a transaction vs a general question.
    Returns True if it appears to be a transaction, False if it's a general query.
    """
    text_lower = text.lower().strip()
    
    # Transaction indicators (strong signals)
    transaction_indicators = [
        # Malay transaction terms
        'beli', 'jual', 'bayar', 'terima', 'hutang', 'kredit', 'tunai',
        'rm ', 'ringgit', 'sen', 'harga', 'kos', 'jualan', 'pembelian',
        'untung', 'rugi', 'modal', 'pendapatan', 'perbelanjaan',
        # English transaction terms  
        'buy', 'bought', 'sell', 'sold', 'pay', 'paid', 'receive', 'received',
        'cash', 'credit', 'debt', 'price', 'cost', 'sales', 'purchase',
        'profit', 'loss', 'income', 'expense', 'revenue'
    ]
    
    # Amount patterns (strong indicators)
    amount_patterns = [
        r'rm\s*\d+', r'\$\d+', r'\d+\s*(ringgit|dollar)', r'\d+\.\d+',
        r'\d+\s*(rm|usd|myr)', r'(total|amount|harga|kos|price|cost).*\d+'
    ]
    
    # General question indicators (signals it's NOT a transaction)
    question_indicators = [
        # Malay questions
        'apa', 'bagaimana', 'mengapa', 'bila', 'di mana', 'siapa', 'berapa',
        'boleh', 'adakah', 'macam mana', 'kenapa', 'camana',
        # English questions
        'what', 'how', 'why', 'when', 'where', 'who', 'which', 'can',
        'could', 'would', 'should', 'is', 'are', 'do', 'does', 'did'
    ]
    
    # Count transaction indicators
    transaction_count = sum(1 for indicator in transaction_indicators if indicator in text_lower)
    
    # Check amount patterns
    for pattern in amount_patterns:
        if re.search(pattern, text_lower):
            transaction_count += 3  # High weight for amount patterns
    
    # Check question indicators
    question_count = sum(1 for indicator in question_indicators if text_lower.startswith(indicator) or f" {indicator} " in text_lower)
    
    # If it starts with a question word, likely not a transaction
    question_starters = ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'can', 'could', 'would', 'should', 'is', 'are', 'do', 'does', 'did',
                         'apa', 'bagaimana', 'mengapa', 'bila', 'di mana', 'siapa', 'berapa', 'boleh', 'adakah', 'macam mana', 'kenapa', 'camana']
    
    starts_with_question = any(text_lower.startswith(starter) for starter in question_starters)
    
    # Decision logic
    if starts_with_question and transaction_count < 2:
        return False  # Likely a question
    elif transaction_count >= 2:
        return True   # Likely a transaction
    elif question_count > 0 and transaction_count == 0:
        return False  # Likely a question
    else:
        return True   # Default to transaction (current behavior)

# --- Financial Metrics Functions ---
def get_ccc_metrics(wa_id: str) -> dict:
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
            "wa_id": wa_id
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
                dio = (remaining_inventory / total_purchases) * period_days
            else:
                dio = 0

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

        logger.info(f"FIXED CCC calculation for wa_id {wa_id}:")
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
        logger.error(f"Error in FIXED CCC calculation for wa_id {wa_id}: {e}")
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
def save_to_mongodb(data: dict, wa_id: str, image_data: bytes | None = None) -> bool:
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
        # Add user isolation with wa_id
        data['wa_id'] = wa_id

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
        logger.info(f"Successfully inserted data into MongoDB for wa_id {wa_id}: {data.get('action', 'Unknown')} - {data.get('amount', 'N/A')} (ID: {result.inserted_id})")
        return True

    except Exception as e:
        logger.error(f"Error saving to MongoDB: {e}")
        # Try to reconnect for next time
        connect_to_mongodb()
        return False

# --- WhatsApp Message Handlers ---

def handle_start_command(wa_id: str, user_message: str = '') -> str:
    """Handle start command."""
    # Detect language from user's message, default to English
    user_language = detect_language(user_message) if user_message else 'en'
    
    return get_localized_message('welcome', user_language)

def handle_test_db_command(wa_id: str) -> str:
    """Test database connection."""
    try:
        logger.info(f"Manual database test requested by wa_id {wa_id}")

        # Test connection
        if connect_to_mongodb():
            # Check if collection is available before performing queries
            if collection is None:
                return "❌ **Database Connection Failed!**\n\n🚫 Collection not initialized properly."
            
            # Try to perform a simple query
            test_result = collection.find_one({"wa_id": wa_id})
            count = collection.count_documents({"wa_id": wa_id})

            # Format MongoDB URI for display
            mongo_uri_display = "Not configured"
            if MONGO_URI:
                if len(MONGO_URI) > 30:
                    mongo_uri_display = f"{MONGO_URI[:20]}...{MONGO_URI[-10:]}"
                else:
                    mongo_uri_display = MONGO_URI

            reply_text = f"""✅ **Database Connection Test Successful!**

🔗 **Connection Status**: Connected
📊 **Your Records Found**: {count} transactions
🗄️ **Database**: transactions_db
📋 **Collection**: entries
👥 **Users Collection**: Available

**MongoDB URI**: {mongo_uri_display}

The database is working properly! 🎉"""
            return reply_text
        else:
            # Format MongoDB URI for display
            mongo_uri_display = "Not configured"
            if MONGO_URI:
                if len(MONGO_URI) > 30:
                    mongo_uri_display = f"{MONGO_URI[:20]}...{MONGO_URI[-10:]}"
                else:
                    mongo_uri_display = MONGO_URI

            reply_text = f"""❌ **Database Connection Test Failed!**

🔗 **Connection Status**: Failed
📊 **Error**: Cannot connect to MongoDB

**Possible Issues:**
1. Check your IP address is whitelisted in MongoDB Atlas
2. Verify MONGO_URI environment variable is correct
3. Check network connectivity
4. Verify MongoDB cluster is running

**MongoDB URI**: {mongo_uri_display}"""
            return reply_text

    except Exception as e:
        logger.error(f"Error in database test: {e}")
        return f"❌ Database test failed with error: {str(e)}"

def handle_message(wa_id: str, message_body: str) -> str:
    """Handle regular text messages."""
    logger.info(f"Received message from wa_id {wa_id}: '{message_body}'")

    # Detect the language of the user's message
    user_language = detect_language(message_body)

    # Check if user has a pending transaction waiting for clarification
    pending = get_pending_transaction(wa_id)

    if pending:
        # This might be a clarification response
        missing_fields = pending['missing_fields']

        if is_clarification_response(message_body, missing_fields):
            # Process as clarification
            return handle_clarification_response(wa_id, message_body, pending)
        else:
            # User is starting a new transaction, clear the old pending one
            clear_pending_transaction(wa_id)

    # Check for commands
    if message_body.lower().strip() in ['status', '/status']:
        return handle_status_command(wa_id)
    elif message_body.lower().strip() in ['summary', '/summary']:
        return handle_summary_command(wa_id)
    elif message_body.lower().strip() in ['streak', '/streak']:
        return handle_streak_command(wa_id)
    elif message_body.lower().strip() in ['test_db', '/test_db', 'testdb']:
        return handle_test_db_command(wa_id)
    elif message_body.lower().strip() in ['start', '/start', 'help', '/help']:
        return handle_start_command(wa_id, message_body)

    # Determine if this is a transaction or general query
    if not is_transaction_query(message_body):
        # Handle as general query
        return generate_ai_response(message_body, wa_id)

    # Process as new transaction
    parsed_data = parse_transaction_with_ai(message_body)

    if "error" in parsed_data:
        # Log the actual error for debugging
        error_msg = parsed_data.get('error', 'Unknown error')
        logger.error(f"Transaction parsing error for wa_id {wa_id}: {error_msg}")
        
        # Return more specific error message for debugging
        if user_language == 'ms':
            return f"🤖 Maaf, saya tidak faham. Ralat: {error_msg}. Sila cuba tulis semula."
        else:
            return f"🤖 Sorry, I couldn't understand that. Error: {error_msg}. Please try rephrasing."

    # Check for missing critical information and ask for clarification
    missing_fields = []
    clarification_questions = []

    # Check for missing items
    if not parsed_data.get('items') or parsed_data.get('items') in [None, 'null', 'N/A', '']:
        action = parsed_data.get('action') or 'transaction'
        if action == 'purchase':
            clarification_questions.append(get_localized_message('clarification_items', user_language))
        elif action == 'sale':
            clarification_questions.append(get_localized_message('clarification_items_sell', user_language))
        elif action in ['payment_made', 'payment_received']:
            # Payments don't necessarily need items, so skip this check
            pass
        else:
            # Use generic item clarification
            if user_language == 'ms':
                clarification_questions.append("📦 Barang apa yang terlibat dalam transaksi ini?")
            else:
                clarification_questions.append("📦 What item was involved in this transaction?")
        if action not in ['payment_made', 'payment_received']:
            missing_fields.append('items')

    # Check for missing amount
    if not parsed_data.get('amount') or parsed_data.get('amount') in [None, 'null', 0]:
        clarification_questions.append(get_localized_message('clarification_amount', user_language))
        missing_fields.append('amount')

    # Check for missing customer/vendor
    if not parsed_data.get('customer') and not parsed_data.get('vendor'):
        action = parsed_data.get('action') or 'transaction'
        if action == 'purchase':
            clarification_questions.append(get_localized_message('clarification_customer_buy', user_language))
        elif action == 'sale':
            clarification_questions.append(get_localized_message('clarification_customer_sell', user_language))
        elif action == 'payment_made':
            clarification_questions.append(get_localized_message('clarification_payment_to', user_language))
        elif action == 'payment_received':
            clarification_questions.append(get_localized_message('clarification_payment_from', user_language))
        else:
            # Generic clarification
            if user_language == 'ms':
                clarification_questions.append("� Siapa pihak lain dalam transaksi ini?")
            else:
                clarification_questions.append("👥 Who was the other party in this transaction?")
        missing_fields.append('customer/vendor')

    # If there are missing fields, store transaction and ask for clarification
    if clarification_questions:
        # Store the partial transaction
        store_pending_transaction(wa_id, parsed_data, missing_fields)

        # Create clarification message in user's language
        action = parsed_data.get('action') or 'transaction'
        clarification_prefix = get_localized_message('clarification_prefix', user_language)
        clarification_suffix = get_localized_message('clarification_suffix', user_language)
        
        if user_language == 'ms':
            clarification_text = f"🤔 Saya faham ini sebagai *{action}* tetapi saya perlukan penjelasan:\n\n"
        else:
            clarification_text = f"🤔 I understood this as a *{action}* but I need some clarification:\n\n"
            
        clarification_text += "\n".join(clarification_questions)
        clarification_text += f"\n\n{clarification_suffix}"

        return clarification_text

    # Save the complete transaction
    success = save_to_mongodb(parsed_data, wa_id)

    if success:
        # Update user's daily logging streak
        streak_info = update_user_streak(wa_id)

        # Create a user-friendly confirmation message in user's language
        action = (parsed_data.get('action') or 'transaction').capitalize()
        amount = parsed_data.get('amount', 0)
        customer = safe_text(parsed_data.get('customer') or parsed_data.get('vendor', 'N/A'))
        items = safe_text(parsed_data.get('items', 'N/A'))

        if user_language == 'ms':
            reply_text = f"✅ Direkodkan: {action} sebanyak *{amount}* dengan *{customer}*"
            if items and items != 'N/A':
                reply_text += f"\n📦 Barang: {items}"
        else:
            reply_text = f"✅ Logged: {action} of *{amount}* with *{customer}*"
            if items and items != 'N/A':
                reply_text += f"\n📦 Items: {items}"

        # Add streak information if updated
        if streak_info.get('updated', False) and not streak_info.get('error', False):
            streak = streak_info.get('streak', 0)
            if streak_info.get('is_new', False):
                if user_language == 'ms':
                    reply_text += f"\n\n🎯 *Streak pencatatan harian baharu dimulakan!* Streak semasa: *{streak} hari*"
                else:
                    reply_text += f"\n\n🎯 *New daily logging streak started!* Current streak: *{streak} days*"
            elif streak_info.get('was_broken', False):
                if user_language == 'ms':
                    reply_text += f"\n\n🔄 *Streak dimulakan semula!* Streak semasa: *{streak} hari*"
                else:
                    reply_text += f"\n\n🔄 *Streak restarted!* Current streak: *{streak} days*"
            else:
                if user_language == 'ms':
                    reply_text += f"\n\n🔥 *Streak diperpanjang!* Streak semasa: *{streak} hari*"
                else:
                    reply_text += f"\n\n🔥 *Streak extended!* Current streak: *{streak} days*"
        elif not streak_info.get('updated', False) and not streak_info.get('error', False):
            # Already logged today
            streak = streak_info.get('streak', 0)
            if user_language == 'ms':
                day_word = "hari" if streak == 1 else "hari"
                reply_text += f"\n\n🔥 Anda sudah log hari ini! Streak semasa: *{streak} {day_word}*"
            else:
                day_word = "day" if streak == 1 else "days"
                reply_text += f"\n\n🔥 You've already logged today! Current streak: *{streak} {day_word}*"

        return reply_text
    else:
        return get_localized_message('transaction_error', user_language, error="Database error")

def handle_clarification_response(wa_id: str, message_body: str, pending: dict) -> str:
    """Handle user's clarification response to complete the transaction."""
    transaction_data = pending['data'].copy()
    missing_fields = pending['missing_fields']

    logger.info(f"Processing clarification for wa_id {wa_id}: '{message_body}' for fields {missing_fields}")

    # Try to extract missing information from the clarification
    message_lower = message_body.lower()

    # Handle vendor/customer clarification
    if 'customer/vendor' in missing_fields:
        # Extract vendor/customer name from clarification
        vendor_patterns = ['dari', 'from', 'kepada', 'to', 'dengan', 'with']
        extracted_name = message_body.strip()

        # Remove common prepositions
        for pattern in vendor_patterns:
            if extracted_name.lower().startswith(pattern + ' '):
                extracted_name = extracted_name[len(pattern) + 1:]

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
        transaction_data['items'] = message_body.strip()
        missing_fields.remove('items')

    # Handle amount clarification
    if 'amount' in missing_fields and not transaction_data.get('amount'):
        # Try to extract number from the message
        numbers = re.findall(r'\d+(?:\.\d+)?', message_body)
        if numbers:
            transaction_data['amount'] = float(numbers[0])
            missing_fields.remove('amount')

    # Check if we still have missing fields
    if missing_fields:
        # Update pending transaction and ask for remaining info
        store_pending_transaction(wa_id, transaction_data, missing_fields)

        clarification_questions = []
        for field in missing_fields:
            if field == 'items':
                clarification_questions.append("📦 What items were involved?")
            elif field == 'amount':
                clarification_questions.append("💰 What was the amount?")
            elif field == 'customer/vendor':
                clarification_questions.append("👥 Who was the other party?")

        clarification_text = "👍 Got it! I still need:\n\n"
        clarification_text += "\n".join(clarification_questions)

        return clarification_text

    # All fields completed, save the transaction
    clear_pending_transaction(wa_id)
    success = save_to_mongodb(transaction_data, wa_id)

    if success:
        # Update user's daily logging streak
        streak_info = update_user_streak(wa_id)

        action = (transaction_data.get('action') or 'transaction').capitalize()
        amount = transaction_data.get('amount', 0)
        customer = safe_text(transaction_data.get('customer') or transaction_data.get('vendor', 'N/A'))
        items = safe_text(transaction_data.get('items', 'N/A'))

        reply_text = f"✅ *Transaction completed!* {action} of *{amount}* with *{customer}*"
        if items and items != 'N/A':
            reply_text += f"\n📦 Items: {items}"

        # Add streak information if updated
        if streak_info.get('updated', False) and not streak_info.get('error', False):
            streak = streak_info.get('streak', 0)
            if streak_info.get('is_new', False):
                reply_text += f"\n\n🎯 *New daily logging streak started!* Current streak: *{streak} days*"
            elif streak_info.get('was_broken', False):
                reply_text += f"\n\n🔄 *Streak restarted!* Current streak: *{streak} days*"
            else:
                reply_text += f"\n\n🔥 *Streak extended!* Current streak: *{streak} days*"
        elif not streak_info.get('updated', False) and not streak_info.get('error', False):
            # Already logged today
            streak = streak_info.get('streak', 0)
            day_word = "day" if streak == 1 else "days"
            reply_text += f"\n\n🔥 You've already logged today! Current streak: *{streak} {day_word}*"

        return reply_text
    else:
        return "❌ There was an error saving your transaction to the database."

def handle_status_command(wa_id: str) -> str:
    """Send financial health status report."""
    try:
        logger.info(f"Generating status report for wa_id {wa_id}")

        # Get the financial metrics for this specific user
        metrics = get_ccc_metrics(wa_id=wa_id)

        # Generate actionable advice
        advice = generate_actionable_advice(metrics)

        # Create the formatted report
        report = f"""💡 *Your Financial Health Status* (last 90 days)

Your Cash Conversion Cycle is *{metrics['ccc']} days*.
_This is how long your money is tied up in operations before becoming cash again._

*Component Analysis:*
🤝 Days Sales Outstanding (DSO): *{metrics['dso']} days*
   _Time to collect money from credit sales_

📦 Days Inventory Outstanding (DIO): *{metrics['dio']} days*
   _Time inventory sits before being sold_

💸 Days Payable Outstanding (DPO): *{metrics['dpo']} days*
   _Time you take to pay suppliers_

*Formula:* CCC = DSO + DIO - DPO = {metrics['dso']} + {metrics['dio']} - {metrics['dpo']} = *{metrics['ccc']} days*

---
{advice}"""

        return report

    except Exception as e:
        logger.error(f"Error generating status report: {e}")
        return "❌ Sorry, there was an error generating your financial status report."

def handle_summary_command(wa_id: str) -> str:
    """Send a summary of user's transactions."""
    try:
        logger.info(f"Generating summary for wa_id {wa_id}")

        # Check if collection is available before querying
        if collection is None:
            return "❌ Database connection not available. Please try again later."

        # Query only this user's transactions
        user_transactions = list(collection.find({'wa_id': wa_id}).sort('timestamp', -1).limit(10))

        if not user_transactions:
            return "📭 You don't have any transactions recorded yet. Start by sending me a transaction or receipt photo!"

        # Format the summary
        summary_text = f"📊 *Your Recent Transactions Summary*\n\n"
        total_amount = 0

        for i, transaction in enumerate(user_transactions[:5], 1):
            action = transaction.get('action', 'N/A').capitalize()
            amount = transaction.get('amount', 0)
            vendor = safe_text(transaction.get('vendor') or transaction.get('customer', 'N/A'))
            items = safe_text(transaction.get('items', ''))
            date = transaction.get('timestamp', datetime.now()).strftime('%m/%d') if transaction.get('timestamp') else 'N/A'

            # Format the line with items if available
            line = f"{i}. *{action}* - {amount} with {vendor}"
            if items and items != 'N/A':
                line += f"\n   📦 {items}"
            line += f" ({date})\n"

            summary_text += line

            if isinstance(amount, (int, float)):
                total_amount += amount

        summary_text += f"\n💰 *Total Amount*: {total_amount}"
        summary_text += f"\n📝 *Total Transactions*: {len(user_transactions)}"

        if len(user_transactions) > 5:
            summary_text += f"\n\n_Showing latest 5 of {len(user_transactions)} transactions_"

        return summary_text

    except Exception as e:
        logger.error(f"Error generating summary for wa_id {wa_id}: {e}")
        return "❌ Sorry, there was an error generating your transaction summary."

def handle_streak_command(wa_id: str) -> str:
    """Send user's current daily logging streak."""
    try:
        logger.info(f"Getting streak for wa_id {wa_id}")

        streak_info = get_user_streak(wa_id)

        if streak_info.get('exists', False):
            streak = streak_info.get('streak', 0)
            last_log_date = streak_info.get('last_log_date', '')

            # Check if streak is current (logged today or yesterday)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if last_log_date:
                from datetime import datetime as dt
                last_date = dt.strptime(last_log_date, "%Y-%m-%d")
                today_date = dt.strptime(today, "%Y-%m-%d")
                days_diff = (today_date - last_date).days

                if days_diff <= 1:
                    status = "🔥 *Active streak!*"
                else:
                    status = f"⚠️ *Streak paused* ({days_diff} days ago)"
            else:
                status = "📅 *No recent activity*"

            day_word = "day" if streak == 1 else "days"
            reply_text = f"""🔥 *Your Daily Logging Streak*

Current streak: *{streak} {day_word}*
Last logged: {last_log_date if last_log_date else 'Never'}

{status}

Keep logging every day to build up your streak! 📈"""
            return reply_text
        else:
            return """🔥 *Your Daily Logging Streak*

You haven't started logging yet!
Send me your first transaction to begin your streak! 💪"""

    except Exception as e:
        logger.error(f"Error getting streak for wa_id {wa_id}: {e}")
        return "❌ Sorry, there was an error getting your streak information."

def handle_media_message(wa_id: str, media_id: str, media_type: str) -> str:
    """Handle media messages (images/receipts)."""
    try:
        logger.info(f"Processing media from wa_id {wa_id}, type: {media_type}")

        # Send initial processing message
        processing_msg = "📸 Processing your receipt... Please wait."

        # Download the media from WhatsApp
        image_data = download_whatsapp_media(media_id)

        if not image_data:
            return "❌ Sorry, I couldn't download your image. Please try again."

        # Extract text from image
        extracted_text = extract_text_from_image(image_data)

        if not extracted_text:
            return "🤖 Sorry, I couldn't extract text from your receipt. Please send a clearer image or type the transaction manually."

        # Parse the extracted text with AI
        parsed_data = parse_receipt_with_ai(extracted_text)

        if "error" in parsed_data:
            return "🤖 Sorry, I couldn't understand the receipt. Please type the transaction manually."

        # Check for missing critical information in receipt
        missing_fields = []
        clarification_questions = []

        # Check for missing items
        if not parsed_data.get('items') or parsed_data.get('items') in [None, 'null', 'N/A', '']:
            clarification_questions.append("📦 What items were in this receipt?")
            missing_fields.append('items')

        # Check for missing amount
        if not parsed_data.get('amount') or parsed_data.get('amount') in [None, 'null', 0]:
            clarification_questions.append("💰 What was the total amount?")
            missing_fields.append('amount')

        # If there are missing critical fields, ask for clarification
        if clarification_questions:
            # Store the partial transaction
            store_pending_transaction(wa_id, parsed_data, missing_fields)

            clarification_text = "🤔 I found a receipt but need some clarification:\n\n"
            clarification_text += "\n".join(clarification_questions)
            clarification_text += "\n\nPlease provide the missing information!"

            return clarification_text

        # Save to database with image and user isolation
        success = save_to_mongodb(parsed_data, wa_id, image_data)

        if success:
            # Update user's daily logging streak
            streak_info = update_user_streak(wa_id)

            action = (parsed_data.get('action') or 'transaction').capitalize()
            amount = parsed_data.get('amount', 0)
            customer = safe_text(parsed_data.get('customer') or parsed_data.get('vendor', 'N/A'))
            items = safe_text(parsed_data.get('items', 'N/A'))

            reply_text = f"✅ *Receipt processed!* {action} of *{amount}* with *{customer}*"
            if items and items != 'N/A':
                reply_text += f"\n📦 Items: {items}"

            # Add streak information if updated
            if streak_info.get('updated', False) and not streak_info.get('error', False):
                streak = streak_info.get('streak', 0)
                if streak_info.get('is_new', False):
                    reply_text += f"\n\n🎯 *New daily logging streak started!* Current streak: *{streak} days*"
                elif streak_info.get('was_broken', False):
                    reply_text += f"\n\n🔄 *Streak restarted!* Current streak: *{streak} days*"
                else:
                    reply_text += f"\n\n🔥 *Streak extended!* Current streak: *{streak} days*"
            elif not streak_info.get('updated', False) and not streak_info.get('error', False):
                # Already logged today
                streak = streak_info.get('streak', 0)
                day_word = "day" if streak == 1 else "days"
                reply_text += f"\n\n🔥 You've already logged today! Current streak: *{streak} {day_word}*"

            return reply_text
        else:
            return "❌ There was an error saving your receipt to the database."

    except Exception as e:
        logger.error(f"Error processing media: {e}")
        return "❌ Sorry, there was an error processing your receipt. Please try again."

# --- WhatsApp Webhook Routes ---
@app.route('/whatsapp/webhook', methods=['GET'])
def whatsapp_webhook_verify():
    """Verify WhatsApp webhook."""
    # WhatsApp sends a hub.verify_token parameter for verification
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    # Verify the token (you should set this in your environment variables)
    verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN', 'your_verify_token_here')

    if mode == 'subscribe' and token == verify_token and challenge:
        logger.info("WhatsApp webhook verified successfully")
        return challenge
    else:
        logger.warning("WhatsApp webhook verification failed")
        return 'Verification failed', 403

@app.route('/whatsapp/webhook', methods=['POST'])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages."""
    try:
        data = request.get_json()
        logger.info(f"Received WhatsApp webhook: {data}")

        if not data or 'entry' not in data:
            return jsonify({'status': 'ok'})

        for entry in data['entry']:
            for change in entry.get('changes', []):
                if change.get('field') == 'messages':
                    messages = change.get('value', {}).get('messages', [])

                    for message in messages:
                        message_type = message.get('type')
                        wa_id = message.get('from')  # Sender's WhatsApp ID
                        message_id = message.get('id')

                        # Mark message as read
                        mark_message_as_read(message_id)

                        if message_type == 'text':
                            # Handle text messages
                            message_body = message.get('text', {}).get('body', '')
                            response_text = handle_message(wa_id, message_body)

                        elif message_type == 'image':
                            # Handle image messages
                            media_id = message.get('image', {}).get('id')
                            media_type = message.get('image', {}).get('mime_type', 'image/jpeg')
                            response_text = handle_media_message(wa_id, media_id, media_type)

                        else:
                            response_text = "🤖 Sorry, I can only process text messages and images right now."

                        # Send response back to user
                        if response_text:
                            send_whatsapp_message(wa_id, response_text)

        return jsonify({'status': 'ok'})

    except Exception as e:
        logger.error(f"Error in WhatsApp webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint."""
    return "Aliran Tunai WhatsApp Business API Bot is running! 🚀"

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    logger.info("Health check requested")
    try:
        # Test database connection
        if mongo_client:
            mongo_client.admin.command('ping')
            db_status = "✅ Connected"
        else:
            db_status = "❌ Not connected"

        # Test WhatsApp API
        if WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID:
            wa_status = "✅ Configured"
        else:
            wa_status = "❌ Not configured"

        return f"""
🤖 *Aliran Tunai WhatsApp Business API Bot Status*

🗄️ **Database**: {db_status}
📱 **WhatsApp API**: {wa_status}
🌐 **Webhook**: Active
📊 **Environment**: Production

Bot is ready to receive WhatsApp messages! 💪
        """, 200, {'Content-Type': 'text/plain; charset=utf-8'}

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return f"❌ Health check failed: {str(e)}", 500

def main():
    """Start the WhatsApp Business API bot."""
    logger.info("🚀 MAIN FUNCTION STARTED - Initializing WhatsApp Business API Bot...")
    
    # Initialize OpenAI client
    logger.info("🔧 Starting OpenAI client initialization...")
    if not initialize_openai_client():
        logger.error("Failed to initialize OpenAI client. Exiting.")
        return

    # Check WhatsApp configuration
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.error("WhatsApp Business API credentials not configured!")
        logger.error("Please set WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID in your .env file")
        return

    # Try to connect to MongoDB
    try:
        connect_to_mongodb()
        logger.info("✅ MongoDB connection established")
    except Exception as e:
        logger.error(f"⚠️ MongoDB connection failed: {e}")
        logger.warning("Bot will continue without database features")

    logger.info("🚀 Starting Aliran Tunai WhatsApp Business API Bot...")
    logger.info(f"📱 Phone Number ID: {WHATSAPP_PHONE_NUMBER_ID}")
    logger.info("🌐 Webhook endpoint: /whatsapp/webhook")
    logger.info("💻 Health check available at: /health")

    # Start Flask app
    port = int(os.getenv("PORT", "5001"))
    logger.info(f"🌐 Server starting on port {port}")

    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()
