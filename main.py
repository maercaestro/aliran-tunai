import os
import logging
import json
import base64
import io
import tempfile
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import pytesseract
import cv2
import numpy as np

# --- Setup ---
load_dotenv()

# Securely get your tokens and keys
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# Set up basic logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Initialize Clients ---
# OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# MongoDB
try:
    mongo_client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
    # Send a ping to confirm a successful connection
    mongo_client.admin.command('ping')
    logger.info("Pinged your deployment. You successfully connected to MongoDB!")
    db = mongo_client.transactions_db
    collection = db.entries
    users_collection = db.users
except Exception as e:
    logger.error(f"Error connecting to MongoDB: {e}")
    mongo_client = None

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

def get_pending_transaction(chat_id: int) -> dict:
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
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
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
    system_prompt = """
    You are an expert bookkeeping assistant. Your task is to extract transaction details from a user's message.
    Extract the following fields: 'action', 'amount' (as a number), 'customer' (or 'vendor'), 'items' (what was bought/sold),
    'terms' (e.g., 'credit', 'cash', 'hutang'), and a brief 'description'.
    
    The 'action' field MUST BE one of the following exact values: "sale", "purchase", or "payment".
    
    Pay special attention to ITEMS - this is what was actually bought or sold. Examples:
    - "beli beras 5 kg" → items: "beras 5 kg"
    - "jual ayam 2 ekor" → items: "ayam 2 ekor" 
    - "azim beli nasi lemak" → items: "nasi lemak"
    - "sold 10 widgets to ABC" → items: "widgets (10 units)"
    
    The items field should capture the actual product/service being transacted, including quantities if mentioned.
    
    If a value is not found, use null.
    Return the result ONLY as a JSON object.
    """
    try:
        response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"}
        )
        result_json = response.choices[0].message.content
        logger.info(f"Received JSON from OpenAI: {result_json}")
        return json.loads(result_json)
    except Exception as e:
        logger.error(f"Error calling OpenAI: {e}")
        return {"error": str(e)}

# --- Image Processing Functions ---
def preprocess_image_for_ocr(image_bytes: bytes) -> np.ndarray:
    """Preprocess image to improve OCR accuracy."""
    try:
        # Convert bytes to PIL Image
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        # Convert PIL to OpenCV format
        opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply threshold to get binary image
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return thresh
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
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Receipt text:\n{extracted_text}"}
            ],
            response_format={"type": "json_object"}
        )
        result_json = response.choices[0].message.content
        logger.info(f"Received JSON from OpenAI: {result_json}")
        return json.loads(result_json)
    except Exception as e:
        logger.error(f"Error calling OpenAI for receipt parsing: {e}")
        return {"error": str(e)}

# --- Financial Metrics Functions ---
def get_ccc_metrics(chat_id: int) -> dict:
    """Calculate Cash Conversion Cycle metrics from database for specific user."""
    try:
        # For demonstration purposes, this returns sample data.
        # In a real implementation, you would calculate these from your database:
        # - DSO (Days Sales Outstanding): Average days to collect receivables
        # - DIO (Days Inventory Outstanding): Average days inventory stays
        # - DPO (Days Payable Outstanding): Average days to pay suppliers
        # - CCC (Cash Conversion Cycle): DSO + DIO - DPO
        
        # Example of how to query user-specific data from MongoDB:
        # from datetime import datetime, timedelta
        # ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)
        # 
        # pipeline = [
        #     {"$match": {
        #         "timestamp": {"$gte": ninety_days_ago},
        #         "chat_id": chat_id
        #     }},
        #     # Add your aggregation stages here to calculate DSO, DIO, DPO
        # ]
        # results = list(collection.aggregate(pipeline))
        
        # Sample metrics - replace with actual calculations from your database
        dso = 48  # Days Sales Outstanding
        dio = 25  # Days Inventory Outstanding  
        dpo = 15  # Days Payable Outstanding
        ccc = dso + dio - dpo  # Cash Conversion Cycle
        
        logger.info(f"Calculated CCC metrics for chat_id {chat_id}: CCC={ccc}")
        
        return {
            'ccc': ccc,
            'dso': dso,
            'dio': dio,
            'dpo': dpo
        }
    except Exception as e:
        logger.error(f"Error calculating CCC metrics for chat_id {chat_id}: {e}")
        return {'ccc': 0, 'dso': 0, 'dio': 0, 'dpo': 0}

def generate_actionable_advice(metrics: dict) -> str:
    """Generate actionable advice based on financial metrics."""
    dso = metrics.get('dso', 0)
    dio = metrics.get('dio', 0)
    dpo = metrics.get('dpo', 0)
    
    if dso > 45:
        return "Your biggest cash drain is waiting for customer payments (DSO is high). Consider following up on overdue invoices."
    elif dio > 30:
        return "Your inventory is sitting for a while (DIO is high). Consider a promotion to move slow-moving stock."
    elif dpo < 20:
        return "You're paying your suppliers very quickly (DPO is low). Consider negotiating longer payment terms to improve your cash flow."
    else:
        return "Your cash flow looks balanced. Keep up the great work!"

# --- Database Function ---
def save_to_mongodb(data: dict, chat_id: int, image_data: bytes = None) -> bool:
    """Saves the transaction data to MongoDB with user isolation."""
    if not mongo_client or "error" in data:
        logger.error("MongoDB client not available or data contains an error.")
        return False
    
    try:
        # Add user isolation with chat_id
        data['chat_id'] = chat_id
        
        # Add a timestamp to the record
        data['timestamp'] = datetime.now(timezone.utc)
        
        # Add image data if provided
        if image_data:
            # Convert image to base64 for storage
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            data['receipt_image'] = image_base64
            data['has_image'] = True
        else:
            data['has_image'] = False
        
        # Insert the data into the collection
        collection.insert_one(data)
        logger.info(f"Successfully inserted data into MongoDB for chat_id {chat_id}: {data.get('action', 'Unknown')} - {data.get('amount', 'N/A')}")
        return True
    except Exception as e:
        logger.error(f"Error saving to MongoDB: {e}")
        return False

# --- Telegram Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_text = """
Hi! I'm your financial assistant. 

You can:
📝 Send me a text message describing a transaction
📸 Send me a photo of a receipt to automatically extract transaction details
📊 Use /status to get your financial health report with actionable advice
📋 Use /summary to see your recent transactions
🔥 Use /streak to check your daily logging streak

All your data is kept private and separate from other users!
Build your daily logging streak by recording transactions every day! 💪
    """
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    chat_id = update.message.chat_id
    logger.info(f"Received message from chat_id {chat_id}: '{user_message}'")
    
    # Check if user has a pending transaction waiting for clarification
    pending = get_pending_transaction(chat_id)
    
    if pending:
        # This might be a clarification response
        missing_fields = pending['missing_fields']
        
        if is_clarification_response(user_message, missing_fields):
            # Process as clarification
            await handle_clarification_response(update, context, user_message, pending)
            return
        else:
            # User is starting a new transaction, clear the old pending one
            clear_pending_transaction(chat_id)
    
    # Process as new transaction
    parsed_data = parse_transaction_with_ai(user_message)
    
    if "error" in parsed_data:
        await update.message.reply_text(f"🤖 Sorry, I couldn't understand that. Please try rephrasing.")
        return

    # Check for missing critical information and ask for clarification
    missing_fields = []
    clarification_questions = []
    
    # Check for missing items
    if not parsed_data.get('items') or parsed_data.get('items') in [None, 'null', 'N/A', '']:
        action = parsed_data.get('action', 'transaction')
        if action == 'purchase':
            clarification_questions.append("🛒 What item did you buy?")
        elif action == 'sale':
            clarification_questions.append("🏪 What item did you sell?")
        else:
            clarification_questions.append("📦 What item was involved in this transaction?")
        missing_fields.append('items')
    
    # Check for missing amount
    if not parsed_data.get('amount') or parsed_data.get('amount') in [None, 'null', 0]:
        clarification_questions.append("💰 What was the amount?")
        missing_fields.append('amount')
    
    # Check for missing customer/vendor
    if not parsed_data.get('customer') and not parsed_data.get('vendor'):
        action = parsed_data.get('action', 'transaction')
        if action == 'purchase':
            clarification_questions.append("🏪 Who did you buy from?")
        elif action == 'sale':
            clarification_questions.append("👤 Who did you sell to?")
        else:
            clarification_questions.append("👥 Who was the other party in this transaction?")
        missing_fields.append('customer/vendor')

    # If there are missing fields, store transaction and ask for clarification
    if clarification_questions:
        # Store the partial transaction
        store_pending_transaction(chat_id, parsed_data, missing_fields)
        
        clarification_text = "🤔 I understood this as a **" + parsed_data.get('action', 'transaction') + "** but I need some clarification:\n\n"
        clarification_text += "\n".join(clarification_questions)
        clarification_text += "\n\nPlease provide the missing information and I'll log the complete transaction for you! 😊"
        
        await update.message.reply_text(clarification_text, parse_mode='Markdown')
        return

    # Save the complete transaction
    success = save_to_mongodb(parsed_data, chat_id)
    
    if success:
        # Update user's daily logging streak
        streak_info = update_user_streak(chat_id)
        
        # Create a user-friendly confirmation message
        action = parsed_data.get('action', 'N/A').capitalize()
        amount = parsed_data.get('amount', 0)
        customer = parsed_data.get('customer') or parsed_data.get('vendor', 'N/A')
        items = parsed_data.get('items', 'N/A')
        
        reply_text = f"✅ Logged: {action} of **{amount}** with **{customer}**"
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

async def handle_clarification_response(update: Update, context: ContextTypes.DEFAULT_TYPE, user_message: str, pending: dict) -> None:
    """Handle user's clarification response to complete the transaction."""
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
        
        action = transaction_data.get('action', '')
        if action == 'purchase':
            transaction_data['vendor'] = extracted_name
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
                action = transaction_data.get('action', 'transaction')
                if action == 'purchase':
                    clarification_questions.append("🛒 What item did you buy?")
                elif action == 'sale':
                    clarification_questions.append("🏪 What item did you sell?")
                else:
                    clarification_questions.append("📦 What item was involved?")
            elif field == 'amount':
                clarification_questions.append("💰 What was the amount?")
            elif field == 'customer/vendor':
                action = transaction_data.get('action', 'transaction')
                if action == 'purchase':
                    clarification_questions.append("🏪 Who did you buy from?")
                elif action == 'sale':
                    clarification_questions.append("👤 Who did you sell to?")
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
        
        action = transaction_data.get('action', 'N/A').capitalize()
        amount = transaction_data.get('amount', 0)
        customer = transaction_data.get('customer') or transaction_data.get('vendor', 'N/A')
        items = transaction_data.get('items', 'N/A')
        
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
_This is the time it takes for your business to convert investments in inventory and receivables back into cash._

**Breakdown:**
🤝 Customer Payments (DSO): **{metrics['dso']} days**
📦 Inventory on Hand (DIO): **{metrics['dio']} days** (assumed)
💸 Supplier Payments (DPO): **{metrics['dpo']} days** (assumed)

---
**Actionable Advice:**
{advice}"""
        
        await update.message.reply_text(report, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error generating status report: {e}")
        await update.message.reply_text("❌ Sorry, there was an error generating your financial status report.")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a summary of user's transactions."""
    try:
        chat_id = update.message.chat_id
        logger.info(f"Generating summary for chat_id {chat_id}")
        
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
            vendor = transaction.get('vendor') or transaction.get('customer', 'N/A')
            items = transaction.get('items', '')
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
    """Handle photo messages (receipts)."""
    try:
        chat_id = update.message.chat_id
        logger.info(f"Processing photo from chat_id {chat_id}")
        
        # Send initial processing message
        processing_msg = await update.message.reply_text("📸 Processing your receipt... Please wait.")
        
        # Get the largest photo (best quality)
        photo = update.message.photo[-1]
        
        # Get file info
        file = await context.bot.get_file(photo.file_id)
        
        # Download the image directly using the telegram file object
        image_data = await file.download_as_bytearray()
        
        # Extract text from image
        extracted_text = extract_text_from_image(bytes(image_data))
        
        if not extracted_text:
            await processing_msg.edit_text("❌ Sorry, I couldn't extract any text from this image. Please try with a clearer photo.")
            return
        
        # Parse the extracted text with AI
        parsed_data = parse_receipt_with_ai(extracted_text)
        
        if "error" in parsed_data:
            await processing_msg.edit_text("🤖 Sorry, I couldn't understand the receipt content. Please try with a different image or send the details as text.")
            return
        
        # Check for missing critical information in receipt
        missing_fields = []
        clarification_questions = []
        
        # Check for missing items
        if not parsed_data.get('items') or parsed_data.get('items') in [None, 'null', 'N/A', '']:
            action = parsed_data.get('action', 'transaction')
            if action == 'purchase':
                clarification_questions.append("🛒 What items did you buy?")
            elif action == 'sale':
                clarification_questions.append("🏪 What items did you sell?")
            else:
                clarification_questions.append("📦 What items were in this transaction?")
            missing_fields.append('items')
        
        # Check for missing amount
        if not parsed_data.get('amount') or parsed_data.get('amount') in [None, 'null', 0]:
            clarification_questions.append("💰 What was the total amount?")
            missing_fields.append('amount')

        # If there are missing critical fields, ask for clarification
        if clarification_questions:
            clarification_text = "📸 **Receipt processed** but I need some clarification:\n\n"
            clarification_text += "\n".join(clarification_questions)
            clarification_text += "\n\nPlease provide the missing information and I'll complete the transaction for you! 😊"
            
            await processing_msg.edit_text(clarification_text, parse_mode='Markdown')
            return
        
        # Save to database with image and user isolation
        success = save_to_mongodb(parsed_data, chat_id, bytes(image_data))
        
        if success:
            # Create detailed confirmation message
            action = parsed_data.get('action', 'Transaction').capitalize()
            amount = parsed_data.get('amount', 'N/A')
            vendor = parsed_data.get('vendor') or parsed_data.get('customer', 'N/A')
            date = parsed_data.get('date', 'N/A')
            items = parsed_data.get('items', 'N/A')
            description = parsed_data.get('description', 'N/A')
            
            reply_text = f"""✅ **Receipt processed successfully!**

📋 **Details extracted:**
• Action: {action}
• Amount: {amount}
• Vendor/Customer: {vendor}
• Items: {items}
• Date: {date}
• Description: {description}

💾 Saved to database with receipt image attached."""
            
            await processing_msg.edit_text(reply_text, parse_mode='Markdown')
        else:
            await processing_msg.edit_text("❌ There was an error saving your receipt to the database.")
            
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        await update.message.reply_text("❌ Sorry, there was an error processing your receipt. Please try again.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle document uploads (in case user sends image as document)."""
    document = update.message.document
    
    # Check if it's an image document
    if document.mime_type and document.mime_type.startswith('image/'):
        # Treat it as a photo
        await handle_photo_document(update, context)
    else:
        await update.message.reply_text("📄 I can only process image files. Please send your receipt as a photo.")

async def handle_photo_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle image documents."""
    try:
        chat_id = update.message.chat_id
        processing_msg = await update.message.reply_text("📸 Processing your receipt document... Please wait.")
        
        document = update.message.document
        file = await context.bot.get_file(document.file_id)
        
        # Download the image directly using the telegram file object
        image_data = await file.download_as_bytearray()
        
        # Extract text from image
        extracted_text = extract_text_from_image(bytes(image_data))
        
        if not extracted_text:
            await processing_msg.edit_text("❌ Sorry, I couldn't extract any text from this document. Please try with a clearer image.")
            return
        
        # Parse the extracted text with AI
        parsed_data = parse_receipt_with_ai(extracted_text)
        
        if "error" in parsed_data:
            await processing_msg.edit_text("🤖 Sorry, I couldn't understand the receipt content. Please try with a different image or send the details as text.")
            return
        
        # Save to database with image and user isolation
        success = save_to_mongodb(parsed_data, chat_id, bytes(image_data))
        
        if success:
            action = parsed_data.get('action', 'Transaction').capitalize()
            amount = parsed_data.get('amount', 'N/A')
            vendor = parsed_data.get('vendor') or parsed_data.get('customer', 'N/A')
            
            reply_text = f"✅ **Document processed!** {action} of **{amount}** with **{vendor}** saved to database."
            await processing_msg.edit_text(reply_text, parse_mode='Markdown')
        else:
            await processing_msg.edit_text("❌ There was an error saving your receipt to the database.")
            
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        await processing_msg.edit_text("❌ Sorry, there was an error processing your document. Please try again.")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("summary", summary))
    application.add_handler(CommandHandler("streak", streak))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running with multi-user support, image processing, financial status, and streak capabilities...")
    application.run_polling()

if __name__ == '__main__':
    main()