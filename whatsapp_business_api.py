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
import concurrent.futures
import threading
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

# Initialize OpenAI client at module level
logger.info("🤖 Initializing OpenAI client...")
if not initialize_openai_client():
    logger.error("❌ Failed to initialize OpenAI client at startup")
else:
    logger.info("✅ OpenAI client initialized successfully at startup")

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
        },
        'multiple_transactions': {
            'en': """🤖 I detected multiple transactions in your message!

For accuracy, please record **one transaction at a time**:

**Instead of:** "sales rm10 coke, purchase rm50 sugar"

**Please send separately:**
📤 "sales rm10 coke"
📥 "purchase rm50 sugar"

This helps me record each transaction correctly! 📝""",
            'ms': """🤖 Saya kesan beberapa transaksi dalam mesej anda!

Untuk ketepatan, sila rekod **satu transaksi pada satu masa**:

**Bukannya:** "jual rm10 coke, beli rm50 gula"

**Sila hantar berasingan:**
📤 "jual rm10 coke"
📥 "beli rm50 gula"

Ini membantu saya merekod setiap transaksi dengan betul! 📝"""
        },
        'ambiguous_message': {
            'en': """🤖 I'm having trouble understanding your message!

📝 **Please send clear transaction details like:**

**✅ Good examples:**
• "buy rice rm25"
• "sell chicken rm15"  
• "pay supplier rm100"

**❌ Please avoid:**
• Only emojis: "😀🎉💰"
• Random text: "asdfghjkl"
• Unclear messages: "???"

💡 **Tip:** Use simple words with amounts and items for best results!""",
            'ms': """🤖 Saya sukar memahami mesej anda!

📝 **Sila hantar butiran transaksi yang jelas seperti:**

**✅ Contoh yang baik:**
• "beli beras rm25"
• "jual ayam rm15"
• "bayar supplier rm100"

**❌ Sila elakkan:**
• Hanya emoji: "😀🎉💰"
• Teks rawak: "asdfghjkl"  
• Mesej tidak jelas: "???"

💡 **Tip:** Guna perkataan mudah dengan jumlah dan barang untuk hasil terbaik!"""
        },
        'greeting_response': {
            'en': """👋 Hello! I'm your financial assistant bot!

📝 **How to Record Transactions:**

**🛒 Purchases (Buying):**
• "I bought rice 5kg for RM 20"
• "beli ayam RM 15 dari kedai Ah Seng"
• "purchased supplies from ABC Company $50"

**💰 Sales (Selling):**
• "sold nasi lemak RM 5"
• "jual 3 roti canai RM 6"
• "made sale of coffee RM 8"

**💸 Payments:**
• "paid supplier ABC RM 100"
• "bayar hutang kepada vendor XYZ RM 200"
• "received payment from customer RM 150"

**📸 Or just send me a photo of your receipt!**

**⚡ Quick Commands:**
• *status* - Financial health report
• *summary* - Recent transactions
• *streak* - Daily logging streak

Just describe your transaction naturally and I'll understand! 🤖✨""",
            'ms': """👋 Hai! Saya pembantu kewangan bot anda!

📝 **Cara Rekod Transaksi:**

**🛒 Pembelian (Beli):**
• "saya beli beras 5kg RM 20"
• "beli ayam RM 15 dari kedai Ah Seng"
• "beli bekalan dari syarikat ABC RM 50"

**💰 Jualan (Jual):**
• "jual nasi lemak RM 5"
• "jual 3 roti canai RM 6"
• "buat jualan kopi RM 8"

**💸 Bayaran:**
• "bayar pembekal ABC RM 100"
• "bayar hutang kepada vendor XYZ RM 200"
• "terima bayaran dari pelanggan RM 150"

**📸 Atau hantar foto resit sahaja!**

**⚡ Arahan Pantas:**
• *status* - Laporan kesihatan kewangan
• *summary* - Transaksi terkini
• *streak* - Streak pencatatan harian

Terangkan transaksi anda secara semula jadi dan saya akan faham! 🤖✨"""
        },
        'help_response': {
            'en': """🆘 **Need Help?**

**📝 Transaction Recording Examples:**

**For Purchases:** "I bought [item] for [amount]"
• "bought chicken rice RM 8"
• "beli sayur RM 10 dari pasar"

**For Sales:** "I sold [item] for [amount]"  
• "sold coffee RM 5"
• "jual nasi lemak RM 4"

**For Payments:** "I paid [person/company] [amount]"
• "paid supplier ABC RM 100"
• "bayar vendor XYZ RM 50"

**📸 Photo Method:**
Just snap a photo of your receipt and send it to me!

**🔧 Commands:**
• *status* - See your financial health
• *summary* - View recent transactions  
• *streak* - Check daily logging streak
• *help* - Show this help message

**💡 Tips:**
• Include amount and item/service
• Use natural language - I understand both English and Malay
• Be specific about quantities when possible

Ready to track your finances! 💪""",
            'ms': """🆘 **Perlukan Bantuan?**

**📝 Contoh Rekod Transaksi:**

**Untuk Pembelian:** "Saya beli [barang] [harga]"
• "beli nasi ayam RM 8"
• "beli sayur RM 10 dari pasar"

**Untuk Jualan:** "Saya jual [barang] [harga]"
• "jual kopi RM 5"  
• "jual nasi lemak RM 4"

**Untuk Bayaran:** "Saya bayar [orang/syarikat] [jumlah]"
• "bayar pembekal ABC RM 100"
• "bayar vendor XYZ RM 50"

**📸 Kaedah Foto:**
Ambil gambar resit dan hantar kepada saya!

**🔧 Arahan:**
• *status* - Lihat kesihatan kewangan
• *summary* - Lihat transaksi terkini
• *streak* - Semak streak pencatatan harian  
• *help* - Papar mesej bantuan ini

**💡 Tips:**
• Sertakan jumlah dan barang/perkhidmatan
• Guna bahasa biasa - saya faham Bahasa Malaysia dan Inggeris
• Nyatakan kuantiti jika boleh

Sedia untuk jejak kewangan anda! 💪"""
        },
        'registration_welcome': {
            'en': """🎉 Welcome to Aliran Tunai!

Before we start tracking your finances, I need to collect some basic information about your business:

This is a **one-time setup** and helps me provide better insights for your specific business! 📊

Let's begin! ✨""",
            'ms': """🎉 Selamat datang ke Aliran Tunai!

Sebelum kita mula jejak kewangan anda, saya perlu kumpul maklumat asas tentang perniagaan anda:

Ini adalah **persediaan sekali sahaja** dan membantu saya beri pandangan yang lebih baik untuk perniagaan anda! 📊

Mari kita mulakan! ✨"""
        },
        'registration_email': {
            'en': "📧 **Step 1/5:** What is your email address?\n\n*This will be used for important notifications and account recovery.*",
            'ms': "📧 **Langkah 1/5:** Apakah alamat emel anda?\n\n*Ini akan digunakan untuk pemberitahuan penting dan pemulihan akaun.*"
        },
        'registration_owner_name': {
            'en': "👤 **Step 2/5:** What is your name (business owner)?",
            'ms': "👤 **Langkah 2/5:** Siapakah nama anda (pemilik perniagaan)?"
        },
        'registration_company_name': {
            'en': "🏢 **Step 3/5:** What is your company/business name?",
            'ms': "🏢 **Langkah 3/5:** Apakah nama syarikat/perniagaan anda?"
        },
        'registration_location': {
            'en': "📍 **Step 4/5:** Where is your business located? (City/State)",
            'ms': "📍 **Langkah 4/5:** Di manakah lokasi perniagaan anda? (Bandar/Negeri)"
        },
        'registration_business_type': {
            'en': """🏪 **Step 5/5:** What type of business do you run?

**Examples:** Restaurant, Retail Shop, Freelance Service, Trading, Manufacturing, etc.""",
            'ms': """🏪 **Langkah 5/5:** Apakah jenis perniagaan yang anda jalankan?

**Contoh:** Restoran, Kedai Runcit, Perkhidmatan Freelance, Perdagangan, Pembuatan, dll."""
        },
        'personal_registration_name': {
            'en': """👤 *Personal Information*

What's your name?

Example: John Doe""",
            'ms': """👤 *Maklumat Peribadi*

Siapakah nama anda?

Contoh: Ahmad Ali"""
        },
        'registration_complete': {
            'en': """✅ **Registration Complete!**

Welcome aboard, **{owner_name}**! 🎉

Your business profile:
📧 **Email:** {email}
🏢 **Company:** {company_name}
📍 **Location:** {location}  
🏪 **Business Type:** {business_type}

You can now start recording your transactions! Just describe them naturally and I'll help you track your finances. 💰

Type *help* anytime for transaction examples! 📝""",
            'ms': """✅ **Pendaftaran Selesai!**

Selamat datang, **{owner_name}**! 🎉

Profil perniagaan anda:
📧 **Emel:** {email}
🏢 **Syarikat:** {company_name}
📍 **Lokasi:** {location}
🏪 **Jenis Perniagaan:** {business_type}

Anda kini boleh mula merekod transaksi! Huraikan secara semula jadi dan saya akan bantu jejak kewangan anda. 💰

Taip *help* bila-bila masa untuk contoh transaksi! 📝"""
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

# --- User Registration Management ---
# Store pending registrations
pending_registrations = {}

def is_user_registered(wa_id: str) -> bool:
    """Check if user is already registered in the system."""
    global users_collection
    
    if users_collection is None:
        logger.warning("Users collection not available for registration check")
        if not connect_to_mongodb():
            logger.error("Failed to connect to MongoDB for registration check")
            return False
    
    try:
        user_data = users_collection.find_one({"wa_id": wa_id})
        
        if not user_data:
            return False
        
        # Check if user has required fields based on their mode
        user_mode = user_data.get('mode', 'business')  # Default to business for legacy users
        
        if user_mode == 'business':
            # Business users need: email, owner_name, company_name, location, business_type
            required_fields = ['email', 'owner_name', 'company_name', 'location', 'business_type']
            is_registered = all(key in user_data for key in required_fields)
        elif user_mode == 'personal':
            # Personal users need: name, email, monthly_budget
            required_fields = ['name', 'email', 'monthly_budget']
            is_registered = all(key in user_data for key in required_fields)
        else:
            # Unknown mode, assume not registered
            is_registered = False
        
        logger.info(f"Registration check for {wa_id}: mode={user_mode}, registered={is_registered}")
        return is_registered
    except Exception as e:
        logger.error(f"Error checking user registration for wa_id {wa_id}: {e}")
        return False

def get_user_mode(wa_id: str) -> str:
    """Get the user's mode (business or personal)."""
    global users_collection
    
    if users_collection is None:
        if not connect_to_mongodb():
            return 'business'  # Default fallback
    
    try:
        user_data = users_collection.find_one({"wa_id": wa_id})
        return user_data.get('mode', 'business') if user_data else 'business'
    except Exception as e:
        logger.error(f"Error getting user mode for wa_id {wa_id}: {e}")
        return 'business'  # Default fallback

def start_user_registration(wa_id: str, user_language: str) -> str:
    """Start the user registration process with mode selection."""
    # Initialize registration data with mode selection step
    pending_registrations[wa_id] = {
        'step': 0,  # Start with step 0 (mode selection)
        'data': {},
        'language': user_language,
        'timestamp': datetime.now(timezone.utc)
    }
    
    logger.info(f"Started registration process for wa_id {wa_id}")
    
    # Send welcome message and mode selection
    if user_language == 'ms':
        return """🎉 *Selamat datang ke AliranTunai!*

Saya adalah bot yang akan membantu anda mengurus kewangan dengan mudah dan cekap.

📊 *Pilih mod penggunaan:*

Taip *1* untuk *PERNIAGAAN*
- Jejak jualan, pembelian & aliran tunai
- Analisis prestasi perniagaan
- Laporan untuk syarikat

Taip *2* untuk *PERIBADI*  
- Jejak perbelanjaan harian
- Pantau bajet bulanan
- Analisis tabiat berbelanja

Sila pilih: *1* atau *2*"""
    else:
        return """🎉 *Welcome to AliranTunai!*

I'm your financial management bot, here to help you track your money easily and efficiently.

📊 *Choose your usage mode:*

Type *1* for *BUSINESS*
- Track sales, purchases & cash flow
- Business performance analytics  
- Company reports

Type *2* for *PERSONAL*
- Track daily expenses
- Monitor monthly budget
- Spending habit analysis

Please choose: *1* or *2*"""

def handle_registration_step(wa_id: str, message_body: str) -> str:
    """Handle each step of the registration process."""
    if wa_id not in pending_registrations:
        # Registration not started, this shouldn't happen
        return start_user_registration(wa_id, detect_language(message_body))
    
    registration = pending_registrations[wa_id]
    current_step = registration['step']
    user_language = registration['language']
    registration_data = registration['data']
    
    # Process current step response
    if current_step == 0:  # Mode selection
        mode_choice = message_body.strip()
        
        if mode_choice == '1':
            # Business mode
            registration_data['mode'] = 'business'
            registration['step'] = 1
            return get_localized_message('registration_email', user_language)
        elif mode_choice == '2':
            # Personal mode
            registration_data['mode'] = 'personal'
            registration['step'] = 101  # Use different step numbers for personal flow
            return get_localized_message('personal_registration_name', user_language)
        else:
            # Invalid choice
            if user_language == 'ms':
                return "❌ Pilihan tidak sah. Sila pilih *1* untuk Perniagaan atau *2* untuk Peribadi."
            else:
                return "❌ Invalid choice. Please choose *1* for Business or *2* for Personal."
                
    elif current_step == 1:  # Business Email
        email = message_body.strip().lower()
        # Email validation
        if not validate_email(email):
            if user_language == 'ms':
                return "❌ Alamat emel tidak sah. Sila masukkan alamat emel yang betul (contoh: nama@domain.com)"
            else:
                return "❌ Invalid email address. Please enter a valid email (example: name@domain.com)"
        
        registration_data['email'] = email
        registration['step'] = 2
        return get_localized_message('registration_owner_name', user_language)
        
    elif current_step == 2:  # Owner name
        registration_data['owner_name'] = message_body.strip()
        registration['step'] = 3
        return get_localized_message('registration_company_name', user_language)
        
    elif current_step == 3:  # Company name
        registration_data['company_name'] = message_body.strip()
        registration['step'] = 4
        return get_localized_message('registration_location', user_language)
        
    elif current_step == 4:  # Location
        registration_data['location'] = message_body.strip()
        registration['step'] = 5
        return get_localized_message('registration_business_type', user_language)
        
    elif current_step == 5:  # Business type - Final step
        registration_data['business_type'] = message_body.strip()
        
        # Save registration to database
        success = save_user_registration(wa_id, registration_data)
        
        if success:
            # Clear pending registration
            del pending_registrations[wa_id]
            
            # Return completion message
            return get_localized_message('registration_complete', user_language, 
                                       email=registration_data['email'],
                                       owner_name=registration_data['owner_name'],
                                       company_name=registration_data['company_name'],
                                       location=registration_data['location'],
                                       business_type=registration_data['business_type'])
        else:
            # Registration failed, ask them to try again
            if user_language == 'ms':
                return "❌ Maaf, terdapat masalah menyimpan maklumat anda. Sila cuba lagi nanti."
            else:
                return "❌ Sorry, there was an issue saving your information. Please try again later."
    
    # PERSONAL REGISTRATION FLOW (steps 101-103)
    elif current_step == 101:  # Personal Name
        registration_data['name'] = message_body.strip()
        registration['step'] = 102
        if user_language == 'ms':
            return "📧 *Alamat Emel*\n\nSila masukkan alamat emel anda untuk notifikasi dan laporan:\n\nContoh: nama@gmail.com"
        else:
            return "📧 *Email Address*\n\nPlease enter your email address for notifications and reports:\n\nExample: name@gmail.com"
    
    elif current_step == 102:  # Personal Email
        email = message_body.strip().lower()
        # Email validation
        if not validate_email(email):
            if user_language == 'ms':
                return "❌ Alamat emel tidak sah. Sila masukkan alamat emel yang betul (contoh: nama@gmail.com)"
            else:
                return "❌ Invalid email address. Please enter a valid email (example: name@gmail.com)"
        
        registration_data['email'] = email
        registration['step'] = 103
        if user_language == 'ms':
            return "💰 *Bajet Bulanan*\n\nBerapa bajet perbelanjaan bulanan anda? (RM)\n\nContoh: 2000\n\n💡 _Ini akan membantu kami pantau perbelanjaan anda_"
        else:
            return "💰 *Monthly Budget*\n\nWhat's your monthly spending budget? (RM)\n\nExample: 2000\n\n💡 _This helps us track your spending_"
    
    elif current_step == 103:  # Personal Monthly Budget - Final step
        try:
            budget_amount = float(message_body.strip().replace('RM', '').replace(',', ''))
            if budget_amount <= 0:
                raise ValueError("Budget must be positive")
            
            registration_data['monthly_budget'] = budget_amount
            
            # Save personal registration to database
            success = save_personal_registration(wa_id, registration_data)
            
            if success:
                # Clear pending registration
                del pending_registrations[wa_id]
                
                # Return completion message for personal user
                if user_language == 'ms':
                    return f"""✅ *Pendaftaran Berjaya!*

🎉 Selamat datang *{registration_data['name']}*!

📊 *Maklumat Anda:*
• Nama: {registration_data['name']}
• Emel: {registration_data['email']}
• Bajet Bulanan: RM {budget_amount:,.2f}

🚀 *Anda boleh mula menghantar transaksi sekarang!*

Contoh: "makan RM15 nasi lemak" atau "gaji RM3000"

Hantar "help" untuk panduan lengkap."""
                else:
                    return f"""✅ *Registration Successful!*

🎉 Welcome *{registration_data['name']}*!

📊 *Your Information:*
• Name: {registration_data['name']}
• Email: {registration_data['email']}
• Monthly Budget: RM {budget_amount:,.2f}

🚀 *You can start sending transactions now!*

Examples: "food RM15 nasi lemak" or "salary RM3000"

Send "help" for complete guide."""
            else:
                # Registration failed
                if user_language == 'ms':
                    return "❌ Maaf, terdapat masalah menyimpan maklumat anda. Sila cuba lagi nanti."
                else:
                    return "❌ Sorry, there was an issue saving your information. Please try again later."
        
        except (ValueError, TypeError):
            if user_language == 'ms':
                return "❌ Jumlah bajet tidak sah. Sila masukkan nombor yang betul (contoh: 2000)"
            else:
                return "❌ Invalid budget amount. Please enter a valid number (example: 2000)"
    
    # Should not reach here
    return "❌ Registration error occurred."

def save_user_registration(wa_id: str, registration_data: dict) -> bool:
    """Save user registration data to the database."""
    global users_collection
    
    if users_collection is None:
        logger.warning("Users collection not available for saving registration")
        if not connect_to_mongodb():
            logger.error("Failed to connect to MongoDB for saving registration")
            return False
    
    try:
        # Create user document with registration data
        user_doc = {
            "wa_id": wa_id,
            "mode": "business",  # Add mode field
            "email": registration_data['email'],
            "owner_name": registration_data['owner_name'],
            "company_name": registration_data['company_name'], 
            "location": registration_data['location'],
            "business_type": registration_data['business_type'],
            "registered_at": datetime.now(timezone.utc),
            "streak": 0,  # Initialize streak
            "last_log_date": ""  # Initialize last log date
        }
        
        # Use upsert to update existing user or create new one
        result = users_collection.update_one(
            {"wa_id": wa_id},
            {"$set": user_doc},
            upsert=True
        )
        
        logger.info(f"Successfully saved registration for wa_id {wa_id}: {registration_data}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving user registration for wa_id {wa_id}: {e}")
        return False

def save_personal_registration(wa_id: str, registration_data: dict) -> bool:
    """Save personal user registration data to the database."""
    global users_collection
    
    if users_collection is None:
        logger.warning("Users collection not available for saving personal registration")
        if not connect_to_mongodb():
            logger.error("Failed to connect to MongoDB for saving personal registration")
            return False
    
    try:
        # Create user document with personal registration data
        user_doc = {
            "wa_id": wa_id,
            "mode": "personal",  # Add mode field
            "name": registration_data['name'],
            "email": registration_data['email'],
            "monthly_budget": registration_data['monthly_budget'],
            "registered_at": datetime.now(timezone.utc),
            "streak": 0,  # Initialize streak
            "last_log_date": "",  # Initialize last log date
            "current_month_spending": 0.0,  # Track monthly spending
            "budget_notifications_enabled": True  # Enable budget notifications by default
        }
        
        # Use upsert to update existing user or create new one
        result = users_collection.update_one(
            {"wa_id": wa_id},
            {"$set": user_doc},
            upsert=True
        )
        
        if result.upserted_id or result.modified_count > 0:
            logger.info(f"Personal registration saved successfully for wa_id {wa_id}")
            logger.info(f"User doc: {user_doc}")
            return True
        else:
            logger.error(f"No changes made during personal registration save for wa_id {wa_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error saving personal registration for wa_id {wa_id}: {e}")
        return False

def is_in_registration_process(wa_id: str) -> bool:
    """Check if user is currently in the registration process."""
    return wa_id in pending_registrations

def validate_email(email: str) -> bool:
    """Validate email format using basic regex pattern."""
    import re
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_registration_data_parallel(registration_data: dict) -> dict:
    """Validate all registration fields in parallel."""
    
    def validate_email_field():
        email = registration_data.get('email', '')
        return {
            'field': 'email',
            'valid': validate_email(email),
            'message': 'Valid email' if validate_email(email) else 'Invalid email format'
        }
    
    def validate_name_field():
        name = registration_data.get('owner_name', '').strip()
        valid = len(name) >= 2 and name.replace(' ', '').isalpha()
        return {
            'field': 'owner_name',
            'valid': valid,
            'message': 'Valid name' if valid else 'Name must be at least 2 characters and contain only letters'
        }
    
    def validate_company_field():
        company = registration_data.get('company_name', '').strip()
        valid = len(company) >= 2
        return {
            'field': 'company_name',
            'valid': valid,
            'message': 'Valid company name' if valid else 'Company name must be at least 2 characters'
        }
    
    def validate_location_field():
        location = registration_data.get('location', '').strip()
        valid = len(location) >= 2
        return {
            'field': 'location',
            'valid': valid,
            'message': 'Valid location' if valid else 'Location must be at least 2 characters'
        }
    
    def validate_business_type_field():
        business_type = registration_data.get('business_type', '').strip()
        valid = len(business_type) >= 2
        return {
            'field': 'business_type',
            'valid': valid,
            'message': 'Valid business type' if valid else 'Business type must be at least 2 characters'
        }
    
    # Run all validations in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(validate_email_field),
            executor.submit(validate_name_field),
            executor.submit(validate_company_field),
            executor.submit(validate_location_field),
            executor.submit(validate_business_type_field)
        ]
        
        # Collect results
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                logger.error(f"Error in parallel validation: {e}")
        
        # Analyze results
        validation_result = {
            'all_valid': all(r['valid'] for r in results),
            'field_results': {r['field']: r for r in results},
            'errors': [r['message'] for r in results if not r['valid']]
        }
        
        return validation_result

# --- Fast Regex Parser ---
def parse_transaction_with_regex(text: str) -> dict | None:
    """Fast regex-based parsing for common transaction patterns."""
    import re
    
    text_clean = text.lower().strip()
    user_language = detect_language(text)
    
    # Common patterns (English and Malay)
    patterns = [
        # Buy patterns: "beli X rm Y", "buy X rm Y", "bought X $Y"
        {
            'pattern': r'(?:beli|buy|bought)\s+(.+?)\s+(?:rm|usd?|\$)\s*(\d+(?:\.\d{2})?)',
            'action': 'purchase'
        },
        # Sell patterns: "jual X rm Y", "sell X rm Y", "sold X $Y" 
        {
            'pattern': r'(?:jual|sell|sold)\s+(.+?)\s+(?:rm|usd?|\$)\s*(\d+(?:\.\d{2})?)',
            'action': 'sale'
        },
        # Pay patterns: "bayar X rm Y", "pay X rm Y", "paid X $Y"
        {
            'pattern': r'(?:bayar|pay|paid)\s+(.+?)\s+(?:rm|usd?|\$)\s*(\d+(?:\.\d{2})?)',
            'action': 'payment_made'
        },
        # Receive payment: "terima bayaran rm Y", "received payment $Y"
        {
            'pattern': r'(?:terima\s+bayaran|received?\s+payment)\s+(?:dari\s+)?(.+?)\s+(?:rm|usd?|\$)\s*(\d+(?:\.\d{2})?)',
            'action': 'payment_received'
        },
        # Simple amount first: "rm Y untuk X", "$Y for X"
        {
            'pattern': r'(?:rm|usd?|\$)\s*(\d+(?:\.\d{2})?)\s+(?:untuk|for)\s+(.+)',
            'action': 'purchase',
            'reverse_order': True
        }
    ]
    
    for pattern_config in patterns:
        pattern = pattern_config['pattern']
        match = re.search(pattern, text_clean, re.IGNORECASE)
        
        if match:
            if pattern_config.get('reverse_order'):
                amount_str = match.group(1)
                items = match.group(2).strip()
            else:
                items = match.group(1).strip()
                amount_str = match.group(2)
            
            # Extract amount
            try:
                amount = float(amount_str)
            except:
                continue
                
            # Clean up items
            items = re.sub(r'\b(?:dari|from|kepada|to|dengan|with)\b', '', items).strip()
            
            # Create transaction dict
            result = {
                'action': pattern_config['action'],
                'amount': amount,
                'items': items,
                'customer': None,
                'vendor': None, 
                'terms': None,
                'category': None,
                'detected_language': user_language,
                'parsed_by': 'regex'
            }
            
            # Generate description based on language
            if user_language == 'ms':
                if pattern_config['action'] == 'purchase':
                    result['description'] = f"Beli {items} RM{amount}"
                elif pattern_config['action'] == 'sale':  
                    result['description'] = f"Jual {items} RM{amount}"
                else:
                    result['description'] = f"Bayar {items} RM{amount}"
            else:
                action_text = {
                    'purchase': 'Bought',
                    'sale': 'Sold', 
                    'payment_made': 'Paid',
                    'payment_received': 'Received payment'
                }
                result['description'] = f"{action_text[pattern_config['action']]} {items} ${amount}"
            
            return {'success': True, 'data': result}
    
    return {'success': False, 'data': None}

# --- Core AI Function ---
def parse_transaction_with_ai(text: str) -> dict:
    logger.info(f"Sending text to OpenAI for parsing and categorization: '{text}'")
    
    # Check if OpenAI client is initialized
    if openai_client is None:
        logger.error("OpenAI client not initialized")
        return {"error": "OpenAI client not available"}
    
    # Detect the language of the input text
    user_language = detect_language(text)
    
    system_prompt = f"""Extract transaction details from user message.
Required fields: action, amount, items, customer/vendor, terms, description, category.

Actions: "sale", "purchase", "payment_received", "payment_made"
Categories (purchases only): OPEX, CAPEX, COGS, INVENTORY, MARKETING, UTILITIES, OTHER
Language: {user_language} (match description language)

Return JSON only."""
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-5-nano",
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

def categorize_purchase_with_ai(description, vendor=None, amount=None):
    """Use OpenAI to categorize a purchase transaction."""
    if not OPENAI_API_KEY or openai_client is None:
        logger.warning("OpenAI not configured, returning default category")
        return "OTHER"
    
    try:
        # Create a shortened prompt for categorization
        prompt = f"""Categorize: {description} (${amount or 'N/A'})
Categories: OPEX, CAPEX, COGS, INVENTORY, MARKETING, UTILITIES, OTHER
Return code only:"""
        
        response = openai_client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": "Categorize expenses. Return code only."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=50,
            temperature=0.1
        )
        
        category = response.choices[0].message.content.strip().upper()
        
        # Validate that the returned category is one of our expected categories
        valid_categories = ['OPEX', 'CAPEX', 'COGS', 'INVENTORY', 'MARKETING', 'UTILITIES', 'OTHER']
        if category in valid_categories:
            logger.info(f"AI categorized transaction as: {category}")
            return category
        else:
            logger.warning(f"AI returned invalid category: {category}, defaulting to OTHER")
            return "OTHER"
            
    except Exception as e:
        logger.error(f"Error calling OpenAI API for categorization: {e}")
        return "OTHER"

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
    """Extract text from image using GPT Vision."""
    if openai_client is None:
        logger.warning("OpenAI Vision not available - client not initialized")
        return ""

    try:
        # Convert image bytes to base64
        import base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        logger.info("Using GPT Vision to extract text from image...")
        
        response = openai_client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please extract all the text from this receipt/document image. Return only the extracted text without any additional commentary."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_completion_tokens=1000
        )
        
        extracted_text = response.choices[0].message.content
        if extracted_text:
            extracted_text = extracted_text.strip()
            logger.info(f"GPT Vision extracted text: {extracted_text[:200]}...")
            return extracted_text
        else:
            logger.warning("GPT Vision returned no text")
            return ""
        
    except Exception as e:
        logger.error(f"Error extracting text from image using GPT Vision: {e}")
        return ""

def parse_receipt_with_vision(image_bytes: bytes) -> dict:
    """Parse receipt image directly using GPT Vision to extract transaction details."""
    if openai_client is None:
        logger.warning("OpenAI Vision not available - client not initialized")
        return {"error": "OpenAI Vision not available"}

    try:
        # Convert image bytes to base64
        import base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        logger.info("Using GPT Vision to parse receipt directly...")
        
        # Set default language
        user_language = "english"
        
        system_prompt = f"""
        You are an expert at analyzing receipt and invoice images. Extract transaction details AND categorize purchases directly from the receipt image.
        Extract the following fields: 'action', 'amount' (as a number), 'customer' (or 'vendor'), 'items' (what was bought/sold),
        'terms' (e.g., 'credit', 'cash', 'hutang'), 'description', and 'category'.

        The 'action' field MUST BE one of the following exact values: "sale", "purchase", "payment_received", or "payment_made".

        Action guidelines:
        - "sale": Selling goods/services to customers  
        - "purchase": Buying goods/services from suppliers
        - "payment_received": Receiving money from customers (collections)
        - "payment_made": Paying money to suppliers or for expenses

        Pay special attention to ITEMS - extract all the products/services listed on the receipt:
        - "nasi lemak" → items: "nasi lemak"
        - "Coca Cola 2 bottles" → items: "Coca Cola (2 bottles)"
        - Multiple items should be listed clearly

        For the action field, if you see a receipt from a store/business, it's usually a "purchase".

        CATEGORY field (ONLY for purchases/expenses):
        If action is "purchase" or "payment_made", categorize into one of these business expense categories:
        - OPEX: Operating expenses (utilities, rent, marketing, office supplies, services, staff costs)
        - CAPEX: Capital expenses (equipment, machinery, property, vehicles, long-term assets)
        - COGS: Cost of goods sold (raw materials, inventory for resale, direct production costs)
        - INVENTORY: Inventory purchases (stock for resale, finished goods)
        - MARKETING: Marketing and advertising expenses
        - UTILITIES: Utilities and overhead costs (electricity, water, internet, phone)
        - OTHER: Miscellaneous or unclear expenses
        
        For sales or payment_received, set category to null.
        
        If a value is not found, use null.
        Return the result ONLY as a JSON object.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {
                    "role": "system", 
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please analyze this receipt image and extract the transaction details as JSON."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=500
        )
        
        result_json = response.choices[0].message.content
        if result_json:
            logger.info(f"GPT Vision parsed receipt: {result_json}")
            result = json.loads(result_json)
            result['detected_language'] = user_language
            return result
        else:
            logger.error("GPT Vision returned no response")
            return {"error": "No response from GPT Vision"}
            
    except Exception as e:
        logger.error(f"Error parsing receipt with GPT Vision: {e}")
        return {"error": str(e)}

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
    You are an expert at parsing receipts and invoices. Extract transaction details AND categorize purchases from the receipt text provided.

    Extract the following fields:
    - 'action': Determine if this is a "sale", "purchase", "payment_received", or "payment_made" based on context
    - 'amount': The total amount (as a number, extract from total, grand total, etc.)
    - 'customer': Customer name if this is a sale, or store/vendor name if this is a purchase
    - 'vendor': Store/business name (for purchases) or customer name (for sales)
    - 'terms': Payment method if available (e.g., 'cash', 'credit', 'card')
    - 'items': List or description of items purchased (this is VERY important - extract all items with quantities/descriptions)
    - 'description': Brief description of the transaction
    - 'category': Business expense category (see below)
    - 'date': Transaction date if available

    Pay special attention to ITEMS - extract all the products/services listed on the receipt:
    - Look for item names, product descriptions, services
    - Include quantities, sizes, or other specifications
    - Examples: "Nasi Lemak (2x)", "Beras 5kg", "Coffee Large", "Roti Canai (3 pcs)"

    CATEGORY field (ONLY for purchases/expenses):
    If action is "purchase" or "payment_made", categorize into one of these business expense categories:
    - OPEX: Operating expenses (utilities, rent, marketing, office supplies, services, staff costs)
    - CAPEX: Capital expenses (equipment, machinery, property, vehicles, long-term assets)
    - COGS: Cost of goods sold (raw materials, inventory for resale, direct production costs)
    - INVENTORY: Inventory purchases (stock for resale, finished goods)
    - MARKETING: Marketing and advertising expenses
    - UTILITIES: Utilities and overhead costs (electricity, water, internet, phone)
    - OTHER: Miscellaneous or unclear expenses
    
    For sales or payment_received, set category to null.

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
            model="gpt-5-nano",
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
            model="gpt-5-nano",
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

def is_greeting_or_help(text: str) -> str | None:
    """
    Detect if the message is a greeting or help request.
    Returns 'greeting' for greetings, 'help' for help requests, None otherwise.
    """
    text_lower = text.lower().strip()
    
    # Greeting indicators (English and Malay)
    greeting_patterns = [
        # English greetings
        'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
        'good day', 'greetings', 'what\'s up', 'how are you', 'howdy',
        # English gratitude/thanks
        'thank you', 'thanks', 'thank u', 'thx', 'ty', 'much appreciated',
        'appreciate it', 'cheers', 'nice', 'awesome', 'great', 'perfect',
        'excellent', 'wonderful', 'brilliant', 'good job', 'well done',
        # Malay greetings  
        'hai', 'helo', 'selamat pagi', 'selamat petang', 'selamat malam',
        'selamat tengahari', 'apa khabar', 'hello',
        # Malay gratitude/thanks
        'terima kasih', 'tq', 'tenkiu', 'thank you', 'thanks', 'bagus',
        'hebat', 'mantap', 'terbaik', 'syabas', 'tahniah', 'baik',
        'ok', 'okay', 'okey', 'fine', 'good', 'nice',
        # Common variations
        'hii', 'hiii', 'hiiii', 'helo', 'hallo'
    ]
    
    # Help request indicators (English and Malay)
    help_patterns = [
        # English help requests
        'help', 'how to', 'how do i', 'guide', 'tutorial', 'instructions',
        'what can you do', 'what do you do', 'how does this work',
        'how to use', 'how to record', 'how to save', 'how to track',
        'i need help', 'can you help', 'assist me', 'guidance',
        # Malay help requests
        'tolong', 'bantuan', 'macam mana', 'camana', 'bagaimana',
        'panduan', 'cara guna', 'cara rekod', 'cara simpan', 'cara jejak',
        'saya perlukan bantuan', 'boleh tolong', 'bantu saya', 'pandu saya',
        'nak tahu', 'want to know', 'perlu bantuan'
    ]
    
    # Check for exact matches or starts with
    for greeting in greeting_patterns:
        if text_lower == greeting or text_lower.startswith(greeting):
            return 'greeting'
    
    # Check for help patterns (can be anywhere in the text)
    for help_pattern in help_patterns:
        if help_pattern in text_lower:
            return 'help'
    
    # Check for question marks + short messages (likely help requests)
    if '?' in text and len(text.split()) <= 5:
        return 'help'
        
    return None

def is_ambiguous_message(text: str) -> bool:
    """
    Detect if the message is ambiguous, contains mostly emojis, gibberish, or random text.
    Returns True if the message should be flagged as ambiguous.
    """
    if not text or len(text.strip()) == 0:
        return True
        
    text_stripped = text.strip()
    
    # Count different types of characters
    emoji_count = 0
    letter_count = 0
    gibberish_chars = 0
    total_chars = len(text_stripped)
    
    # Check for emojis and various character types
    for char in text_stripped:
        # Check for emojis (basic Unicode ranges)
        if ord(char) > 127:  # Non-ASCII characters (including emojis)
            if (0x1F600 <= ord(char) <= 0x1F64F or  # Emoticons
                0x1F300 <= ord(char) <= 0x1F5FF or  # Misc Symbols
                0x1F680 <= ord(char) <= 0x1F6FF or  # Transport
                0x1F700 <= ord(char) <= 0x1F77F or  # Alchemical
                0x2600 <= ord(char) <= 0x26FF or    # Misc symbols
                0x2700 <= ord(char) <= 0x27BF):     # Dingbats
                emoji_count += 1
        elif char.isalpha():
            letter_count += 1
        elif not char.isspace() and not char.isdigit() and char not in '.,!?-()[]{}':
            gibberish_chars += 1
    
    # Rules for detecting ambiguous messages
    
    # 1. Too many emojis (more than 50% of message)
    if total_chars > 0 and emoji_count / total_chars > 0.5:
        return True
    
    # 2. Message is mostly symbols/gibberish
    if total_chars > 0 and gibberish_chars / total_chars > 0.4:
        return True
        
    # 3. Very short messages with no meaningful content
    if total_chars <= 3 and letter_count == 0:
        return True
    
    # 4. Check for random key mashing patterns
    words = text_stripped.lower().split()
    gibberish_words = 0
    
    for word in words:
        # Skip very short words, numbers, and common expressions
        if len(word) <= 2 or word.isdigit():
            continue
            
        # Check for patterns that suggest gibberish
        # Consecutive identical characters (like "aaaa", "jjjj")
        if len(set(word)) <= 2 and len(word) > 3:
            gibberish_words += 1
            continue
            
        # Random keyboard patterns
        keyboard_patterns = ['asdf', 'qwer', 'zxcv', 'hjkl', 'fghj', 'yuio']
        if any(pattern in word for pattern in keyboard_patterns) and len(word) > 4:
            gibberish_words += 1
            continue
            
        # Check consonant-to-vowel ratio (gibberish often has too many consonants)
        vowels = 'aeiou'
        consonants = 'bcdfghjklmnpqrstvwxyz'
        vowel_count = sum(1 for c in word if c in vowels)
        consonant_count = sum(1 for c in word if c in consonants)
        
        if len(word) > 4 and consonant_count > 0 and vowel_count / max(consonant_count, 1) < 0.2:
            gibberish_words += 1
    
    # 5. Too many gibberish words
    if len(words) > 0 and gibberish_words / len(words) > 0.6:
        return True
        
    return False

def detect_multiple_transactions(text: str) -> bool:
    """
    Detect if the message contains multiple transactions.
    Returns True if multiple transactions are detected.
    """
    text_lower = text.lower().strip()
    
    # Transaction action keywords
    transaction_actions = [
        # English actions
        'buy', 'bought', 'sell', 'sold', 'sale', 'purchase', 'pay', 'paid', 'payment',
        # Malay actions
        'beli', 'jual', 'jualan', 'bayar', 'pembayaran', 'pembelian'
    ]
    
    # Count how many transaction actions appear in the text
    action_count = 0
    found_actions = []
    
    for action in transaction_actions:
        if action in text_lower:
            action_count += text_lower.count(action)
            if text_lower.count(action) > 0:
                found_actions.append(action)
    
    # If we find multiple different actions, likely multiple transactions
    if len(found_actions) > 1:
        return True
    
    # Check for conjunction patterns that suggest multiple transactions
    multiple_patterns = [
        # English conjunctions
        r'\band\s+(then\s+)?(buy|sell|pay|purchase)',
        r'(buy|sell|pay|purchase).+\sand\s+(buy|sell|pay|purchase)',
        r'(buy|sell|pay|purchase).+[,;]\s*(buy|sell|pay|purchase)',
        r'also\s+(buy|sell|pay|purchase)',
        r'then\s+(buy|sell|pay|purchase)',
        # Malay conjunctions  
        r'\bdan\s+(kemudian\s+)?(beli|jual|bayar)',
        r'(beli|jual|bayar).+\bdan\s+(beli|jual|bayar)',
        r'(beli|jual|bayar).+[,;]\s*(beli|jual|bayar)',
        r'juga\s+(beli|jual|bayar)',
        r'kemudian\s+(beli|jual|bayar)',
        r'lepas\s+tu\s+(beli|jual|bayar)',
        # Mixed patterns
        r'(sale|sales).+[,;]\s*(purchase|buy)',
        r'(purchase|buy).+[,;]\s*(sale|sell)',
    ]
    
    for pattern in multiple_patterns:
        if re.search(pattern, text_lower):
            return True
    
    # Check for multiple amounts (strong indicator of multiple transactions)
    amount_patterns = [
        r'rm\s*\d+',
        r'\$\d+',
        r'\d+\s*(ringgit|dollar)',
        r'\d+\.\d+',
    ]
    
    total_amounts = 0
    for pattern in amount_patterns:
        matches = re.findall(pattern, text_lower)
        total_amounts += len(matches)
    
    # If we have multiple amounts and multiple actions, likely multiple transactions
    if total_amounts > 1 and action_count > 1:
        return True
    
    return False

def is_transaction_query(text: str) -> bool:
    """
    Determine if the user's message is likely a transaction vs a general question.
    Returns True if it appears to be a transaction, False if it's a general query.
    """
    text_lower = text.lower().strip()
    
    # First check if it's a greeting or thanks - definitely not a transaction
    if is_greeting_or_help(text):
        return False
    
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

        # Enhanced transaction breakdown with null safety
        transaction_breakdown_list = []
        action_summary = {}
        for transaction in transactions:
            action = transaction.get('action') or 'unknown'
            if action not in action_summary:
                action_summary[action] = {'count': 0, 'total_amount': 0}
            action_summary[action]['count'] += 1
            action_summary[action]['total_amount'] += transaction.get('amount', 0)

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
            action = item.get('_id') or 'Unknown'
            count = item.get('count', 0)
            # Handle case where action might be None
            action_text = action.capitalize() if action and action != 'Unknown' else 'Unknown'
            breakdown_summary += f"• {action_text}: {count} transactions\n"

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
def save_to_mongodb_parallel(data: dict, wa_id: str, image_data: bytes | None = None) -> bool:
    """Saves transaction data with parallel database operations for better performance."""
    global mongo_client, collection

    if "error" in data:
        logger.error(f"Cannot save transaction with error: {data['error']}")
        return False

    # Check if MongoDB client is available, if not try to reconnect
    if mongo_client is None or collection is None:
        logger.warning("MongoDB client not available for saving, attempting to reconnect...")
        if not connect_to_mongodb():
            logger.error("Failed to connect to MongoDB for saving")
            return False

    try:
        # Prepare transaction document
        transaction_doc = {
            "wa_id": wa_id,
            "action": data.get('action'),
            "amount": data.get('amount'),
            "customer": data.get('customer') or data.get('vendor'),
            "vendor": data.get('vendor') or data.get('customer'),
            "items": data.get('items'),
            "terms": data.get('terms'),
            "description": data.get('description'),
            "category": data.get('category'),
            "detected_language": data.get('detected_language', 'en'),
            "timestamp": datetime.now(timezone.utc),
            "date_created": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "time_created": datetime.now(timezone.utc).strftime("%H:%M:%S")
        }

        # Handle category logic
        if data.get('action') in ['purchase', 'payment_made'] and not data.get('category'):
            # Fallback categorization if needed
            try:
                description = data.get('description', '') or data.get('items', '')
                vendor = data.get('vendor', '') or data.get('customer', '')
                amount = data.get('amount', 0)
                
                if description:
                    category = categorize_purchase_with_ai(description, vendor, amount)
                    transaction_doc['category'] = category
                    logger.info(f"Fallback categorization: {category}")
                else:
                    transaction_doc['category'] = 'OTHER'
            except Exception as e:
                logger.error(f"Error in fallback categorization: {e}")
                transaction_doc['category'] = 'OTHER'
        elif data.get('category'):
            logger.info(f"Using AI-provided category: {data.get('category')}")
        
        # Ensure non-purchase transactions don't have categories
        if data.get('action') in ['sale', 'payment_received'] and transaction_doc.get('category'):
            transaction_doc['category'] = None

        # Add image data if provided
        if image_data:
            import base64
            transaction_doc['receipt_image'] = base64.b64encode(image_data).decode('utf-8')

        # Define parallel operations
        def save_transaction():
            """Save the transaction to MongoDB"""
            try:
                result = collection.insert_one(transaction_doc)
                logger.info(f"Transaction saved with ID: {result.inserted_id}")
                return True
            except Exception as e:
                logger.error(f"Error saving transaction: {e}")
                return False

        def update_streak():
            """Update user's daily logging streak"""
            try:
                streak_result = update_user_streak(wa_id)
                return streak_result
            except Exception as e:
                logger.error(f"Error updating user streak: {e}")
                return {"streak": 0, "updated": False, "error": True}

        def log_activity():
            """Log user activity for analytics"""
            try:
                activity_doc = {
                    "wa_id": wa_id,
                    "activity_type": "transaction_logged",
                    "action": data.get('action'),
                    "amount": data.get('amount'),
                    "timestamp": datetime.now(timezone.utc)
                }
                
                # Try to save to activity collection if it exists
                if hasattr(db, 'activity'):
                    db.activity.insert_one(activity_doc)
                    logger.info("Activity logged successfully")
                return True
            except Exception as e:
                logger.error(f"Error logging activity: {e}")
                return False

        # Execute operations in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all operations simultaneously
            future_save = executor.submit(save_transaction)
            future_streak = executor.submit(update_streak)
            future_activity = executor.submit(log_activity)
            
            # Wait for critical operation (save transaction) to complete
            save_success = future_save.result()
            
            # Get other results (these are less critical)
            try:
                streak_result = future_streak.result()
                activity_result = future_activity.result()
                logger.info(f"Parallel operations completed - Streak: {streak_result.get('updated', False)}, Activity: {activity_result}")
            except Exception as e:
                logger.error(f"Error in non-critical parallel operations: {e}")
            
            return save_success

    except Exception as e:
        logger.error(f"Error in parallel save operation: {e}")
        return False

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

        # Handle category for purchases (now included in AI response)
        if data.get('action') in ['purchase', 'payment_made'] and not data.get('category'):
            # If category wasn't provided by AI, use fallback categorization
            try:
                description = data.get('description', '') or data.get('items', '')
                vendor = data.get('vendor', '') or data.get('customer', '')
                amount = data.get('amount', 0)
                
                if description:  # Only categorize if we have a description
                    category = categorize_purchase_with_ai(description, vendor, amount)
                    data['category'] = category
                    logger.info(f"Fallback categorization for purchase: {category}")
                else:
                    data['category'] = 'OTHER'
                    logger.info("No description available for purchase, defaulting to OTHER category")
            except Exception as e:
                logger.error(f"Error in fallback categorization: {e}")
                data['category'] = 'OTHER'
        elif data.get('category'):
            logger.info(f"Using AI-provided category: {data.get('category')}")
        
        # Ensure non-purchase transactions don't have categories
        if data.get('action') in ['sale', 'payment_received'] and data.get('category'):
            data['category'] = None

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
    logger.info(f"DEBUG: handle_message() function called")

    # Detect the language of the user's message
    user_language = detect_language(message_body)

    # PRIORITY 1: Check if user is in registration process
    if is_in_registration_process(wa_id):
        return handle_registration_step(wa_id, message_body)
    
    # PRIORITY 2: Check if user needs to register (first-time user)
    if not is_user_registered(wa_id):
        return start_user_registration(wa_id, user_language)

    # Check for greetings/thanks first, even if there's a pending transaction
    greeting_type = is_greeting_or_help(message_body)
    logger.info(f"Greeting detection for '{message_body}': {greeting_type}")
    if greeting_type:
        logger.info(f"Processing as {greeting_type}, clearing any pending transactions")
        # If there's a pending transaction and user says thanks/greeting, assume they're done
        if get_pending_transaction(wa_id):
            clear_pending_transaction(wa_id)
        
        if greeting_type == 'greeting':
            return get_localized_message('greeting_response', user_language)
        elif greeting_type == 'help':
            # For help requests, detect language more specifically  
            if any(malay_help in message_body.lower() for malay_help in ['tolong', 'bantuan', 'macam mana', 'camana', 'bagaimana']):
                return get_localized_message('help_response', 'ms')
            return get_localized_message('help_response', user_language)

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

    # Check for ambiguous messages (emojis, gibberish, random text)
    if is_ambiguous_message(message_body):
        return get_localized_message('ambiguous_message', user_language)

    # Determine if this is a transaction or general query
    if not is_transaction_query(message_body):
        # Handle as general query
        return generate_ai_response(message_body, wa_id)

    # Check for multiple transactions before processing
    if detect_multiple_transactions(message_body):
        logger.info(f"Multiple transactions detected in message: '{message_body}'")
        return get_localized_message('multiple_transactions', user_language)

    # Process as new transaction - try regex first for speed
    regex_result = parse_transaction_with_regex(message_body)
    
    if regex_result and regex_result.get('success'):
        # Regex parsing successful - use it for instant response
        logger.info(f"Regex parsing successful for: '{message_body}'")
        parsed_data = regex_result['data']
    else:
        # Fall back to AI parsing for complex cases
        logger.info(f"Regex parsing failed, using AI parsing for: '{message_body}'")
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
    user_mode = get_user_mode(wa_id)
    missing_fields = []
    clarification_questions = []

    # Check for missing items (mode-aware: less strict for personal users)
    if not parsed_data.get('items') or parsed_data.get('items') in [None, 'null', 'N/A', '']:
        action = parsed_data.get('action') or 'transaction'
        
        if user_mode == 'business':
            # Business users need detailed items for inventory/business tracking
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
        else:
            # Personal users: items are optional, we can infer from context or use generic terms
            # Skip item clarification for personal expenses - they often just track categories
            pass

    # Check for missing amount
    if not parsed_data.get('amount') or parsed_data.get('amount') in [None, 'null', 0]:
        clarification_questions.append(get_localized_message('clarification_amount', user_language))
        missing_fields.append('amount')

    # Check for missing customer/vendor (mode-aware: only required for business users)
    if user_mode == 'business' and not parsed_data.get('customer') and not parsed_data.get('vendor'):
        # Business users need customer/vendor for tracking business relationships
        action = parsed_data.get('action') or 'transaction'
        if action == 'purchase':
            clarification_questions.append(get_localized_message('clarification_customer_buy', user_language))
            missing_fields.append('customer/vendor')
        elif action == 'sale':
            # Sales don't require customer information - skip clarification
            pass
        elif action == 'payment_made':
            clarification_questions.append(get_localized_message('clarification_payment_to', user_language))
            missing_fields.append('customer/vendor')
        elif action == 'payment_received':
            clarification_questions.append(get_localized_message('clarification_payment_from', user_language))
            missing_fields.append('customer/vendor')
        else:
            # Generic clarification for unknown transaction types
            if user_language == 'ms':
                clarification_questions.append("👥 Siapa pihak lain dalam transaksi ini?")
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

    # Save the complete transaction with parallel processing
    success = save_to_mongodb_parallel(parsed_data, wa_id)

    if success:
        # Update user's daily logging streak
        streak_info = update_user_streak(wa_id)

        # Create a user-friendly confirmation message based on user mode and language
        user_mode = get_user_mode(wa_id)
        action = (parsed_data.get('action') or 'transaction').capitalize()
        amount = parsed_data.get('amount', 0)
        customer = safe_text(parsed_data.get('customer') or parsed_data.get('vendor', 'N/A'))
        items = safe_text(parsed_data.get('items', 'N/A'))

        # Mode-specific responses
        if user_mode == 'personal':
            # Personal budget tracking responses
            if user_language == 'ms':
                if action.lower() in ['purchase', 'expense']:
                    reply_text = f"💰 *Perbelanjaan direkod!* RM{amount}"
                else:
                    reply_text = f"💰 *Pendapatan direkod!* RM{amount}"
                if items and items != 'N/A':
                    reply_text += f"\n🏷️ {items}"
                if customer and customer != 'N/A':
                    reply_text += f"\n📍 {customer}"
            else:
                if action.lower() in ['purchase', 'expense']:
                    reply_text = f"💰 *Expense recorded!* RM{amount}"
                else:
                    reply_text = f"💰 *Income recorded!* RM{amount}"
                if items and items != 'N/A':
                    reply_text += f"\n🏷️ {items}"
                if customer and customer != 'N/A':
                    reply_text += f"\n📍 {customer}"
        else:
            # Business transaction responses (original)
            if user_language == 'ms':
                reply_text = f"✅ Direkodkan: {action} sebanyak *RM{amount}* dengan *{customer}*"
                if items and items != 'N/A':
                    reply_text += f"\n📦 Barang: {items}"
            else:
                reply_text = f"✅ Transaction completed! {action} of *RM{amount}* with *{customer}*"
                if items and items != 'N/A':
                    reply_text += f"\n📦 Items: {items}"

        # Add streak information if updated (mode-aware messaging)
        if streak_info.get('updated', False) and not streak_info.get('error', False):
            streak = streak_info.get('streak', 0)
            if streak_info.get('is_new', False):
                if user_mode == 'personal':
                    if user_language == 'ms':
                        reply_text += f"\n\n🎯 *Tracking habit baharu dimulakan!* Streak: *{streak} hari*"
                    else:
                        reply_text += f"\n\n🎯 *New tracking habit started!* Streak: *{streak} days*"
                else:
                    if user_language == 'ms':
                        reply_text += f"\n\n🎯 *Streak pencatatan harian baharu dimulakan!* Streak semasa: *{streak} hari*"
                    else:
                        reply_text += f"\n\n🎯 *New daily logging streak started!* Current streak: *{streak} days*"
            elif streak_info.get('was_broken', False):
                if user_mode == 'personal':
                    if user_language == 'ms':
                        reply_text += f"\n\n🔄 *Tracking habit dimulakan semula!* Streak: *{streak} hari*"
                    else:
                        reply_text += f"\n\n🔄 *Tracking habit restarted!* Streak: *{streak} days*"
                else:
                    if user_language == 'ms':
                        reply_text += f"\n\n🔄 *Streak dimulakan semula!* Streak semasa: *{streak} hari*"
                    else:
                        reply_text += f"\n\n🔄 *Streak restarted!* Current streak: *{streak} days*"
            else:
                if user_mode == 'personal':
                    if user_language == 'ms':
                        reply_text += f"\n\n🔥 *Great job tracking!* Streak: *{streak} hari*"
                    else:
                        reply_text += f"\n\n🔥 *Great job tracking!* Streak: *{streak} days*"
                else:
                    if user_language == 'ms':
                        reply_text += f"\n\n🔥 *Streak diperpanjang!* Streak semasa: *{streak} hari*"
                    else:
                        reply_text += f"\n\n🔥 *Streak extended!* Current streak: *{streak} days*"
        elif not streak_info.get('updated', False) and not streak_info.get('error', False):
            # Already logged today (mode-aware messaging)
            streak = streak_info.get('streak', 0)
            if user_mode == 'personal':
                if user_language == 'ms':
                    day_word = "hari" if streak == 1 else "hari"
                    reply_text += f"\n\n🔥 Anda sudah track hari ini! Streak: *{streak} {day_word}*"
                else:
                    day_word = "day" if streak == 1 else "days"
                    reply_text += f"\n\n🔥 You've already tracked today! Streak: *{streak} {day_word}*"
            else:
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

    # All fields completed, save the transaction with parallel processing
    clear_pending_transaction(wa_id)
    success = save_to_mongodb_parallel(transaction_data, wa_id)

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

def process_image_parallel(image_data: bytes) -> dict:
    """Process image using parallel GPT Vision and fallback text extraction."""
    
    def vision_processing():
        """Primary: GPT Vision direct parsing"""
        try:
            return parse_receipt_with_vision(image_data)
        except Exception as e:
            logger.error(f"GPT Vision processing failed: {e}")
            return {"error": "Vision processing failed"}
    
    def text_extraction_fallback():
        """Fallback: Text extraction + AI parsing"""
        try:
            extracted_text = extract_text_from_image(image_data)
            if extracted_text:
                return parse_receipt_with_ai(extracted_text)
            else:
                return {"error": "No text extracted"}
        except Exception as e:
            logger.error(f"Text extraction fallback failed: {e}")
            return {"error": "Text extraction failed"}
    
    # Run both processes in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both processing methods
        future_vision = executor.submit(vision_processing)
        future_text = executor.submit(text_extraction_fallback)
        
        # Get vision result first (primary method)
        vision_result = future_vision.result()
        
        # If vision succeeded, use it; otherwise use text extraction
        if "error" not in vision_result:
            logger.info("Using GPT Vision result")
            # Cancel the text extraction if it's still running
            future_text.cancel()
            return vision_result
        else:
            logger.info("GPT Vision failed, using text extraction fallback")
            text_result = future_text.result()
            return text_result

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

        # Process image using parallel GPT Vision and text extraction
        parsed_data = process_image_parallel(image_data)

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

        # Save to database with image and user isolation using parallel processing
        success = save_to_mongodb_parallel(parsed_data, wa_id, image_data)

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
    
    # OpenAI client already initialized at module level
    if openai_client is None:
        logger.error("OpenAI client not available. Exiting.")
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
