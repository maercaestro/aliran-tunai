from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file, abort
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
import os
import logging
import pandas as pd
import io
import jwt
import random
from functools import wraps
import requests
import re
from collections import defaultdict
import time
import openai

# --- Setup ---
load_dotenv()

# Set up basic logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)

# Enhanced CORS configuration for production
CORS(app, 
     origins=['https://aliran-tunai.com', 'http://localhost:5173', 'http://localhost:3000'],
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     supports_credentials=True)

# Security configuration
MALICIOUS_PATTERNS = [
    r'/cgi-bin/',
    r'\.php$',
    r'/wp-',
    r'/dns-query',
    r'/owa/',
    r'\.asp',
    r'\.jsp',
    r'/admin',
    r'/phpmyadmin',
    r'/test',
    r'/shell',
    r'/hack',
    r'/exploit'
]

# Rate limiting storage (in production, use Redis)
request_counts = defaultdict(list)
RATE_LIMIT_REQUESTS = 200  # requests per minute (increased for development/testing)
RATE_LIMIT_WINDOW = 60  # seconds

def is_malicious_request(path):
    """Check if the request path matches known malicious patterns."""
    for pattern in MALICIOUS_PATTERNS:
        if re.search(pattern, path, re.IGNORECASE):
            return True
    return False

def check_rate_limit(client_ip):
    """Simple rate limiting check."""
    now = time.time()
    # Clean old requests outside the window
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip] 
        if now - req_time < RATE_LIMIT_WINDOW
    ]
    
    # Check if over limit
    if len(request_counts[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False
    
    # Add current request
    request_counts[client_ip].append(now)
    return True

@app.before_request
def security_filter():
    """Filter malicious requests before they reach route handlers."""
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    # Skip security checks for debug and health endpoints
    if request.path in ['/api/health', '/api/debug/connection']:
        return
    
    # Temporary debug mode - check environment variable
    debug_mode = os.getenv('DEBUG_SECURITY', 'false').lower() == 'true'
    if debug_mode:
        logger.info(f"DEBUG MODE: Security checks bypassed for {request.path} from {client_ip}")
        return
    
    # Rate limiting (more lenient for auth endpoints)
    rate_limit = RATE_LIMIT_REQUESTS
    if request.path.startswith('/api/auth/'):
        rate_limit = 20  # More restrictive for auth endpoints to prevent brute force
    
    if not check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip} on path: {request.path}")
        abort(429)  # Too Many Requests
    
    # Block malicious requests
    if is_malicious_request(request.path):
        logger.warning(f"Blocked malicious request from {client_ip}: {request.path}")
        abort(404)  # Return 404 instead of revealing server info
    
    # Log all incoming requests for debugging
    logger.info(f"Request: {request.method} {request.path} from {client_ip} - User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
    
    # Detailed logging for API requests
    if request.path.startswith('/api/') or request.path.startswith('/whatsapp/'):
        logger.info(f"API request details: {request.method} {request.path} - Headers: {dict(request.headers)}")
        if request.is_json and request.path.startswith('/api/auth/'):
            # Log auth requests (without sensitive data)
            data = request.get_json() or {}
            safe_data = {k: v if k != 'phone_number' else f"{v[:3]}***{v[-3:]}" if v else None for k, v in data.items()}
            logger.info(f"Auth request data: {safe_data}")

@app.errorhandler(404)
def not_found(error):
    """Custom 404 handler to avoid revealing server information."""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(429)
def rate_limit_exceeded(error):
    """Custom rate limit handler."""
    return jsonify({'error': 'Rate limit exceeded'}), 429

@app.after_request
def after_request(response):
    """Add additional headers and logging for debugging."""
    # CORS is handled by flask-cors extension above, no need to add headers here
    
    # Log successful API responses for debugging
    if request.path.startswith('/api/auth/') and response.status_code == 200:
        logger.info(f"Successful auth response: {request.method} {request.path} - Status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        # Log response data (without sensitive information)
        try:
            if response.is_json:
                data = response.get_json()
                safe_data = {k: v if k not in ['token'] else f"{v[:20]}..." if v else None for k, v in data.items()}
                logger.info(f"Response data: {safe_data}")
        except Exception as e:
            logger.warning(f"Could not parse response data: {e}")
    
    return response

# --- MongoDB Connection ---
MONGO_URI = os.getenv("MONGO_URI")

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")

# WhatsApp Configuration
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v18.0")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

mongo_client = None
db = None
collection = None
users_collection = None
otp_collection = None

def connect_to_mongodb():
    """Connect to MongoDB with retry logic and better error handling."""
    global mongo_client, db, collection, users_collection, otp_collection
    
    if not MONGO_URI:
        logger.error("MONGO_URI environment variable not set!")
        return False
    
    try:
        logger.info("Attempting to connect to MongoDB...")
        
        # Try different SSL configurations to resolve the TLS error
        connection_options = [
            # Option 1: Fixed SSL/TLS configuration
            {
                "tls": True,
                "tlsAllowInvalidCertificates": False,
                "tlsAllowInvalidHostnames": False,
                "retryWrites": True,
                "w": "majority",
                "serverSelectionTimeoutMS": 3000,
                "connectTimeoutMS": 3000,
                "socketTimeoutMS": 3000
            },
            # Option 2: Alternative SSL configuration
            {
                "ssl": True,
                "ssl_cert_reqs": "CERT_NONE",
                "serverSelectionTimeoutMS": 5000,
                "connectTimeoutMS": 5000,
                "socketTimeoutMS": 5000
            },
            # Option 3: Basic configuration with Server API
            {
                "server_api": ServerApi('1'),
                "serverSelectionTimeoutMS": 3000,
                "connectTimeoutMS": 3000
            },
            # Option 4: Minimal configuration
            {
                "serverSelectionTimeoutMS": 5000
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
                otp_collection = db.otp_codes
                
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
        otp_collection = None
        return False

# --- Authentication Functions ---
def generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))

def send_whatsapp_message(to_phone_number: str, message: str) -> bool:
    """Send WhatsApp message using Business API."""
    try:
        if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
            logger.error("WhatsApp configuration missing")
            return False
        
        url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        
        headers = {
            'Authorization': f'Bearer {WHATSAPP_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'messaging_product': 'whatsapp',
            'to': to_phone_number,
            'type': 'text',
            'text': {
                'body': message
            }
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        # Enhanced logging for debugging
        logger.info(f"WhatsApp API Request to: {url}")
        logger.info(f"Payload: {payload}")
        logger.info(f"Response Status: {response.status_code}")
        logger.info(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            # Parse response to check for actual delivery status
            response_data = response.json()
            logger.info(f"WhatsApp API Response Data: {response_data}")
            
            # Check if message was actually queued/sent
            if 'messages' in response_data and len(response_data['messages']) > 0:
                message_id = response_data['messages'][0].get('id')
                logger.info(f"WhatsApp message queued with ID: {message_id} to {to_phone_number}")
                return True
            else:
                logger.error(f"WhatsApp message not queued properly: {response_data}")
                return False
        else:
            logger.error(f"Failed to send WhatsApp message: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        return False

def create_jwt_token(wa_id: str, user_data: dict) -> str:
    """Create a JWT token for authenticated user."""
    payload = {
        'wa_id': wa_id,
        'owner_name': user_data.get('owner_name', ''),
        'company_name': user_data.get('company_name', ''),
        'exp': datetime.now(timezone.utc) + timedelta(days=30)  # Token expires in 30 days
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')

def verify_jwt_token(token: str) -> dict:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Token has expired'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}

def token_required(f):
    """Decorator to require valid JWT token for API routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Authentication token is missing'}), 401
        
        payload = verify_jwt_token(token)
        if 'error' in payload:
            return jsonify(payload), 401
        
        # Add user info to the request context
        request.current_user = payload
        return f(*args, **kwargs)
    
    return decorated

def get_mock_ccc_data(chat_id: int) -> dict:
    """Provide mock CCC data when database is unavailable."""
    logger.info(f"Providing mock CCC data for chat_id {chat_id}")
    
    return {
        'ccc': 45.5,
        'dso': 30.0,
        'dio': 25.5,
        'dpo': 10.0,
        'totalTransactions': 15,
        'recentTransactions': [
            {
                'id': 'mock_1',
                'date': '2025-08-29',
                'type': 'sale',
                'amount': 2500.00,
                'customer': 'Customer A',
                'status': 'completed',
                'items': 'Product X'
            },
            {
                'id': 'mock_2',
                'date': '2025-08-28',
                'type': 'purchase',
                'amount': 1200.00,
                'customer': 'Supplier B',
                'status': 'completed',
                'items': 'Raw materials'
            },
            {
                'id': 'mock_3',
                'date': '2025-08-27',
                'type': 'payment_received',
                'amount': 1800.00,
                'customer': 'Customer C',
                'status': 'completed',
                'items': 'Payment for invoice #123'
            },
            {
                'id': 'mock_4',
                'date': '2025-08-26',
                'type': 'sale',
                'amount': 3200.00,
                'customer': 'Customer D',
                'status': 'completed',
                'items': 'Product Y'
            }
        ],
        'summary': {
            'totalSales': 15000.00,
            'totalPurchases': 8500.00,
            'totalPaymentsReceived': 12000.00,
            'totalPaymentsMade': 7800.00
        },
        'transaction_breakdown': [
            {'_id': 'sale', 'count': 8, 'total_amount': 15000.00},
            {'_id': 'purchase', 'count': 4, 'total_amount': 8500.00},
            {'_id': 'payment_received', 'count': 6, 'total_amount': 12000.00},
            {'_id': 'payment_made', 'count': 3, 'total_amount': 7800.00}
        ],
        'financial_details': {
            'total_sales': 15000.00,
            'total_purchases': 8500.00,
            'estimated_cogs': 7500.00,
            'remaining_inventory': 1000.00,
            'total_credit_sales': 10000.00,
            'outstanding_receivables': 2500.00,
            'total_credit_purchases': 6000.00,
            'outstanding_payables': 1500.00,
            'total_payments_received': 12000.00,
            'total_payments_made': 7800.00
        },
        'mock_data': True,  # Flag to indicate this is mock data
        'database_status': 'disconnected'
    }

def get_ccc_metrics(user_id: str) -> dict:
    """Calculate Cash Conversion Cycle metrics with corrected logic."""
    global mongo_client, collection
    
    # Check if MongoDB client is available, if not try to reconnect
    if mongo_client is None or collection is None:
        logger.warning("MongoDB client not available for CCC metrics, attempting to reconnect...")
        if not connect_to_mongodb():
            logger.error("Failed to connect to MongoDB for CCC metrics. Using mock data.")
            return get_mock_ccc_data(int(user_id) if user_id.isdigit() else 123456)
    
    try:
        ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)
        period_days = 90
        
        # Get all transactions for the period
        # Support both Telegram (chat_id) and WhatsApp (wa_id) data
        transactions = list(collection.find({
            "timestamp": {"$gte": ninety_days_ago},
            "$or": [
                {"chat_id": int(user_id) if user_id.isdigit() else 0},  # Try to convert to int for legacy chat_id
                {"wa_id": user_id}  # WhatsApp IDs are strings
            ]
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
        
        # Get all transactions for dashboard (not just recent)  
        # Support both Telegram (chat_id) and WhatsApp (wa_id) data
        all_transactions = list(collection.find({
            "$or": [
                {"chat_id": int(user_id) if user_id.isdigit() else 0},
                {"wa_id": user_id}  # WhatsApp IDs are strings
            ]
        }).sort('timestamp', -1))
        
        # Format all transactions for frontend
        formatted_recent = []
        for t in all_transactions:
            # Ensure we have valid data for all required fields
            transaction_type = t.get('action') or t.get('type', 'unknown')
            if not transaction_type or transaction_type == 'null':
                transaction_type = 'unknown'
                
            customer_name = t.get('customer') or t.get('vendor') or 'Unknown'
            if not customer_name or customer_name == 'null':
                customer_name = 'Unknown'
                
            formatted_recent.append({
                'id': str(t['_id']),
                'date': t['timestamp'].strftime('%Y-%m-%d') if t.get('timestamp') else '',
                'type': transaction_type,
                'amount': t.get('amount', 0),
                'customer': customer_name,
                'status': 'completed',  # Default status
                'items': t.get('items', '')
            })
        
        logger.info(f"FIXED CCC calculation for user_id {user_id}:")
        logger.info(f"  DSO: {dso:.1f} days (credit sales: ${total_credit_sales:.2f}, outstanding: ${outstanding_receivables:.2f})")
        logger.info(f"  DIO: {dio:.1f} days (purchases: ${total_purchases:.2f}, est. COGS: ${estimated_cogs:.2f}, inventory: ${remaining_inventory:.2f})")
        logger.info(f"  DPO: {dpo:.1f} days (credit purchases: ${total_credit_purchases:.2f}, outstanding payables: ${outstanding_payables:.2f})")
        logger.info(f"  CCC: {ccc:.1f} days")
        
        return {
            'ccc': round(ccc, 1),
            'dso': round(dso, 1),
            'dio': round(dio, 1),
            'dpo': round(dpo, 1),
            'totalTransactions': len(transactions),
            'recentTransactions': formatted_recent,  # Return all transactions
            'summary': {
                'totalSales': total_sales,
                'totalPurchases': total_purchases,
                'totalPaymentsReceived': sum(p['amount'] for p in payments_received),
                'totalPaymentsMade': total_payments_made_amount
            },
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
        logger.error(f"Error in FIXED CCC calculation for user_id {user_id}: {e}")
        logger.info("Fallback to mock data due to database error")
        return get_mock_ccc_data(int(user_id) if user_id.isdigit() else 123456)

# --- AI Categorization Functions ---

def categorize_purchase_with_ai(description, vendor=None, amount=None):
    """Use OpenAI to categorize a purchase transaction."""
    if not OPENAI_API_KEY:
        logger.warning("OpenAI API key not configured, returning default category")
        return "OTHER"
    
    try:
        # Create a detailed prompt for categorization
        prompt = f"""
        Categorize this business purchase transaction into one of these categories:
        - OPEX: Operating expenses (utilities, rent, marketing, office supplies, services)
        - CAPEX: Capital expenses (equipment, machinery, property, vehicles, long-term assets)
        - COGS: Cost of goods sold (raw materials, inventory for resale, direct production costs)
        - INVENTORY: Inventory purchases (stock for resale, finished goods)
        - MARKETING: Marketing and advertising expenses
        - UTILITIES: Utilities and overhead costs (electricity, water, internet, phone)
        - OTHER: Miscellaneous or unclear expenses
        
        Transaction details:
        Description: {description}
        Vendor: {vendor or 'Unknown'}
        Amount: ${amount or 'Unknown'}
        
        Based on this information, return ONLY the category code (OPEX, CAPEX, COGS, INVENTORY, MARKETING, UTILITIES, or OTHER).
        """
        
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a financial AI assistant that categorizes business expenses. Return only the category code."},
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

# --- Authentication Routes ---

@app.route('/api/debug/whatsapp-config', methods=['GET'])
def debug_whatsapp_config():
    """Debug WhatsApp configuration (for troubleshooting)."""
    try:
        config_status = {
            'whatsapp_access_token_exists': bool(WHATSAPP_ACCESS_TOKEN),
            'whatsapp_phone_number_id_exists': bool(WHATSAPP_PHONE_NUMBER_ID),
            'whatsapp_api_version': WHATSAPP_API_VERSION,
            'access_token_length': len(WHATSAPP_ACCESS_TOKEN) if WHATSAPP_ACCESS_TOKEN else 0,
            'phone_number_id': WHATSAPP_PHONE_NUMBER_ID[:10] + '...' if WHATSAPP_PHONE_NUMBER_ID else None
        }
        
        # Test WhatsApp API connectivity
        if WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID:
            test_url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}"
            headers = {'Authorization': f'Bearer {WHATSAPP_ACCESS_TOKEN}'}
            
            try:
                test_response = requests.get(test_url, headers=headers, timeout=10)
                config_status['api_connectivity'] = {
                    'status_code': test_response.status_code,
                    'accessible': test_response.status_code == 200,
                    'response_preview': test_response.text[:200] if test_response.text else None
                }
            except Exception as e:
                config_status['api_connectivity'] = {
                    'error': str(e),
                    'accessible': False
                }
        else:
            config_status['api_connectivity'] = {
                'error': 'Missing configuration',
                'accessible': False
            }
        
        return jsonify(config_status), 200
        
    except Exception as e:
        logger.error(f"Error checking WhatsApp config: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/test-whatsapp', methods=['POST'])
def test_whatsapp_message():
    """Send a test WhatsApp message for debugging."""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        
        if not phone_number:
            return jsonify({'error': 'Phone number is required'}), 400
        
        test_message = f"""🔧 *Test Message from AliranTunai*

This is a test message sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.

If you receive this, WhatsApp messaging is working!

- AliranTunai Debug Team"""
        
        # Send test message with detailed logging
        success = send_whatsapp_message(phone_number, test_message)
        
        return jsonify({
            'success': success,
            'message': 'Test message sent' if success else 'Test message failed',
            'phone_number': phone_number,
            'timestamp': datetime.now().isoformat()
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error sending test WhatsApp message: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/send-otp', methods=['POST'])
def send_otp():
    """Send OTP to user's phone number."""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        
        if not phone_number:
            return jsonify({'error': 'Phone number is required'}), 400
        
        # Check if user exists in the system
        if mongo_client is None or users_collection is None:
            if not connect_to_mongodb():
                return jsonify({'error': 'Database connection failed'}), 500
        
        user = users_collection.find_one({"wa_id": phone_number})
        if not user:
            return jsonify({'error': 'Phone number not registered. Please register via WhatsApp first.'}), 404
        
        # Generate OTP
        otp_code = generate_otp()
        
        # Store OTP in database with expiration (5 minutes)
        otp_data = {
            'phone_number': phone_number,
            'otp': otp_code,
            'created_at': datetime.now(timezone.utc),
            'expires_at': datetime.now(timezone.utc) + timedelta(minutes=5),
            'used': False
        }
        
        otp_collection.insert_one(otp_data)
        
        # Send OTP via WhatsApp
        otp_message = f"""🔐 *AliranTunai Login Code*

Your verification code is: *{otp_code}*

This code will expire in 5 minutes.
Do not share this code with anyone.

- AliranTunai Team"""
        
        whatsapp_sent = send_whatsapp_message(phone_number, otp_message)
        
        if whatsapp_sent:
            logger.info(f"OTP sent via WhatsApp to {phone_number}")
            return jsonify({
                'message': 'OTP sent successfully via WhatsApp'
            }), 200
        else:
            # Fallback: log the OTP if WhatsApp fails
            logger.info(f"WhatsApp failed, OTP for {phone_number}: {otp_code}")
            return jsonify({
                'message': 'OTP generated but WhatsApp delivery failed',
                'otp': otp_code  # Include OTP as fallback
            }), 200
        
    except Exception as e:
        logger.error(f"Error sending OTP: {e}")
        return jsonify({'error': 'Failed to send OTP'}), 500

@app.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP and return JWT token."""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        otp_input = data.get('otp')
        
        logger.info(f"OTP verification attempt for phone: {phone_number[:3]}***{phone_number[-3:] if phone_number else 'None'}")
        
        if not phone_number or not otp_input:
            logger.warning(f"Missing required fields - phone_number: {bool(phone_number)}, otp: {bool(otp_input)}")
            return jsonify({'error': 'Phone number and OTP are required'}), 400
        
        # Check database connection
        if mongo_client is None or otp_collection is None or users_collection is None:
            if not connect_to_mongodb():
                return jsonify({'error': 'Database connection failed'}), 500
        
        # Find valid OTP
        current_time = datetime.now(timezone.utc)
        logger.info(f"Searching for OTP record - phone: {phone_number}, otp: {otp_input}, current_time: {current_time}")
        
        otp_record = otp_collection.find_one({
            'phone_number': phone_number,
            'otp': otp_input,
            'used': False,
            'expires_at': {'$gt': current_time}
        })
        
        if not otp_record:
            # Debug: Check if there's any OTP record for this phone number
            any_otp = otp_collection.find_one({'phone_number': phone_number})
            if any_otp:
                logger.warning(f"OTP record exists but conditions not met - used: {any_otp.get('used')}, expires_at: {any_otp.get('expires_at')}, submitted_otp: {otp_input}, stored_otp: {any_otp.get('otp')}")
            else:
                logger.warning(f"No OTP record found for phone number: {phone_number}")
            return jsonify({'error': 'Invalid or expired OTP'}), 400
        
        # Mark OTP as used
        otp_collection.update_one(
            {'_id': otp_record['_id']},
            {'$set': {'used': True}}
        )
        
        # Get user data
        logger.info(f"Looking up user data for phone: {phone_number}")
        user = users_collection.find_one({"wa_id": phone_number})
        if not user:
            logger.error(f"User not found in users_collection for phone: {phone_number}")
            return jsonify({'error': 'User not found'}), 404
        
        logger.info(f"User found: {user.get('owner_name', 'Unknown')} - {user.get('company_name', 'Unknown Company')}")
        
        # Create JWT token
        token = create_jwt_token(phone_number, user)
        
        # Return user info (without sensitive data)
        user_info = {
            'wa_id': user['wa_id'],
            'owner_name': user.get('owner_name', ''),
            'company_name': user.get('company_name', ''),
            'location': user.get('location', ''),
            'business_type': user.get('business_type', ''),
            'mode': user.get('mode', 'business'),  # Default to business mode if not set
            'language': user.get('language', 'en')  # Include language for UI localization
        }
        
        return jsonify({
            'message': 'Authentication successful',
            'token': token,
            'user': user_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error verifying OTP: {e}")
        return jsonify({'error': 'Failed to verify OTP'}), 500

# --- API Routes ---

@app.route('/api/dashboard/<wa_id>', methods=['GET'])
@token_required
def get_dashboard_data(wa_id):
    """Get dashboard data for a specific user."""
    try:
        logger.info(f"API request for dashboard data from wa_id {wa_id}")
        
        # Verify the requesting user matches the wa_id
        if request.current_user['wa_id'] != wa_id:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        # Get CCC metrics and financial data
        metrics = get_ccc_metrics(wa_id)
        
        if 'error' in metrics:
            return jsonify({
                'error': metrics['error'],
                'ccc': 0,
                'dso': 0,
                'dio': 0,
                'dpo': 0,
                'totalTransactions': 0,
                'recentTransactions': [],
                'summary': {
                    'totalSales': 0,
                    'totalPurchases': 0,
                    'totalPaymentsReceived': 0,
                    'totalPaymentsMade': 0
                }
            }), 200
        
        return jsonify(metrics), 200
        
    except Exception as e:
        logger.error(f"Error in dashboard API for wa_id {wa_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/personal-budget/<wa_id>', methods=['GET'])
@token_required
def get_personal_budget(wa_id):
    """Get personal budget data for a specific user."""
    try:
        logger.info(f"API request for personal budget data from wa_id {wa_id}")
        
        # Verify the requesting user matches the wa_id
        if request.current_user['wa_id'] != wa_id:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        # Get user data from MongoDB
        user_doc = db.users.find_one({'wa_id': wa_id})
        if not user_doc:
            return jsonify({'error': 'User not found'}), 404
        
        # Get transactions for the current month
        current_month = datetime.now().strftime('%Y-%m')
        query = {
            'wa_id': wa_id,
            'date_created': {'$regex': f'^{current_month}'}
        }
        logger.info(f"Querying transactions with: {query}")
        
        # Also check what transactions exist for this user
        all_user_transactions = list(db.entries.find({'wa_id': wa_id}))
        logger.info(f"Found {len(all_user_transactions)} total transactions for wa_id {wa_id}")
        if all_user_transactions:
            logger.info(f"Sample transaction: {all_user_transactions[0]}")
        
        transactions = list(db.entries.find(query))
        logger.info(f"Found {len(transactions)} transactions for current month {current_month}")
        
        # Calculate spending and income
        total_spending = 0
        total_income = 0
        categories = defaultdict(lambda: {'amount': 0, 'transactions': 0})
        
        for transaction in transactions:
            amount = abs(transaction.get('amount', 0))
            category = transaction.get('category', 'Other')
            action = transaction.get('action', '') or ''
            action = action.lower() if action else ''
            
            if action in ['purchase', 'expense', 'payment']:
                total_spending += amount
                categories[category]['amount'] += amount
                categories[category]['transactions'] += 1
            elif action in ['sale', 'income']:
                total_income += amount
        
        # Convert categories to array format with colors
        colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336', '#00BCD4', '#FFEB3B', '#795548']
        categories_array = []
        for i, (name, data) in enumerate(categories.items()):
            categories_array.append({
                'name': name,
                'amount': data['amount'],
                'transactions': data['transactions'],
                'color': colors[i % len(colors)]
            })
        
        # Sort by amount (highest first)
        categories_array.sort(key=lambda x: x['amount'], reverse=True)
        
        # Get monthly spending for the last 4 months
        monthly_spending = []
        for i in range(4):
            month_date = datetime.now() - timedelta(days=30*i)
            month_str = month_date.strftime('%Y-%m')
            month_name = month_date.strftime('%B %Y')
            
            month_transactions = list(db.entries.find({
                'wa_id': wa_id,
                'date_created': {'$regex': f'^{month_str}'},
                'action': {'$in': ['purchase', 'expense']}
            }))
            
            month_total = sum(abs(t.get('amount', 0)) for t in month_transactions)
            monthly_spending.append({
                'month': month_name,
                'amount': month_total,
                'transactions': len(month_transactions)
            })
        
        # Calculate balance
        balance = total_income - total_spending
        
        # Convert ObjectIds to strings for JSON serialization
        recent_transactions = []
        for transaction in (transactions[-10:] if transactions else []):
            tx = transaction.copy()
            if '_id' in tx:
                tx['_id'] = str(tx['_id'])
            recent_transactions.append(tx)
        
        budget_data = {
            'totalSpending': total_spending,
            'totalIncome': total_income,
            'balance': balance,
            'categories': categories_array,
            'monthlySpending': monthly_spending,
            'recentTransactions': recent_transactions
        }
        
        return jsonify(budget_data), 200
        
    except Exception as e:
        logger.error(f"Error in personal budget API for wa_id {wa_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Test MongoDB connection
        if mongo_client:
            mongo_client.admin.command('ping')
            db_status = "connected"
        else:
            db_status = "disconnected"
        
        return jsonify({
            'status': 'healthy',
            'database': db_status,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/api/debug/connection', methods=['GET'])
def debug_connection():
    """Debug endpoint to check API connectivity and security status."""
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    return jsonify({
        'message': 'API is reachable',
        'client_ip': client_ip,
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'security_active': True,
        'rate_limit_remaining': RATE_LIMIT_REQUESTS - len(request_counts.get(client_ip, [])),
        'path_tested': request.path,
        'method': request.method
    }), 200

@app.route('/api/download-excel/<wa_id>', methods=['GET'])
@token_required
def download_excel(wa_id):
    """Download all transactions for a user as Excel file."""
    try:
        if mongo_client is None or collection is None:
            if not connect_to_mongodb():
                return jsonify({'error': 'Database connection failed'}), 500
        
        # Get date range (optional query parameters)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Verify the requesting user matches the wa_id
        if request.current_user['wa_id'] != wa_id:
            return jsonify({'error': 'Unauthorized access'}), 403

        # Build query - support both Telegram (chat_id) and WhatsApp (wa_id) data
        query = {
            "$or": [
                {"chat_id": int(wa_id) if wa_id.isdigit() else 0},  # Try to convert to int for legacy chat_id
                {"wa_id": wa_id}  # WhatsApp IDs are strings
            ]
        }
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query['$gte'] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                date_query['$lte'] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            # Update the $or query to include timestamp filter
            query = {
                "$and": [
                    {
                        "$or": [
                            {"chat_id": int(wa_id) if wa_id.isdigit() else 0},
                            {"wa_id": wa_id}
                        ]
                    },
                    {"timestamp": date_query}
                ]
            }
        
        # Get transactions
        transactions = list(collection.find(query).sort('timestamp', -1))
        
        if not transactions:
            return jsonify({'error': 'No transactions found'}), 404
        
        # Prepare data for Excel
        excel_data = []
        for transaction in transactions:
            # Safely handle amount field
            amount = transaction.get('amount', 0)
            if amount is None:
                amount = 0
            
            # Safely handle COGS field
            cogs = transaction.get('cogs', '')
            if cogs is None:
                cogs = ''
            
            excel_data.append({
                'Date': transaction.get('timestamp', '').strftime('%Y-%m-%d %H:%M:%S') if transaction.get('timestamp') else '',
                'Action': transaction.get('action', ''),
                'Amount': amount,
                'Customer/Vendor': transaction.get('customer') or transaction.get('vendor', ''),
                'Items': transaction.get('items', ''),
                'Terms': transaction.get('terms', ''),
                'Description': transaction.get('description', ''),
                'COGS': cogs,
                'Has Image': 'Yes' if transaction.get('has_image', False) else 'No'
            })
        
        # Create DataFrame
        df = pd.DataFrame(excel_data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Write transactions to first sheet
            df.to_excel(writer, sheet_name='Transactions', index=False)
            
            # Get the workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Transactions']
            
            # Add formatting
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#4CAF50',
                'font_color': 'white',
                'border': 1
            })
            
            # Write headers with formatting
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Adjust column widths
            worksheet.set_column('A:A', 20)  # Date
            worksheet.set_column('B:B', 15)  # Action
            worksheet.set_column('C:C', 12)  # Amount
            worksheet.set_column('D:D', 25)  # Customer/Vendor
            worksheet.set_column('E:E', 30)  # Items
            worksheet.set_column('F:F', 12)  # Terms
            worksheet.set_column('G:G', 25)  # Description
            worksheet.set_column('H:H', 12)  # COGS
            worksheet.set_column('I:I', 12)  # Has Image
            
            # Add summary sheet
            def safe_sum(transactions, action_type):
                """Safely sum amounts, handling None values."""
                total = 0
                for t in transactions:
                    if t.get('action') == action_type:
                        amount = t.get('amount')
                        if amount is not None:
                            total += amount
                return total
            
            summary_data = {
                'Metric': ['Total Transactions', 'Total Sales', 'Total Purchases', 'Total Payments Received', 'Total Payments Made'],
                'Value': [
                    len(transactions),
                    safe_sum(transactions, 'sale'),
                    safe_sum(transactions, 'purchase'),
                    safe_sum(transactions, 'payment_received'),
                    safe_sum(transactions, 'payment_made')
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Format summary sheet
            summary_worksheet = writer.sheets['Summary']
            summary_worksheet.write(0, 0, 'Metric', header_format)
            summary_worksheet.write(0, 1, 'Value', header_format)
            summary_worksheet.set_column('A:A', 25)
            summary_worksheet.set_column('B:B', 20)
        
        output.seek(0)
        
        # Generate filename
        filename = f"transactions_user_{wa_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error generating Excel file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-excel/<wa_id>/purchase', methods=['GET'])
@token_required
def download_purchase_excel(wa_id):
    """Download purchase transactions for a user as Excel file."""
    return download_filtered_excel(wa_id, 'purchase')

@app.route('/api/download-excel/<wa_id>/sale', methods=['GET'])
@token_required
def download_sale_excel(wa_id):
    """Download sale transactions for a user as Excel file."""
    return download_filtered_excel(wa_id, 'sale')

def download_filtered_excel(wa_id, transaction_type):
    """Helper function to download filtered transactions as Excel."""
    try:
        if mongo_client is None or collection is None:
            if not connect_to_mongodb():
                return jsonify({'error': 'Database connection failed'}), 500
        
        # Get date range (optional query parameters)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Verify the requesting user matches the wa_id
        if request.current_user['wa_id'] != wa_id:
            return jsonify({'error': 'Unauthorized access'}), 403

        # Build query - support both Telegram (chat_id) and WhatsApp (wa_id) data
        query = {
            "$and": [
                {
                    "$or": [
                        {"chat_id": int(wa_id) if wa_id.isdigit() else 0},  # Try to convert to int for legacy chat_id
                        {"wa_id": wa_id}  # WhatsApp IDs are strings
                    ]
                },
                {"action": transaction_type}  # Filter by transaction type
            ]
        }
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query['$gte'] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                date_query['$lte'] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            # Add timestamp filter to the existing query
            query["$and"].append({"timestamp": date_query})
        
        # Get transactions
        transactions = list(collection.find(query).sort('timestamp', -1))
        
        if not transactions:
            return jsonify({'error': f'No {transaction_type} transactions found'}), 404
        
        # Prepare data for Excel
        excel_data = []
        for transaction in transactions:
            # Safely handle amount field
            amount = transaction.get('amount', 0)
            if amount is None:
                amount = 0
            
            # Safely handle COGS field
            cogs = transaction.get('cogs', '')
            if cogs is None:
                cogs = ''
            
            row_data = {
                'Date': transaction.get('timestamp', '').strftime('%Y-%m-%d %H:%M:%S') if transaction.get('timestamp') else '',
                'Action': transaction.get('action', ''),
                'Amount': amount,
                'Customer/Vendor': transaction.get('customer') or transaction.get('vendor', ''),
                'Items': transaction.get('items', ''),
                'Terms': transaction.get('terms', ''),
                'Description': transaction.get('description', ''),
                'Has Image': 'Yes' if transaction.get('has_image', False) else 'No'
            }
            
            # Add category column for purchase transactions
            if transaction_type == 'purchase':
                row_data['Category'] = transaction.get('category', 'Uncategorized')
            
            # Add COGS column for sale transactions
            if transaction_type == 'sale':
                row_data['COGS'] = cogs
            
            excel_data.append(row_data)
        
        # Create DataFrame
        df = pd.DataFrame(excel_data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Write transactions to sheet
            sheet_name = f'{transaction_type.title()} Transactions'
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Get the workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Add formatting
            header_color = '#FF9800' if transaction_type == 'purchase' else '#4CAF50'
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': header_color,
                'font_color': 'white',
                'border': 1
            })
            
            # Apply header formatting
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Set column widths
            worksheet.set_column('A:A', 20)  # Date
            worksheet.set_column('B:B', 12)  # Action
            worksheet.set_column('C:C', 15)  # Amount
            worksheet.set_column('D:D', 20)  # Customer/Vendor
            worksheet.set_column('E:E', 30)  # Items
            worksheet.set_column('F:F', 15)  # Terms
            worksheet.set_column('G:G', 30)  # Description
            if transaction_type == 'purchase':
                worksheet.set_column('H:H', 15)  # Category
                worksheet.set_column('I:I', 12)  # Has Image
            else:
                worksheet.set_column('H:H', 15)  # COGS
                worksheet.set_column('I:I', 12)  # Has Image
        
        output.seek(0)
        
        # Create response
        filename = f'{transaction_type}_transactions_{wa_id}_{datetime.now().strftime("%Y%m%d")}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error generating {transaction_type} Excel file: {e}")
        return jsonify({'error': f'Failed to generate {transaction_type} Excel file'}), 500

def get_user_identifier(user_id):
    """Get the correct identifier field name for database queries."""
    # For WhatsApp IDs (which are strings), use 'wa_id'
    # For Telegram IDs (which are integers), use 'chat_id'
    if isinstance(user_id, str) or (isinstance(user_id, int) and len(str(user_id)) > 10):
        return 'wa_id'
    else:
        return 'chat_id'

@app.route('/api/transactions/<user_id>', methods=['GET'])
@token_required
def get_user_transactions(user_id):
    """Get all transactions for a specific user."""
    try:
        if mongo_client is None or collection is None:
            if not connect_to_mongodb():
                return jsonify({'error': 'Database connection failed'}), 500
        
        # Verify user has access to this data
        if request.current_user['wa_id'] != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get all transactions for the user
        user_identifier = get_user_identifier(user_id)
        transactions = list(collection.find({
            user_identifier: user_id
        }).sort('timestamp', -1))
        
        # Convert ObjectId to string for JSON serialization
        for transaction in transactions:
            transaction['_id'] = str(transaction['_id'])
        
        return jsonify({
            'transactions': transactions,
            'total': len(transactions)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/transactions/<transaction_id>', methods=['PUT'])
@token_required
def update_transaction(transaction_id):
    """Update a specific transaction."""
    try:
        if mongo_client is None or collection is None:
            if not connect_to_mongodb():
                return jsonify({'error': 'Database connection failed'}), 500
        
        data = request.get_json()
        
        # Find the transaction first to verify ownership
        transaction = collection.find_one({'_id': ObjectId(transaction_id)})
        
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        # Verify user has access to this transaction
        user_identifier = get_user_identifier(request.current_user['wa_id'])
        if transaction.get(user_identifier) != request.current_user['wa_id']:
            return jsonify({'error': 'Access denied'}), 403
        
        # Update the transaction
        update_data = {
            'action': data.get('action', transaction['action']),
            'amount': float(data.get('amount', transaction['amount'])),
            'description': data.get('description', transaction['description']),
            'vendor': data.get('vendor', transaction.get('vendor')),
            'terms': data.get('terms', transaction.get('terms')),
            'updated_at': datetime.now(timezone.utc)
        }
        
        # Handle category for purchase transactions
        if 'category' in data:
            update_data['category'] = data['category']
        
        # Update date if provided
        if data.get('date'):
            try:
                update_data['date'] = data['date']
                # Also update timestamp to match the date
                date_obj = datetime.strptime(data['date'], '%Y-%m-%d')
                update_data['timestamp'] = date_obj.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        
        result = collection.update_one(
            {'_id': ObjectId(transaction_id)},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            # Get the updated transaction
            updated_transaction = collection.find_one({'_id': ObjectId(transaction_id)})
            updated_transaction['_id'] = str(updated_transaction['_id'])
            
            return jsonify({
                'message': 'Transaction updated successfully',
                'transaction': updated_transaction
            }), 200
        else:
            return jsonify({'error': 'Failed to update transaction'}), 500
        
    except Exception as e:
        logger.error(f"Error updating transaction: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/transactions/<transaction_id>', methods=['DELETE'])
@token_required
def delete_transaction(transaction_id):
    """Delete a specific transaction."""
    try:
        if mongo_client is None or collection is None:
            if not connect_to_mongodb():
                return jsonify({'error': 'Database connection failed'}), 500
        
        # Find the transaction first to verify ownership
        transaction = collection.find_one({'_id': ObjectId(transaction_id)})
        
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        # Verify user has access to this transaction
        user_identifier = get_user_identifier(request.current_user['wa_id'])
        if transaction.get(user_identifier) != request.current_user['wa_id']:
            return jsonify({'error': 'Access denied'}), 403
        
        # Delete the transaction
        result = collection.delete_one({'_id': ObjectId(transaction_id)})
        
        if result.deleted_count > 0:
            return jsonify({'message': 'Transaction deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete transaction'}), 500
        
    except Exception as e:
        logger.error(f"Error deleting transaction: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/transactions', methods=['POST'])
@token_required
def add_transaction():
    """Add a new transaction."""
    try:
        if mongo_client is None or collection is None:
            if not connect_to_mongodb():
                return jsonify({'error': 'Database connection failed'}), 500
        
        data = request.get_json()
        
        # Create transaction document
        user_identifier = get_user_identifier(request.current_user['wa_id'])
        transaction = {
            user_identifier: request.current_user['wa_id'],
            'action': data.get('type', 'sale'),
            'amount': float(data.get('amount', 0)),
            'description': data.get('description', ''),
            'vendor': data.get('category', ''),  # Using category as vendor for manual entries
            'terms': data.get('paymentMethod', 'cash'),
            'timestamp': datetime.now(timezone.utc),
            'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'has_image': False,  # Manual entries don't have images for now
            'created_via': 'dashboard'
        }
        
        # Insert the transaction
        result = collection.insert_one(transaction)
        
        if result.inserted_id:
            transaction['_id'] = str(result.inserted_id)
            return jsonify({
                'message': 'Transaction added successfully',
                'transaction': transaction
            }), 201
        else:
            return jsonify({'error': 'Failed to add transaction'}), 500
        
    except Exception as e:
        logger.error(f"Error adding transaction: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/categorize', methods=['POST'])
@token_required
def categorize_transaction():
    """Use AI to categorize a purchase transaction."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        description = data.get('description', '')
        vendor = data.get('vendor', '')
        amount = data.get('amount', 0)
        
        if not description:
            return jsonify({'error': 'Description is required for categorization'}), 400
        
        # Use AI to categorize the transaction
        category = categorize_purchase_with_ai(description, vendor, amount)
        
        return jsonify({
            'category': category,
            'message': f'Transaction categorized as {category}'
        }), 200
        
    except Exception as e:
        logger.error(f"Error categorizing transaction: {e}")
        return jsonify({'error': 'Failed to categorize transaction'}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get list of users (chat_ids) for testing."""
    try:
        if mongo_client is None or collection is None:
            if not connect_to_mongodb():
                return jsonify({'error': 'Database connection failed'}), 500
        
        # Get unique chat_ids (Telegram) and wa_ids (WhatsApp)
        chat_ids = collection.distinct('chat_id')
        wa_ids = collection.distinct('wa_id')
        
        # Convert WhatsApp IDs to integers for consistent frontend handling
        wa_ids_as_int = []
        for wa_id in wa_ids:
            if wa_id:  # Skip None values
                try:
                    # Convert WhatsApp phone number to integer for frontend compatibility
                    wa_ids_as_int.append(int(wa_id))
                except (ValueError, TypeError):
                    # If conversion fails, skip this wa_id
                    continue
        
        # Combine both lists and remove duplicates
        all_users = list(set(chat_ids + wa_ids_as_int))
        all_users.sort()  # Sort for consistent ordering
        
        return jsonify({
            'users': all_users,
            'count': len(all_users),
            'telegram_users': len(chat_ids),
            'whatsapp_users': len(wa_ids_as_int)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({'error': str(e)}), 500

# Initialize MongoDB connection on startup
connect_to_mongodb()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
