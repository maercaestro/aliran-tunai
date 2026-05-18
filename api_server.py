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
import threading
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

# Cap inbound bodies (defends against memory-exhaustion uploads).
# Receipts go through the WhatsApp service; this API mostly handles JSON.
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 4 * 1024 * 1024))

# CORS origins are env-driven so we don't ship localhost in prod.
# CORS_ALLOWED_ORIGINS="https://flow-ai.biz,https://aliran-tunai.com"
_default_origins = 'https://aliran-tunai.com,https://flow-ai.biz,http://localhost:5173,http://localhost:3000'
_cors_origins = [
    o.strip() for o in os.getenv('CORS_ALLOWED_ORIGINS', _default_origins).split(',')
    if o.strip()
]
CORS(app,
     origins=_cors_origins,
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     supports_credentials=True)
logger.info(f"CORS configured for origins: {_cors_origins}")

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

# Rate limiting storage. NOTE: process-local; with multiple gunicorn workers
# the effective limit is RATE_LIMIT_REQUESTS * N. Move to Redis (or nginx
# limit_req zone) before scaling beyond a single instance.
request_counts = defaultdict(list)
_rate_limit_lock = threading.Lock()
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '200'))
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '60'))
AUTH_RATE_LIMIT_REQUESTS = int(os.getenv('AUTH_RATE_LIMIT_REQUESTS', '20'))
_RATE_LIMIT_MAX_KEYS = 10_000  # cap memory; evict oldest beyond this

def is_malicious_request(path):
    """Check if the request path matches known malicious patterns."""
    for pattern in MALICIOUS_PATTERNS:
        if re.search(pattern, path, re.IGNORECASE):
            return True
    return False

def check_rate_limit(client_ip, limit=None):
    """Sliding-window rate limit per client IP.

    Pass `limit` to override the global RATE_LIMIT_REQUESTS (e.g. a tighter
    cap on /api/auth/* endpoints).
    """
    if limit is None:
        limit = RATE_LIMIT_REQUESTS
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW
    with _rate_limit_lock:
        # Bound dict growth: drop ~half the keys with no recent activity.
        if len(request_counts) > _RATE_LIMIT_MAX_KEYS:
            stale = [k for k, ts in request_counts.items() if not ts or ts[-1] < cutoff]
            for k in stale[: len(stale) or 1]:
                request_counts.pop(k, None)

        bucket = [t for t in request_counts[client_ip] if t > cutoff]
        if len(bucket) >= limit:
            request_counts[client_ip] = bucket
            return False
        bucket.append(now)
        request_counts[client_ip] = bucket
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
    
    # Rate limiting (tighter cap on auth endpoints to slow OTP brute force)
    rate_limit = AUTH_RATE_LIMIT_REQUESTS if request.path.startswith('/api/auth/') else RATE_LIMIT_REQUESTS

    if not check_rate_limit(client_ip, limit=rate_limit):
        logger.warning(f"Rate limit exceeded for IP: {client_ip} on path: {request.path} (limit={rate_limit}/{RATE_LIMIT_WINDOW}s)")
        abort(429)  # Too Many Requests
    
    # Block malicious requests
    if is_malicious_request(request.path):
        logger.warning(f"Blocked malicious request from {client_ip}: {request.path}")
        abort(404)  # Return 404 instead of revealing server info
    
    # Log all incoming requests for debugging
    logger.info(f"Request: {request.method} {request.path} from {client_ip} - User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
    
    # Detailed logging for API requests (with sensitive headers redacted).
    if request.path.startswith('/api/') or request.path.startswith('/whatsapp/'):
        if logger.isEnabledFor(logging.DEBUG):
            redacted_headers = {
                k: ('<redacted>' if k.lower() in {'authorization', 'cookie', 'x-api-key', 'proxy-authorization'} else v)
                for k, v in request.headers.items()
            }
            logger.debug(f"API request: {request.method} {request.path} headers={redacted_headers}")
        if request.is_json and request.path.startswith('/api/auth/'):
            # Log auth requests (without sensitive data)
            data = request.get_json(silent=True) or {}
            safe_data = {k: v if k != 'phone_number' else f"{v[:3]}***{v[-3:]}" if v else None for k, v in data.items() if k not in {'otp', 'password', 'token'}}
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
    # Minimal auth-endpoint logging without exposing tokens.
    if request.path.startswith('/api/auth/') and response.status_code == 200:
        logger.info(f"Auth OK: {request.method} {request.path}")

    return response

# --- MongoDB Connection ---
MONGO_URI = os.getenv("MONGO_URI")

# JWT Configuration -- fail fast if missing or too short. We refuse to boot
# with the legacy default to avoid silently signing tokens with a known key.
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY or JWT_SECRET_KEY == "your-secret-key-change-in-production":
    raise RuntimeError(
        "JWT_SECRET_KEY environment variable is required and must not be the default. "
        "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(48))'"
    )
if len(JWT_SECRET_KEY) < 32:
    raise RuntimeError("JWT_SECRET_KEY must be at least 32 characters long")

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
waitlist_collection = None

def connect_to_mongodb():
    """Connect to MongoDB with retry logic and better error handling."""
    global mongo_client, db, collection, users_collection, otp_collection, waitlist_collection
    
    if not MONGO_URI:
        logger.error("MONGO_URI environment variable not set!")
        return False
    
    try:
        logger.info("Attempting to connect to MongoDB...")
        
        # Connection options. PyMongo handles reconnection internally so we
        # only need a single well-tuned client; the list keeps a fallback for
        # quirky network setups.
        common_pool = {
            "maxPoolSize": int(os.getenv('MONGO_MAX_POOL_SIZE', '50')),
            "minPoolSize": int(os.getenv('MONGO_MIN_POOL_SIZE', '5')),
            "maxIdleTimeMS": 60_000,
            "retryWrites": True,
            "w": "majority",
            "serverSelectionTimeoutMS": 5000,
            "connectTimeoutMS": 10000,
            "socketTimeoutMS": 60000,
        }
        connection_options = [
            # Option 1: Fixed SSL/TLS configuration
            {**common_pool, "tls": True, "tlsAllowInvalidCertificates": False, "tlsAllowInvalidHostnames": False},
            # Option 2: Server API
            {**common_pool, "server_api": ServerApi('1')},
            # Option 3: Minimal fallback
            {"serverSelectionTimeoutMS": 5000},
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
                waitlist_collection = db.waitlist

                # Best-effort schema-side hardening. These are idempotent.
                try:
                    _ensure_indexes()
                except Exception as ie:  # don't fail boot on index errors
                    logger.warning(f"Index creation skipped: {ie}")

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
        waitlist_collection = None
        return False

# --- Authentication Functions ---
# OTP rate limits (per phone number)
OTP_REQUEST_COOLDOWN_SECONDS = int(os.getenv('OTP_REQUEST_COOLDOWN_SECONDS', '60'))
OTP_REQUEST_MAX_PER_HOUR = int(os.getenv('OTP_REQUEST_MAX_PER_HOUR', '5'))
OTP_VERIFY_MAX_ATTEMPTS = int(os.getenv('OTP_VERIFY_MAX_ATTEMPTS', '5'))


def _ensure_indexes() -> None:
    """Create the small set of indexes the app relies on. Idempotent."""
    if otp_collection is not None:
        # Auto-expire OTPs once expires_at passes (Mongo TTL monitor)
        otp_collection.create_index('expires_at', expireAfterSeconds=0, background=True)
        otp_collection.create_index([('phone_number', 1), ('created_at', -1)], background=True)
    if users_collection is not None:
        users_collection.create_index('wa_id', unique=True, background=True)
        # users_collection.create_index('phone_number', background=True)  # legacy field
    if collection is not None:
        collection.create_index([('wa_id', 1), ('timestamp', -1)], background=True)
        collection.create_index([('chat_id', 1), ('timestamp', -1)], background=True)
    if waitlist_collection is not None:
        # Dedupe entries by normalised phone / email and let us query by status.
        waitlist_collection.create_index('whatsapp_normalised', background=True)
        waitlist_collection.create_index('email_normalised', background=True)
        waitlist_collection.create_index([('status', 1), ('created_at', -1)], background=True)
    logger.info("Mongo indexes ensured (otp TTL, users.wa_id unique, entries compound, waitlist)")


def generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))

def send_whatsapp_otp(to_phone_number: str, otp_code: str) -> bool:
    """Send OTP via WhatsApp using Authentication Template."""
    try:
        if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
            logger.error("WhatsApp configuration missing")
            return False
        
        url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        
        headers = {
            'Authorization': f'Bearer {WHATSAPP_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Use Authentication Template for OTP delivery
        payload = {
            'messaging_product': 'whatsapp',
            'to': to_phone_number,
            'type': 'template',
            'template': {
                'name': 'otp_login',  # Your template name (update if different)
                'language': {
                    'code': 'en'
                },
                'components': [
                    {
                        'type': 'body',
                        'parameters': [
                            {
                                'type': 'text',
                                'text': otp_code  # Only the OTP code
                            }
                        ]
                    },
                    {
                        'type': 'button',
                        'sub_type': 'url',
                        'index': 0,
                        'parameters': [
                            {
                                'type': 'text',
                                'text': otp_code  # For the button parameter
                            }
                        ]
                    }
                ]
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
        logger.error(f"Error sending WhatsApp OTP: {e}")
        return False

def send_whatsapp_message(to_phone_number: str, message: str) -> bool:
    """Send WhatsApp message using Business API (for non-OTP messages)."""
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
            logger.error("Failed to connect to MongoDB for CCC metrics.")
            if os.getenv('ENABLE_MOCK_FALLBACK', 'false').lower() == 'true':
                return get_mock_ccc_data(int(user_id) if user_id.isdigit() else 123456)
            return {'error': 'Database unavailable', 'database_status': 'disconnected'}
    
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
        if os.getenv('ENABLE_MOCK_FALLBACK', 'false').lower() == 'true':
            logger.info("Fallback to mock data due to database error")
            return get_mock_ccc_data(int(user_id) if user_id.isdigit() else 123456)
        return {'error': f'Failed to compute metrics: {e}', 'database_status': 'error'}

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
            model="gpt-5-mini",
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

If you receive this, WhatsApp integration is working correctly!"""
        
        success = send_whatsapp_message(phone_number, test_message)
        
        return jsonify({
            'success': success,
            'message': 'Test message sent' if success else 'Failed to send test message',
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

        # Per-phone OTP request throttling (defense against OTP spam / SMS-bomb)
        now_utc = datetime.now(timezone.utc)
        cooldown_since = now_utc - timedelta(seconds=OTP_REQUEST_COOLDOWN_SECONDS)
        hour_since = now_utc - timedelta(hours=1)
        recent = otp_collection.find_one(
            {'phone_number': phone_number, 'created_at': {'$gt': cooldown_since}},
            sort=[('created_at', -1)],
        )
        if recent:
            return jsonify({'error': f'Please wait {OTP_REQUEST_COOLDOWN_SECONDS} seconds before requesting another OTP.'}), 429
        hourly = otp_collection.count_documents({'phone_number': phone_number, 'created_at': {'$gt': hour_since}})
        if hourly >= OTP_REQUEST_MAX_PER_HOUR:
            logger.warning(f"OTP hourly cap hit for {phone_number}")
            return jsonify({'error': 'Too many OTP requests. Please try again later.'}), 429

        # Generate OTP
        otp_code = generate_otp()

        # Store OTP in database with expiration (5 minutes)
        otp_data = {
            'phone_number': phone_number,
            'otp': otp_code,
            'created_at': now_utc,
            'expires_at': now_utc + timedelta(minutes=5),
            'used': False,
            'attempts': 0,
        }
        
        otp_collection.insert_one(otp_data)
        
        # Send OTP via WhatsApp using Authentication Template
        whatsapp_sent = send_whatsapp_otp(phone_number, otp_code)
        
        if whatsapp_sent:
            logger.info(f"OTP sent via WhatsApp template to {phone_number}")
            return jsonify({
                'message': 'OTP sent successfully via WhatsApp'
            }), 200
        else:
            # Log the OTP for debugging if WhatsApp fails
            logger.warning(f"WhatsApp template delivery failed for {phone_number}. OTP: {otp_code}")
            return jsonify({
                'error': 'Failed to send OTP. Please try again later.'
            }), 500
        
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
        
        # Find the most recent unexpired OTP record for this phone, regardless
        # of whether the submitted code matches. We want to count attempts on
        # the *issued* code so an attacker can't try unlimited values.
        current_time = datetime.now(timezone.utc)
        active_otp = otp_collection.find_one(
            {'phone_number': phone_number, 'used': False, 'expires_at': {'$gt': current_time}},
            sort=[('created_at', -1)],
        )

        if not active_otp:
            logger.warning(f"No active OTP for phone: {phone_number}")
            return jsonify({'error': 'Invalid or expired OTP'}), 400

        # Check + increment attempt counter atomically. If the limit was
        # already hit on a previous attempt, refuse without revealing why.
        if active_otp.get('attempts', 0) >= OTP_VERIFY_MAX_ATTEMPTS:
            logger.warning(f"OTP verify attempts exhausted for {phone_number}")
            otp_collection.update_one({'_id': active_otp['_id']}, {'$set': {'used': True}})
            return jsonify({'error': 'Invalid or expired OTP'}), 400

        otp_collection.update_one({'_id': active_otp['_id']}, {'$inc': {'attempts': 1}})

        if active_otp.get('otp') != otp_input:
            logger.warning(f"Wrong OTP submitted for {phone_number} (attempt {active_otp.get('attempts', 0) + 1})")
            return jsonify({'error': 'Invalid or expired OTP'}), 400

        otp_record = active_otp
        
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

# DEMO MODE: Public endpoint without authentication
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get aggregated dashboard data for all users (DEMO MODE - No Auth)."""
    try:
        logger.info("API request for dashboard stats (all users - DEMO MODE)")
        
        if mongo_client is None or collection is None:
            if not connect_to_mongodb():
                logger.error("Database connection failed - using demo data")
                # Return demo data if DB connection fails
                return jsonify({
                    'totalTransactions': 15,
                    'recentTransactions': [
                        {
                            '_id': 'demo1',
                            'wa_id': 'demo_user',
                            'action': 'sale',
                            'amount': 2500.00,
                            'description': 'Website design project',
                            'vendor': 'Client ABC',
                            'terms': 'net30',
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'date_created': datetime.now().strftime('%Y-%m-%d')
                        },
                        {
                            '_id': 'demo2',
                            'wa_id': 'demo_user',
                            'action': 'purchase',
                            'amount': 850.00,
                            'description': 'Office supplies',
                            'vendor': 'Supplier XYZ',
                            'terms': 'net15',
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'date_created': datetime.now().strftime('%Y-%m-%d')
                        }
                    ],
                    'ccc': 45,
                    'dso': 28,
                    'dio': 15,
                    'dpo': 32,
                    'balance': 12500.50,
                    'totalIncome': 25000.00,
                    'totalSpending': 12499.50,
                    'categories': [
                        {'name': 'Services', 'amount': 15000, 'percentage': 60},
                        {'name': 'Supplies', 'amount': 6000, 'percentage': 24},
                        {'name': 'Equipment', 'amount': 4000, 'percentage': 16}
                    ],
                    'monthlySpending': [
                        {'month': 'Jan', 'amount': 3500},
                        {'month': 'Feb', 'amount': 4200},
                        {'month': 'Mar', 'amount': 4799.50}
                    ],
                    'summary': {
                        'totalSales': 25000.00,
                        'totalPurchases': 12499.50,
                        'totalPaymentsReceived': 18000.00,
                        'totalPaymentsMade': 10000.00
                    }
                }), 200
        
        # Get all transactions across all users from correct collection
        all_transactions = list(collection.find().sort('timestamp', -1).limit(50))
        
        # Get recent transactions formatted
        recent_transactions = []
        for txn in all_transactions[:10]:
            recent_transactions.append({
                '_id': str(txn['_id']),
                'wa_id': txn.get('wa_id', txn.get('chat_id', '')),
                'action': txn.get('action', ''),
                'amount': txn.get('amount', 0),
                'description': txn.get('description', ''),
                'vendor': txn.get('vendor', ''),
                'customer': txn.get('customer', ''),
                'category': txn.get('category', ''),
                'terms': txn.get('terms', ''),
                'timestamp': txn.get('timestamp', ''),
                'date_created': txn.get('date_created', ''),
                'time_created': txn.get('time_created', ''),
                'items': txn.get('items', ''),
                'detected_language': txn.get('detected_language', 'en')
            })
        
        # Calculate basic stats from actual data
        total_transactions = collection.count_documents({})
        
        # Calculate totals
        total_sales = 0
        total_purchases = 0
        total_payments_received = 0
        total_payments_made = 0
        
        for txn in all_transactions:
            amount = txn.get('amount', 0)
            action = txn.get('action', '')
            
            # Handle None values
            if action is None:
                continue
            
            action = action.lower()
            
            if action == 'sale':
                total_sales += amount
            elif action == 'purchase':
                total_purchases += amount
            elif action == 'payment_received':
                total_payments_received += amount
            elif action == 'payment_made':
                total_payments_made += amount
        
        balance = total_sales - total_purchases + total_payments_received - total_payments_made
        
        # Demo CCC metrics (would need actual calculation for production)
        return jsonify({
            'totalTransactions': total_transactions,
            'recentTransactions': recent_transactions,
            'ccc': 45,  # Demo value
            'dso': 28,  # Demo value
            'dio': 15,  # Demo value
            'dpo': 32,  # Demo value
            'balance': balance,
            'totalIncome': total_sales + total_payments_received,
            'totalSpending': total_purchases + total_payments_made,
            'categories': [],
            'monthlySpending': [],
            'summary': {
                'totalSales': total_sales,
                'totalPurchases': total_purchases,
                'totalPaymentsReceived': total_payments_received,
                'totalPaymentsMade': total_payments_made
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in dashboard stats API: {e}")
        return jsonify({'error': str(e)}), 500

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

@app.route('/api/transactions', methods=['GET'])
def get_all_transactions():
    """Get all transactions (public endpoint for demo)."""
    try:
        if mongo_client is None or collection is None:
            if not connect_to_mongodb():
                return jsonify({'error': 'Database connection failed'}), 500
        
        # Get all transactions
        transactions = list(collection.find({}).sort('timestamp', -1).limit(100))
        
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

@app.route('/api/transactions/<user_id>', methods=['GET'])
@token_required
def get_user_transactions(user_id):
    """Get all transactions for a specific user with pagination."""
    try:
        if mongo_client is None or collection is None:
            if not connect_to_mongodb():
                return jsonify({'error': 'Database connection failed'}), 500
        
        # Verify user has access to this data
        if request.current_user['wa_id'] != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get pagination parameters from query string
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))  # Default to 10 for faster initial load
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:  # Max 100 items per page
            limit = 10
        
        # Calculate skip value
        skip = (page - 1) * limit
        
        # Get user identifier
        user_identifier = get_user_identifier(user_id)
        query = {user_identifier: user_id}
        
        # Get paginated transactions first (faster)
        transactions = list(collection.find(query)
                          .sort('timestamp', -1)
                          .skip(skip)
                          .limit(limit))
        
        # Get total count only if needed (for first page or if specifically requested)
        # Use a faster estimation method
        if page == 1:
            # For first page, just check if there are more documents
            total_count = skip + len(transactions) + (1 if len(transactions) == limit else 0)
        else:
            # For subsequent pages, do the actual count
            total_count = collection.count_documents(query)
        
        # Convert ObjectId to string for JSON serialization
        for transaction in transactions:
            transaction['_id'] = str(transaction['_id'])
        
        # Calculate pagination metadata
        total_pages = (total_count + limit - 1) // limit  # Ceiling division
        has_more = page < total_pages
        
        return jsonify({
            'transactions': transactions,
            'pagination': {
                'currentPage': page,
                'totalPages': total_pages,
                'totalCount': total_count,
                'limit': limit,
                'hasMore': has_more
            }
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


# ----------------------------------------------------------------------------
# Waiting-list survey endpoints
# ----------------------------------------------------------------------------
# These power the pre-launch landing page (see frontend WelcomePage +
# WaitlistSurvey). Submissions are stored in `db.waitlist` and can be
# exported as CSV by an admin holding ADMIN_TOKEN.

# Allowed survey question IDs (keep in sync with frontend/src/config/survey.js).
# We accept everything but only persist these known keys to avoid arbitrary
# blob ingestion.
_WAITLIST_KNOWN_KEYS = {
    'cash_sync_feeling',
    'ccc_tracking_method',
    'affordable_bookkeeper_salary',
    'most_useful_feature',
    'price_too_expensive',
    'price_too_cheap',
    'price_getting_expensive',
    'price_good_value',
    'industry',
    'industry_other',
    'monthly_transactions',
    'name',
    'whatsapp',
    'email',
    'business_name',
}
_WAITLIST_REQUIRED_KEYS = {
    'cash_sync_feeling',
    'ccc_tracking_method',
    'affordable_bookkeeper_salary',
    'most_useful_feature',
    'price_too_expensive',
    'price_too_cheap',
    'price_getting_expensive',
    'price_good_value',
    'industry',
    'monthly_transactions',
    'name',
    'whatsapp',
}
_WAITLIST_MAX_VALUE_LEN = 1000
_EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


def _normalise_phone(raw):
    """Strip spaces/dashes/+ from a phone number; return digits only or None."""
    if not raw:
        return None
    digits = re.sub(r'[^0-9]', '', str(raw))
    return digits or None


def _normalise_email(raw):
    if not raw:
        return None
    return str(raw).strip().lower()


@app.route('/api/waitlist/survey', methods=['GET'])
def get_waitlist_survey_meta():
    """Lightweight metadata so the client can confirm which survey version is live.

    The actual question schema is shipped with the frontend bundle
    (frontend/src/config/survey.js) for fast loads. This endpoint exists so we
    can later A/B test or version surveys server-side without redeploying FE.
    """
    return jsonify({
        'survey_id': 'flow-waitlist-v1',
        'accepting_submissions': True,
    }), 200


@app.route('/api/waitlist', methods=['POST'])
def submit_waitlist():
    """Persist a waiting-list survey submission."""
    try:
        if waitlist_collection is None:
            if not connect_to_mongodb() or waitlist_collection is None:
                return jsonify({'error': 'Database connection failed'}), 500

        payload = request.get_json(silent=True) or {}
        answers_in = payload.get('answers') or {}
        if not isinstance(answers_in, dict):
            return jsonify({'error': 'Invalid payload: answers must be an object'}), 400

        # Whitelist + truncate values defensively.
        answers = {}
        for k, v in answers_in.items():
            if k not in _WAITLIST_KNOWN_KEYS:
                continue
            if isinstance(v, str):
                v = v.strip()[:_WAITLIST_MAX_VALUE_LEN]
            elif isinstance(v, (int, float, bool)) or v is None:
                pass
            elif isinstance(v, list):
                v = [str(x)[:200] for x in v[:20]]
            else:
                v = str(v)[:_WAITLIST_MAX_VALUE_LEN]
            answers[k] = v

        # Required-field check.
        missing = [k for k in _WAITLIST_REQUIRED_KEYS if not answers.get(k) and answers.get(k) != 0]
        if missing:
            return jsonify({
                'error': 'Missing required fields',
                'missing': missing,
            }), 400

        # Field-level validation.
        email = answers.get('email')
        if email and not _EMAIL_RE.match(email):
            return jsonify({'error': 'Invalid email format'}), 400

        phone_norm = _normalise_phone(answers.get('whatsapp'))
        if not phone_norm or len(phone_norm) < 7 or len(phone_norm) > 15:
            return jsonify({'error': 'Invalid WhatsApp number'}), 400

        email_norm = _normalise_email(email)

        # Dedupe: same phone OR same email already on the list.
        dedupe_query = {'$or': [{'whatsapp_normalised': phone_norm}]}
        if email_norm:
            dedupe_query['$or'].append({'email_normalised': email_norm})
        if waitlist_collection.find_one(dedupe_query, {'_id': 1}):
            return jsonify({
                'error': 'already_registered',
                'message': 'Anda sudah berada dalam waiting list. Terima kasih!',
            }), 409

        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        # Only keep the first hop if behind multiple proxies.
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()

        doc = {
            'survey_id': payload.get('survey_id') or 'flow-waitlist-v1',
            'answers': answers,
            'whatsapp_normalised': phone_norm,
            'email_normalised': email_norm,
            'status': 'pending',  # pending -> invited -> converted
            'wa_id': None,
            'source': 'landing',
            'ip': client_ip,
            'user_agent': request.headers.get('User-Agent', '')[:300],
            'created_at': datetime.now(timezone.utc),
            'invited_at': None,
            'converted_at': None,
        }
        result = waitlist_collection.insert_one(doc)

        # Best-effort position number (total count = current position).
        try:
            position = waitlist_collection.count_documents({})
        except Exception:
            position = None

        logger.info(
            f"Waitlist signup: id={result.inserted_id} phone={phone_norm[:3]}***{phone_norm[-2:]} "
            f"industry={answers.get('industry')} position={position}"
        )

        return jsonify({
            'success': True,
            'id': str(result.inserted_id),
            'position': position,
        }), 201

    except Exception as e:
        logger.error(f"Error submitting waitlist: {e}", exc_info=True)
        return jsonify({'error': 'Failed to submit waitlist entry'}), 500


def _check_admin_token():
    """Return True iff the request carries a valid admin token."""
    expected = os.getenv('ADMIN_TOKEN')
    if not expected:
        # Fail closed: no token configured = endpoint disabled.
        return False
    provided = (
        request.headers.get('X-Admin-Token')
        or request.args.get('token')
        or ''
    )
    # Constant-time compare to avoid timing oracles.
    import hmac
    return hmac.compare_digest(str(provided), str(expected))


@app.route('/api/admin/waitlist', methods=['GET'])
def admin_list_waitlist():
    """Return the latest waiting-list entries (admin only)."""
    if not _check_admin_token():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        if waitlist_collection is None and not connect_to_mongodb():
            return jsonify({'error': 'Database connection failed'}), 500

        limit = min(int(request.args.get('limit', 100)), 1000)
        status = request.args.get('status')
        query = {'status': status} if status else {}

        cursor = (
            waitlist_collection
            .find(query)
            .sort('created_at', -1)
            .limit(limit)
        )
        entries = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            if doc.get('created_at'):
                doc['created_at'] = doc['created_at'].isoformat()
            if doc.get('invited_at'):
                doc['invited_at'] = doc['invited_at'].isoformat()
            if doc.get('converted_at'):
                doc['converted_at'] = doc['converted_at'].isoformat()
            entries.append(doc)
        return jsonify({'count': len(entries), 'entries': entries}), 200
    except Exception as e:
        logger.error(f"Error listing waitlist: {e}")
        return jsonify({'error': 'Failed to list waitlist'}), 500


@app.route('/api/admin/waitlist/export.csv', methods=['GET'])
def admin_export_waitlist_csv():
    """CSV export of every waiting-list submission (admin only)."""
    if not _check_admin_token():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        if waitlist_collection is None and not connect_to_mongodb():
            return jsonify({'error': 'Database connection failed'}), 500

        # Flatten answers into top-level columns for spreadsheet-friendly CSV.
        rows = []
        for doc in waitlist_collection.find({}).sort('created_at', -1):
            answers = doc.get('answers') or {}
            row = {
                'id': str(doc.get('_id')),
                'created_at': doc.get('created_at').isoformat() if doc.get('created_at') else '',
                'status': doc.get('status'),
                'wa_id': doc.get('wa_id'),
                'source': doc.get('source'),
                'ip': doc.get('ip'),
            }
            for key in sorted(_WAITLIST_KNOWN_KEYS):
                val = answers.get(key)
                if isinstance(val, list):
                    val = '|'.join(str(x) for x in val)
                row[key] = val
            rows.append(row)

        df = pd.DataFrame(rows)
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        bytes_buf = io.BytesIO(buf.getvalue().encode('utf-8'))
        ts = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
        return send_file(
            bytes_buf,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'waitlist-{ts}.csv',
        )
    except Exception as e:
        logger.error(f"Error exporting waitlist CSV: {e}")
        return jsonify({'error': 'Failed to export waitlist'}), 500


# Initialize MongoDB connection on startup
connect_to_mongodb()

if __name__ == '__main__':
    # Local-development entrypoint. In production we run under gunicorn:
    #   gunicorn --workers 4 --threads 8 --timeout 60 --bind 0.0.0.0:5001 api_server:app
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5001')), debug=debug)
