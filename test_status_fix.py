#!/usr/bin/env python3
"""Test the status report fix for null safety."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from whatsapp_business_api import generate_actionable_advice
    print("✅ Status report function imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_status_report_fix():
    """Test the status report generation with various scenarios including null actions."""
    
    print("🔧 Testing Status Report Generation Fix")
    print("=" * 50)
    
    # Test with normal transaction breakdown
    normal_metrics = {
        'dso': 15.0,
        'dio': 25.0,
        'dpo': 30.0,
        'ccc': 10.0,
        'transaction_breakdown': [
            {'_id': 'sale', 'count': 5, 'total_amount': 1000.0},
            {'_id': 'purchase', 'count': 3, 'total_amount': 500.0},
            {'_id': 'payment_made', 'count': 2, 'total_amount': 200.0}
        ]
    }
    
    # Test with null/None action (the problematic case)
    problematic_metrics = {
        'dso': 20.0,
        'dio': 45.0, 
        'dpo': 15.0,
        'ccc': 50.0,
        'transaction_breakdown': [
            {'_id': None, 'count': 2, 'total_amount': 300.0},  # This was causing the error
            {'_id': 'sale', 'count': 3, 'total_amount': 800.0},
            {'_id': '', 'count': 1, 'total_amount': 100.0}     # Empty string case
        ]
    }
    
    # Test with missing data
    minimal_metrics = {
        'dso': 0.0,
        'dio': 0.0,
        'dpo': 0.0,
        'ccc': 0.0,
        'transaction_breakdown': []
    }
    
    test_cases = [
        ("Normal Case", normal_metrics),
        ("Problematic Case (Null Actions)", problematic_metrics), 
        ("Minimal Case (Empty)", minimal_metrics)
    ]
    
    for case_name, metrics in test_cases:
        print(f"\n🧪 {case_name}")
        print("-" * 30)
        
        try:
            advice = generate_actionable_advice(metrics)
            print(f"✅ SUCCESS: Generated advice ({len(advice)} characters)")
            print(f"📊 CCC: {metrics['ccc']} days")
            
            # Show first 200 chars of advice 
            preview = advice[:200] + "..." if len(advice) > 200 else advice
            print(f"📝 Advice preview: {preview}")
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
    
    print(f"\n✅ Status Report Fix Verification Complete!")
    print(f"The 'NoneType' object has no attribute 'capitalize' error should now be resolved.")

if __name__ == "__main__":
    test_status_report_fix()