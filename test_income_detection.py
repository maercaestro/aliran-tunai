#!/usr/bin/env python3
"""
Test script to verify that income detection is now more restrictive.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from whatsapp_business_api import parse_transaction_with_regex

def test_income_detection():
    """Test that problematic inputs are now classified as expenses, not income."""
    
    test_cases = [
        # These should NOT be detected as income (should be expenses)
        ("tol rm5", "Should be expense"),
        ("bil elektrik rm100", "Should be expense"), 
        ("bayar bil air rm50", "Should be expense"),
        ("terima bil telefon rm80", "Should be expense"),
        ("receive invoice rm200", "Should be expense"),
        
        # These SHOULD be detected as income
        ("gaji rm3000", "Should be income"),
        ("salary rm2500", "Should be income"),
        ("income rm1000", "Should be income"),
        ("elaun rm500", "Should be income"),
        ("payment received from customer rm400", "Should be income"),
    ]
    
    print("Testing Income Detection Restrictions...")
    print("=" * 50)
    
    for test_input, expected in test_cases:
        result = parse_transaction_with_regex(test_input, 'personal')
        
        if result:
            action = result.get('action', 'unknown')
            is_income = action in ['payment_received', 'sale']
            
            print(f"Input: '{test_input}'")
            print(f"  Action: {action}")
            print(f"  Is Income: {is_income}")
            print(f"  Expected: {expected}")
            
            if "Should be income" in expected and not is_income:
                print(f"  ❌ FAIL: Expected income but got {action}")
            elif "Should be expense" in expected and is_income:
                print(f"  ❌ FAIL: Expected expense but got {action} (income)")
            else:
                print(f"  ✅ PASS")
        else:
            print(f"Input: '{test_input}' -> No regex match (will go to AI)")
            
        print()

if __name__ == "__main__":
    test_income_detection()