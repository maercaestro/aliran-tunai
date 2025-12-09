"""
Contractor Claim Workflow Module

This module handles the workflow for contractors/vendors claiming payment from main contractors:
1. Receipt upload (scanned paper receipt with school stamp)
2. OCR + stamp verification
3. MyInvois e-invoice generation (UBL 2.1 compliant)
4. Save to MongoDB (transactions_db.activity collection)
5. Payment confirmation
"""

import os
import base64
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
from openai import OpenAI
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    logger.info("OpenAI client initialized for contractor claims")
else:
    logger.warning("OPENAI_API_KEY not set - contractor claim processing will be limited")

# Initialize MongoDB client
MONGO_URI = os.getenv("MONGO_URI")
mongo_client = None
activity_collection = None

if MONGO_URI:
    try:
        mongo_client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
        db = mongo_client.transactions_db
        activity_collection = db.activity
        logger.info("MongoDB connected for contractor claims - using transactions_db.activity collection")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
else:
    logger.warning("MONGO_URI not set - contractor claims will not be saved to database")


def verify_receipt_with_stamp(image_bytes: bytes) -> Dict:
    """
    Verify receipt and check for stamp presence using GPT Vision.
    
    Returns:
        dict: {
            'has_stamp': bool,
            'stamp_details': str,
            'receipt_data': dict,
            'is_valid': bool,
            'verification_message': str
        }
    """
    if openai_client is None:
        return {
            'has_stamp': False,
            'stamp_details': '',
            'receipt_data': {},
            'is_valid': False,
            'verification_message': 'OpenAI client not initialized'
        }
    
    try:
        # Convert image bytes to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        logger.info("Analyzing receipt for stamp and data extraction...")
        
        prompt = """Analyze this receipt image and provide the following information:

1. **Stamp Verification**: Check if there is an official stamp on this receipt.
   - Look for rubber stamps, official seals, company chops, or stamped marks
   - Describe the stamp if present (color, shape, text visible on stamp)

2. **Receipt Data Extraction**: Extract ALL the following information:
   - Vendor/Contractor Name
   - Vendor Business Registration Number (if visible)
   - Vendor TIN/Tax ID (if visible)
   - Invoice/Receipt Number
   - Date of invoice/receipt
   - Items/Services provided (detailed list)
   - Unit prices for each item
   - Quantities
   - Subtotal amount
   - Tax amount (if any)
   - Total amount
   - Payment terms (if mentioned)
   - Any other relevant details

Return your analysis as a JSON object with this structure:
{
    "has_stamp": true/false,
    "stamp_details": "Description of stamp if present",
    "vendor_name": "Name from receipt",
    "vendor_registration": "Registration number if visible",
    "vendor_tin": "TIN if visible",
    "invoice_number": "Invoice/Receipt number",
    "invoice_date": "Date in YYYY-MM-DD format",
    "items": [
        {
            "description": "Item description",
            "quantity": 1.0,
            "unit_price": 100.00,
            "amount": 100.00
        }
    ],
    "subtotal": 0.00,
    "tax_amount": 0.00,
    "total_amount": 0.00,
    "payment_terms": "Payment terms if mentioned",
    "additional_notes": "Any other relevant information"
}

Be thorough and accurate. If a field is not visible, use null."""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
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
            max_completion_tokens=2000,
            temperature=0.1
        )
        
        result_text = response.choices[0].message.content.strip()
        logger.info(f"Receipt analysis result: {result_text[:300]}...")
        
        # Parse JSON response
        # Remove markdown code blocks if present
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        receipt_data = json.loads(result_text)
        
        # Validate receipt
        has_stamp = receipt_data.get('has_stamp', False)
        has_vendor = receipt_data.get('vendor_name') is not None
        has_amount = receipt_data.get('total_amount') is not None and receipt_data.get('total_amount', 0) > 0
        
        is_valid = has_stamp and has_vendor and has_amount
        
        if not has_stamp:
            verification_message = "❌ Receipt rejected: No official stamp detected. Please ensure the receipt is stamped by the school/authority."
        elif not has_vendor:
            verification_message = "❌ Receipt rejected: Vendor information not clear."
        elif not has_amount:
            verification_message = "❌ Receipt rejected: Total amount not found or invalid."
        else:
            verification_message = "✅ Receipt verified successfully! Stamp detected and all required information present."
        
        return {
            'has_stamp': has_stamp,
            'stamp_details': receipt_data.get('stamp_details', ''),
            'receipt_data': receipt_data,
            'is_valid': is_valid,
            'verification_message': verification_message
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse receipt analysis JSON: {e}")
        return {
            'has_stamp': False,
            'stamp_details': '',
            'receipt_data': {},
            'is_valid': False,
            'verification_message': f'Failed to parse receipt data: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Error verifying receipt with stamp: {e}")
        return {
            'has_stamp': False,
            'stamp_details': '',
            'receipt_data': {},
            'is_valid': False,
            'verification_message': f'Error processing receipt: {str(e)}'
        }


def generate_myinvois_einvoice(receipt_data: Dict, buyer_info: Dict = None) -> Dict:
    """
    Generate MyInvois-compliant e-invoice (UBL 2.1 format) from receipt data.
    
    Args:
        receipt_data: Extracted receipt data from verify_receipt_with_stamp
        buyer_info: Optional buyer information (TIN, name, address)
        
    Returns:
        dict: MyInvois JSON structure (UBL 2.1 compliant)
    """
    try:
        # Get current date and time
        now = datetime.now(timezone.utc)
        issue_date = now.strftime('%Y-%m-%d')
        issue_time = now.strftime('%H:%M:%SZ')
        
        # Extract receipt data
        vendor_name = receipt_data.get('vendor_name', 'Unknown Vendor')
        vendor_tin = receipt_data.get('vendor_tin', 'C234567890')  # Dummy TIN if not provided
        invoice_number = receipt_data.get('invoice_number', f'INV-{now.strftime("%Y%m%d%H%M%S")}')
        items = receipt_data.get('items', [])
        subtotal = receipt_data.get('subtotal', 0.0)
        tax_amount = receipt_data.get('tax_amount', 0.0)
        total_amount = receipt_data.get('total_amount', 0.0)
        
        # Default buyer info if not provided
        if buyer_info is None:
            buyer_info = {
                'name': 'Main Contractor',
                'tin': 'C987654321',
                'address': 'Malaysia',
                'city': 'Kuala Lumpur',
                'postal_code': '50000',
                'country': 'MYS'
            }
        
        # Build invoice lines from items
        invoice_lines = []
        for idx, item in enumerate(items, start=1):
            line = {
                "ID": str(idx),
                "InvoicedQuantity": {
                    "unitCode": "C62",  # Unit (piece)
                    "value": item.get('quantity', 1.0)
                },
                "LineExtensionAmount": {
                    "currencyID": "MYR",
                    "value": item.get('amount', 0.0)
                },
                "Item": {
                    "Description": item.get('description', 'Item'),
                    "ItemClassificationCode": {
                        "listID": "CLASS",
                        "value": "43221"  # Default MSIC code for construction/plumbing
                    }
                },
                "Price": {
                    "PriceAmount": {
                        "currencyID": "MYR",
                        "value": item.get('unit_price', 0.0)
                    }
                },
                "TaxTotal": {
                    "TaxAmount": {
                        "currencyID": "MYR",
                        "value": 0.0  # Individual line tax
                    },
                    "TaxSubtotal": [
                        {
                            "TaxableAmount": {
                                "currencyID": "MYR",
                                "value": item.get('amount', 0.0)
                            },
                            "TaxAmount": {
                                "currencyID": "MYR",
                                "value": 0.0
                            },
                            "TaxCategory": {
                                "ID": "E",  # Exempt
                                "TaxScheme": {
                                    "ID": "OTH"
                                }
                            }
                        }
                    ]
                }
            }
            invoice_lines.append(line)
        
        # If no items, create a single line item
        if not invoice_lines:
            invoice_lines = [{
                "ID": "1",
                "InvoicedQuantity": {
                    "unitCode": "C62",
                    "value": 1.0
                },
                "LineExtensionAmount": {
                    "currencyID": "MYR",
                    "value": total_amount
                },
                "Item": {
                    "Description": "Services rendered",
                    "ItemClassificationCode": {
                        "listID": "CLASS",
                        "value": "43221"
                    }
                },
                "Price": {
                    "PriceAmount": {
                        "currencyID": "MYR",
                        "value": total_amount
                    }
                },
                "TaxTotal": {
                    "TaxAmount": {
                        "currencyID": "MYR",
                        "value": 0.0
                    },
                    "TaxSubtotal": [
                        {
                            "TaxableAmount": {
                                "currencyID": "MYR",
                                "value": total_amount
                            },
                            "TaxAmount": {
                                "currencyID": "MYR",
                                "value": 0.0
                            },
                            "TaxCategory": {
                                "ID": "E",
                                "TaxScheme": {
                                    "ID": "OTH"
                                }
                            }
                        }
                    ]
                }
            }]
        
        # Build MyInvois JSON structure (UBL 2.1)
        einvoice = {
            "_D": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
            "_A": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            "_B": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            "Invoice": {
                "ID": invoice_number,
                "IssueDate": issue_date,
                "IssueTime": issue_time,
                "InvoiceTypeCode": {
                    "listVersionID": "1.0",
                    "value": "01"  # Standard Invoice
                },
                "DocumentCurrencyCode": "MYR",
                "AccountingSupplierParty": {
                    "Party": {
                        "PartyIdentification": [
                            {
                                "ID": {
                                    "schemeID": "TIN",
                                    "value": vendor_tin
                                }
                            }
                        ],
                        "PartyName": {
                            "Name": vendor_name
                        },
                        "PostalAddress": {
                            "CityName": "Kuala Lumpur",
                            "PostalZone": "50000",
                            "CountrySubentityCode": "14",
                            "Country": {
                                "IdentificationCode": {
                                    "listID": "ISO3166-1",
                                    "listAgencyID": "6",
                                    "value": "MYS"
                                }
                            }
                        },
                        "PartyTaxScheme": {
                            "TaxScheme": {
                                "ID": {
                                    "schemeID": "UN/ECE 5153",
                                    "schemeAgencyID": "6",
                                    "value": "OTH"
                                }
                            },
                            "CompanyID": vendor_tin
                        }
                    }
                },
                "AccountingCustomerParty": {
                    "Party": {
                        "PartyIdentification": [
                            {
                                "ID": {
                                    "schemeID": "TIN",
                                    "value": buyer_info.get('tin', 'C987654321')
                                }
                            }
                        ],
                        "PartyName": {
                            "Name": buyer_info.get('name', 'Main Contractor')
                        },
                        "PostalAddress": {
                            "CityName": buyer_info.get('city', 'Kuala Lumpur'),
                            "PostalZone": buyer_info.get('postal_code', '50000'),
                            "CountrySubentityCode": "14",
                            "Country": {
                                "IdentificationCode": {
                                    "listID": "ISO3166-1",
                                    "listAgencyID": "6",
                                    "value": buyer_info.get('country', 'MYS')
                                }
                            }
                        },
                        "PartyTaxScheme": {
                            "TaxScheme": {
                                "ID": {
                                    "schemeID": "UN/ECE 5153",
                                    "schemeAgencyID": "6",
                                    "value": "OTH"
                                }
                            },
                            "CompanyID": buyer_info.get('tin', 'C987654321')
                        }
                    }
                },
                "TaxTotal": {
                    "TaxAmount": {
                        "currencyID": "MYR",
                        "value": tax_amount
                    },
                    "TaxSubtotal": [
                        {
                            "TaxableAmount": {
                                "currencyID": "MYR",
                                "value": subtotal if subtotal > 0 else total_amount
                            },
                            "TaxAmount": {
                                "currencyID": "MYR",
                                "value": tax_amount
                            },
                            "TaxCategory": {
                                "ID": "E",  # Exempt
                                "TaxScheme": {
                                    "ID": {
                                        "schemeID": "UN/ECE 5153",
                                        "schemeAgencyID": "6",
                                        "value": "OTH"
                                    }
                                }
                            }
                        }
                    ]
                },
                "LegalMonetaryTotal": {
                    "LineExtensionAmount": {
                        "currencyID": "MYR",
                        "value": subtotal if subtotal > 0 else total_amount
                    },
                    "TaxExclusiveAmount": {
                        "currencyID": "MYR",
                        "value": subtotal if subtotal > 0 else total_amount
                    },
                    "TaxInclusiveAmount": {
                        "currencyID": "MYR",
                        "value": total_amount
                    },
                    "PayableAmount": {
                        "currencyID": "MYR",
                        "value": total_amount
                    }
                },
                "InvoiceLine": invoice_lines
            }
        }
        
        logger.info(f"Generated MyInvois e-invoice: {invoice_number}")
        return einvoice
        
    except Exception as e:
        logger.error(f"Error generating MyInvois e-invoice: {e}")
        return {"error": str(e)}


def save_claim_to_mongodb(wa_id: str, image_bytes: bytes, verification: Dict, einvoice: Dict, user_info: Dict = None) -> bool:
    """
    Save contractor claim to MongoDB transactions_db.activity collection.
    
    Args:
        wa_id: WhatsApp ID of the claimant
        image_bytes: Receipt image bytes
        verification: Verification result from verify_receipt_with_stamp
        einvoice: Generated e-invoice from generate_myinvois_einvoice
        user_info: Optional user information (user_type, name, company, etc.)
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    global activity_collection
    
    if activity_collection is None:
        logger.warning("MongoDB activity collection not available")
        return False
    
    try:
        # Convert image to base64 for storage
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        receipt_data = verification.get('receipt_data', {})
        invoice_id = einvoice.get('Invoice', {}).get('ID', 'UNKNOWN') if einvoice else 'UNKNOWN'
        
        # Generate unique claim ID
        claim_id = f"CLAIM-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        # Build activity document
        activity_doc = {
            # User information
            "wa_id": wa_id,
            "user_type": user_info.get('user_type', 'unknown') if user_info else 'unknown',
            "user_name": user_info.get('name', '') if user_info else '',
            "user_company": user_info.get('company', '') if user_info else '',
            
            # Claim identification
            "activity_type": "contractor_claim",
            "claim_id": claim_id,
            "invoice_id": invoice_id,
            
            # Receipt data
            "receipt_image": image_base64,  # Base64 encoded image
            "receipt_data": {
                "vendor_name": receipt_data.get('vendor_name'),
                "vendor_registration": receipt_data.get('vendor_registration'),
                "vendor_tin": receipt_data.get('vendor_tin'),
                "invoice_number": receipt_data.get('invoice_number'),
                "invoice_date": receipt_data.get('invoice_date'),
                "items": receipt_data.get('items', []),
                "subtotal": receipt_data.get('subtotal', 0.0),
                "tax_amount": receipt_data.get('tax_amount', 0.0),
                "total_amount": receipt_data.get('total_amount', 0.0),
                "payment_terms": receipt_data.get('payment_terms'),
                "additional_notes": receipt_data.get('additional_notes')
            },
            
            # Verification details
            "verification": {
                "has_stamp": verification.get('has_stamp', False),
                "stamp_details": verification.get('stamp_details', ''),
                "is_valid": verification.get('is_valid', False),
                "verification_message": verification.get('verification_message', '')
            },
            
            # E-invoice (full MyInvois JSON)
            "einvoice_json": einvoice if einvoice else {},
            
            # Status tracking
            "status": "approved" if verification.get('is_valid') else "rejected",
            "payment_status": "pending",  # pending | approved | paid
            "approved_by": None,
            "approved_at": None,
            "paid_at": None,
            
            # Timestamps
            "submitted_at": datetime.now(timezone.utc),
            "processed_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Insert into MongoDB
        result = activity_collection.insert_one(activity_doc)
        
        if result.inserted_id:
            logger.info(f"Contractor claim saved to MongoDB: claim_id={claim_id}, invoice_id={invoice_id}, doc_id={result.inserted_id}")
            return True
        else:
            logger.error("Failed to save contractor claim to MongoDB")
            return False
            
    except Exception as e:
        logger.error(f"Error saving contractor claim to MongoDB: {e}")
        return False


def process_contractor_claim(image_bytes: bytes, wa_id: str = None, user_info: Dict = None, buyer_info: Dict = None) -> Tuple[bool, str, Optional[Dict]]:
    """
    Complete contractor claim workflow with MongoDB storage.
    
    Args:
        image_bytes: Receipt image bytes
        wa_id: WhatsApp ID (for MongoDB storage)
        user_info: User information (user_type, name, company)
        buyer_info: Optional buyer information
        
    Returns:
        tuple: (success: bool, message: str, einvoice: dict or None)
    """
    try:
        # Step 1: Verify receipt and check stamp
        logger.info("Step 1: Verifying receipt and checking for stamp...")
        verification = verify_receipt_with_stamp(image_bytes)
        
        if not verification['is_valid']:
            # Still save rejected claims to MongoDB for audit trail
            if wa_id:
                save_claim_to_mongodb(wa_id, image_bytes, verification, {}, user_info)
            return False, verification['verification_message'], None
        
        # Step 2: Generate MyInvois e-invoice
        logger.info("Step 2: Generating MyInvois e-invoice...")
        einvoice = generate_myinvois_einvoice(verification['receipt_data'], buyer_info)
        
        if 'error' in einvoice:
            return False, f"Failed to generate e-invoice: {einvoice['error']}", None
        
        # Step 3: Save to MongoDB
        if wa_id:
            logger.info("Step 3: Saving contractor claim to MongoDB...")
            saved = save_claim_to_mongodb(wa_id, image_bytes, verification, einvoice, user_info)
            if saved:
                logger.info("✅ Contractor claim saved to transactions_db.activity")
            else:
                logger.warning("⚠️ Failed to save contractor claim to MongoDB")
        
        # Step 4: Format success message
        receipt_data = verification['receipt_data']
        success_message = f"""✅ **Contractor Claim Approved**

📋 **Receipt Verification:**
{verification['verification_message']}

🏢 **Vendor:** {receipt_data.get('vendor_name', 'N/A')}
📄 **Invoice #:** {receipt_data.get('invoice_number', 'N/A')}
📅 **Date:** {receipt_data.get('invoice_date', 'N/A')}
💰 **Total Amount:** RM {receipt_data.get('total_amount', 0):.2f}

✨ **Stamp Verified:** {verification['stamp_details']}

📧 **E-Invoice Generated:**
Invoice ID: {einvoice['Invoice']['ID']}
Type: MyInvois UBL 2.1 Compliant

✅ **Status:** Payment claim approved and saved to database.
"""
        
        return True, success_message, einvoice
        
    except Exception as e:
        logger.error(f"Error processing contractor claim: {e}")
        return False, f"Error processing claim: {str(e)}", None
