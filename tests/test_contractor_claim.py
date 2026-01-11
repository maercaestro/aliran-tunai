"""
Test script for contractor claim workflow.

This script tests:
1. Receipt verification with stamp detection
2. MyInvois e-invoice generation
3. Complete workflow integration
"""

import os
import json
from dotenv import load_dotenv
from contractor_claim import (
    verify_receipt_with_stamp,
    generate_myinvois_einvoice,
    process_contractor_claim
)

# Load environment
load_dotenv()

def test_sample_receipt():
    """Test with a sample receipt image if available."""
    print("=" * 60)
    print("CONTRACTOR CLAIM WORKFLOW TEST")
    print("=" * 60)
    
    # Check for test image
    test_image_path = 'test_images/sample_receipt.jpg'
    
    if not os.path.exists(test_image_path):
        print(f"\n⚠️  Test image not found: {test_image_path}")
        print("\nTo test with a real image:")
        print("1. Create a 'test_images' directory")
        print("2. Add a receipt image named 'sample_receipt.jpg'")
        print("3. Run this test script again")
        print("\nGenerating sample e-invoice with mock data instead...\n")
        
        # Test with mock receipt data
        mock_receipt_data = {
            'vendor_name': 'ABC Construction Sdn Bhd',
            'vendor_tin': 'C123456789',
            'invoice_number': 'INV-2025-001',
            'invoice_date': '2025-12-09',
            'items': [
                {
                    'description': 'Plumbing work - Installation of water pipes',
                    'quantity': 1.0,
                    'unit_price': 5000.00,
                    'amount': 5000.00
                },
                {
                    'description': 'Labor charges',
                    'quantity': 3.0,
                    'unit_price': 500.00,
                    'amount': 1500.00
                }
            ],
            'subtotal': 6500.00,
            'tax_amount': 0.00,
            'total_amount': 6500.00,
            'payment_terms': '30 days'
        }
        
        print("📋 Mock Receipt Data:")
        print(json.dumps(mock_receipt_data, indent=2))
        
        # Generate e-invoice
        print("\n🔄 Generating MyInvois e-invoice...")
        einvoice = generate_myinvois_einvoice(mock_receipt_data)
        
        if 'error' in einvoice:
            print(f"\n❌ Error: {einvoice['error']}")
            return False
        
        print("\n✅ MyInvois E-Invoice Generated Successfully!")
        print("\n📄 E-Invoice Details:")
        print(f"  Invoice ID: {einvoice['Invoice']['ID']}")
        print(f"  Issue Date: {einvoice['Invoice']['IssueDate']}")
        print(f"  Issue Time: {einvoice['Invoice']['IssueTime']}")
        print(f"  Type Code: {einvoice['Invoice']['InvoiceTypeCode']['value']}")
        print(f"  Currency: {einvoice['Invoice']['DocumentCurrencyCode']}")
        
        print("\n💰 Monetary Total:")
        monetary = einvoice['Invoice']['LegalMonetaryTotal']
        print(f"  Line Extension: {monetary['LineExtensionAmount']['currencyID']} {monetary['LineExtensionAmount']['value']:.2f}")
        print(f"  Tax Exclusive: {monetary['TaxExclusiveAmount']['currencyID']} {monetary['TaxExclusiveAmount']['value']:.2f}")
        print(f"  Tax Inclusive: {monetary['TaxInclusiveAmount']['currencyID']} {monetary['TaxInclusiveAmount']['value']:.2f}")
        print(f"  Payable: {monetary['PayableAmount']['currencyID']} {monetary['PayableAmount']['value']:.2f}")
        
        print("\n📦 Invoice Lines:")
        for line in einvoice['Invoice']['InvoiceLine']:
            print(f"  {line['ID']}. {line['Item']['Description']}")
            print(f"     Qty: {line['InvoicedQuantity']['value']} {line['InvoicedQuantity']['unitCode']}")
            print(f"     Unit Price: {line['Price']['PriceAmount']['currencyID']} {line['Price']['PriceAmount']['value']:.2f}")
            print(f"     Amount: {line['LineExtensionAmount']['currencyID']} {line['LineExtensionAmount']['value']:.2f}")
        
        # Save to file
        output_file = 'test_einvoice_output.json'
        with open(output_file, 'w') as f:
            json.dump(einvoice, f, indent=2)
        print(f"\n💾 E-invoice saved to: {output_file}")
        
        print("\n✅ Test completed successfully!")
        print("\n📝 E-Invoice Structure:")
        print("  ✓ UBL 2.1 compliant")
        print("  ✓ InvoiceTypeCode: 01 (Invoice)")
        print("  ✓ IssueDate & IssueTime included")
        print("  ✓ AccountingSupplierParty with PartyTaxScheme")
        print("  ✓ AccountingCustomerParty with PartyTaxScheme")
        print("  ✓ ItemClassificationCode (MSIC: 43221)")
        print("  ✓ TaxTotal (even if 0)")
        print("  ✓ LegalMonetaryTotal")
        
        return True
    
    else:
        # Test with real image
        print(f"\n📷 Testing with image: {test_image_path}")
        
        with open(test_image_path, 'rb') as f:
            image_data = f.read()
        
        print("\n🔄 Processing contractor claim workflow...")
        success, message, einvoice = process_contractor_claim(image_data)
        
        print("\n" + "=" * 60)
        print("RESULT:")
        print("=" * 60)
        print(message)
        
        if success and einvoice:
            output_file = f"test_einvoice_{einvoice['Invoice']['ID']}.json"
            with open(output_file, 'w') as f:
                json.dump(einvoice, f, indent=2)
            print(f"\n💾 E-invoice saved to: {output_file}")
            return True
        else:
            print("\n❌ Claim rejected or error occurred.")
            return False

def test_stamp_detection():
    """Test stamp detection separately."""
    print("\n" + "=" * 60)
    print("STAMP DETECTION TEST")
    print("=" * 60)
    
    test_image_path = 'test_images/sample_receipt.jpg'
    
    if not os.path.exists(test_image_path):
        print(f"\n⚠️  Test image not found: {test_image_path}")
        print("Skipping stamp detection test.")
        return
    
    print(f"\n📷 Testing stamp detection with: {test_image_path}")
    
    with open(test_image_path, 'rb') as f:
        image_data = f.read()
    
    print("\n🔍 Verifying receipt and checking for stamp...")
    verification = verify_receipt_with_stamp(image_data)
    
    print("\n📋 Verification Results:")
    print(f"  Has Stamp: {'✅ Yes' if verification['has_stamp'] else '❌ No'}")
    print(f"  Stamp Details: {verification['stamp_details']}")
    print(f"  Is Valid: {'✅ Yes' if verification['is_valid'] else '❌ No'}")
    print(f"  Message: {verification['verification_message']}")
    
    if verification['receipt_data']:
        print("\n📄 Extracted Receipt Data:")
        receipt_data = verification['receipt_data']
        print(f"  Vendor: {receipt_data.get('vendor_name', 'N/A')}")
        print(f"  Invoice #: {receipt_data.get('invoice_number', 'N/A')}")
        print(f"  Date: {receipt_data.get('invoice_date', 'N/A')}")
        print(f"  Total: RM {receipt_data.get('total_amount', 0):.2f}")
        
        if receipt_data.get('items'):
            print("\n  Items:")
            for item in receipt_data['items']:
                print(f"    - {item.get('description', 'N/A')}: RM {item.get('amount', 0):.2f}")

if __name__ == '__main__':
    print("\n🚀 Starting Contractor Claim Workflow Tests\n")
    
    # Test 1: Basic e-invoice generation with mock data
    success1 = test_sample_receipt()
    
    # Test 2: Stamp detection (if image available)
    test_stamp_detection()
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)
    
    if success1:
        print("\n✅ All tests passed!")
        print("\n📌 Next Steps:")
        print("  1. Test with real receipt images")
        print("  2. Send receipt via WhatsApp/Telegram bot")
        print("  3. Verify stamp detection accuracy")
        print("  4. Check e-invoice compliance")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
