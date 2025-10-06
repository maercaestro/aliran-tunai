from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
import logging
import pandas as pd
import io

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
CORS(app)  # Enable CORS for frontend

# --- MongoDB Connection ---
MONGO_URI = os.getenv("MONGO_URI")

mongo_client = None
db = None
collection = None
users_collection = None

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

def get_ccc_metrics(chat_id: int) -> dict:
    """Calculate Cash Conversion Cycle metrics with corrected logic."""
    global mongo_client, collection
    
    # Check if MongoDB client is available, if not try to reconnect
    if mongo_client is None or collection is None:
        logger.warning("MongoDB client not available for CCC metrics, attempting to reconnect...")
        if not connect_to_mongodb():
            logger.error("Failed to connect to MongoDB for CCC metrics. Using mock data.")
            return get_mock_ccc_data(chat_id)
    
    try:
        ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)
        period_days = 90
        
        # Get all transactions for the period
        # Support both Telegram (chat_id) and WhatsApp (wa_id) data
        transactions = list(collection.find({
            "timestamp": {"$gte": ninety_days_ago},
            "$or": [
                {"chat_id": chat_id},
                {"wa_id": str(chat_id)}  # WhatsApp IDs are strings
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
                {"chat_id": chat_id},
                {"wa_id": str(chat_id)}  # WhatsApp IDs are strings
            ]
        }).sort('timestamp', -1))
        
        # Format all transactions for frontend
        formatted_recent = []
        for t in all_transactions:
            formatted_recent.append({
                'id': str(t['_id']),
                'date': t['timestamp'].strftime('%Y-%m-%d') if t.get('timestamp') else '',
                'type': t.get('action', 'unknown'),
                'amount': t.get('amount', 0),
                'customer': t.get('customer') or t.get('vendor', 'Unknown'),
                'status': 'completed',  # Default status
                'items': t.get('items', '')
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
        logger.error(f"Error in FIXED CCC calculation for chat_id {chat_id}: {e}")
        logger.info("Fallback to mock data due to database error")
        return get_mock_ccc_data(chat_id)

# --- API Routes ---

@app.route('/api/dashboard/<int:chat_id>', methods=['GET'])
def get_dashboard_data(chat_id):
    """Get dashboard data for a specific user."""
    try:
        logger.info(f"API request for dashboard data from chat_id {chat_id}")
        
        # Get CCC metrics and financial data
        metrics = get_ccc_metrics(chat_id)
        
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
        logger.error(f"Error in dashboard API for chat_id {chat_id}: {e}")
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

@app.route('/api/download-excel/<int:chat_id>', methods=['GET'])
def download_excel(chat_id):
    """Download all transactions for a user as Excel file."""
    try:
        if mongo_client is None or collection is None:
            if not connect_to_mongodb():
                return jsonify({'error': 'Database connection failed'}), 500
        
        # Get date range (optional query parameters)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query - support both Telegram (chat_id) and WhatsApp (wa_id) data
        query = {
            "$or": [
                {"chat_id": chat_id},
                {"wa_id": str(chat_id)}  # WhatsApp IDs are strings
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
                            {"chat_id": chat_id},
                            {"wa_id": str(chat_id)}
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
        filename = f"transactions_user_{chat_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error generating Excel file: {e}")
        return jsonify({'error': str(e)}), 500

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
