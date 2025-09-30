#!/usr/bin/env python3
"""
Test script untuk debug order creation issue
Run this on your production server with: python3 test_order_creation.py
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_environment_variables():
    """Test if all required environment variables are set"""
    print("\n" + "="*60)
    print("1. TESTING ENVIRONMENT VARIABLES")
    print("="*60)

    required_vars = [
        'DATABASE_URL',
        'TRIPAY_API_KEY',
        'TRIPAY_MERCHANT_CODE',
        'TRIPAY_PRIVATE_KEY',
        'TRIPAY_IS_PRODUCTION',
        'TRIPAY_CALLBACK_URL',
        'ALLOWED_ORIGINS'
    ]

    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'PRIVATE' in var:
                display_value = value[:5] + '***' + value[-5:] if len(value) > 10 else '***'
            else:
                display_value = value
            print(f"  ✓ {var}: {display_value}")
        else:
            print(f"  ✗ {var}: NOT SET")
            missing_vars.append(var)

    if missing_vars:
        print(f"\n  ⚠️  WARNING: {len(missing_vars)} environment variables are missing!")
        return False
    else:
        print("\n  ✓ All environment variables are set")
        return True

def test_database_connection():
    """Test database connection"""
    print("\n" + "="*60)
    print("2. TESTING DATABASE CONNECTION")
    print("="*60)

    try:
        from app import create_app
        from models import db, Order

        app = create_app('production')

        with app.app_context():
            # Try to create tables
            db.create_all()
            print("  ✓ Database tables created/verified")

            # Try a simple query
            order_count = Order.query.count()
            print(f"  ✓ Database query successful (found {order_count} orders)")

            return True

    except Exception as e:
        print(f"  ✗ Database connection failed: {str(e)}")
        logger.exception("Database connection error:")
        return False

def test_tripay_credentials():
    """Test Tripay API credentials"""
    print("\n" + "="*60)
    print("3. TESTING TRIPAY CREDENTIALS")
    print("="*60)

    try:
        from app import create_app
        from utils.tripay_client import get_tripay_client

        app = create_app('production')

        with app.app_context():
            # Initialize Tripay client
            tripay_client = get_tripay_client()
            print("  ✓ Tripay client initialized")

            # Test getting payment channels
            print("  → Testing Tripay API connection...")
            result = tripay_client.get_payment_channels()

            if result.get('success'):
                channels = result.get('data', [])
                print(f"  ✓ Tripay API accessible ({len(channels)} payment channels available)")

                # Show first 3 channels
                if channels:
                    print("\n  Available payment methods:")
                    for channel in channels[:3]:
                        print(f"    - {channel.get('code')}: {channel.get('name')}")
                    if len(channels) > 3:
                        print(f"    ... and {len(channels) - 3} more")

                return True
            else:
                print(f"  ✗ Tripay API error: {result.get('error')}")
                return False

    except Exception as e:
        print(f"  ✗ Tripay credentials test failed: {str(e)}")
        logger.exception("Tripay credentials error:")
        return False

def test_create_order():
    """Test creating an actual order"""
    print("\n" + "="*60)
    print("4. TESTING ORDER CREATION")
    print("="*60)

    try:
        from app import create_app
        from models import db, Order
        from utils.validators import validate_order_data
        from utils.tripay_client import get_tripay_client
        import time

        app = create_app('production')

        with app.app_context():
            # Prepare test order data
            test_data = {
                'customer_email': 'test@example.com',
                'package_id': 'chatgpt_plus_1_month',
                'full_name': 'Test User',
                'phone_number': '+628123456789'
            }

            print(f"  → Validating order data...")
            is_valid, errors, validated_data = validate_order_data(test_data)

            if not is_valid:
                print(f"  ✗ Validation failed: {errors}")
                return False

            print(f"  ✓ Order data validated")

            # Generate merchant ref
            merchant_ref = f"TEST-{int(time.time())}"
            print(f"  → Merchant ref: {merchant_ref}")

            # Get package info
            packages = app.config['PACKAGES']
            package = packages.get('chatgpt_plus_1_month')
            amount = package['price']
            print(f"  → Package: {package['name']}, Amount: Rp {amount:,}")

            # Create Tripay transaction (without saving to DB)
            print(f"  → Creating Tripay transaction...")
            tripay_client = get_tripay_client()

            payment_data = {
                'merchant_ref': merchant_ref,
                'amount': amount,
                'customer_email': validated_data['customer_email'],
                'customer_name': validated_data.get('full_name', 'Test User'),
                'phone_number': validated_data.get('phone_number', '+628123456789'),
                'package_id': 'chatgpt_plus_1_month',
                'package_name': package['name']
            }

            payment_result = tripay_client.create_transaction(payment_data, method='QRIS')

            if payment_result.get('success'):
                print(f"  ✓ Tripay transaction created successfully!")
                print(f"\n  Transaction Details:")
                print(f"    - Reference: {payment_result.get('reference')}")
                print(f"    - Checkout URL: {payment_result.get('checkout_url')}")
                print(f"    - Payment Method: {payment_result.get('payment_method')}")
                print(f"    - Amount: Rp {payment_result.get('amount'):,}")
                print(f"    - Status: {payment_result.get('status')}")

                # Try to save to database
                print(f"\n  → Saving order to database...")
                order = Order(
                    order_id=merchant_ref,
                    customer_email=validated_data['customer_email'],
                    full_name=validated_data.get('full_name'),
                    phone_number=validated_data.get('phone_number'),
                    package_id='chatgpt_plus_1_month',
                    amount=amount,
                    payment_status='pending',
                    invitation_status='pending',
                    checkout_url=payment_result.get('checkout_url'),
                    payment_method=payment_result.get('payment_method'),
                    reference=payment_result.get('reference')
                )

                db.session.add(order)
                db.session.commit()
                print(f"  ✓ Order saved to database")

                return True
            else:
                print(f"  ✗ Tripay transaction failed:")
                print(f"    Error: {payment_result.get('error')}")
                print(f"    Details: {payment_result.get('details')}")
                return False

    except Exception as e:
        print(f"  ✗ Order creation test failed: {str(e)}")
        logger.exception("Order creation error:")
        return False

def main():
    """Main test runner"""
    print("\n" + "="*60)
    print("BACKEND ORDER CREATION DIAGNOSTIC TEST")
    print("="*60)
    print("\nThis script will test:")
    print("  1. Environment variables")
    print("  2. Database connection")
    print("  3. Tripay API credentials")
    print("  4. Order creation flow")
    print("\n" + "="*60)

    # Load .env file if exists
    try:
        from dotenv import load_dotenv
        if os.path.exists('.env'):
            load_dotenv()
            print("\n✓ Loaded .env file")
        else:
            print("\n⚠️  No .env file found, using system environment variables")
    except ImportError:
        print("\n⚠️  python-dotenv not installed, using system environment variables")

    results = []

    # Run tests
    results.append(("Environment Variables", test_environment_variables()))
    results.append(("Database Connection", test_database_connection()))
    results.append(("Tripay Credentials", test_tripay_credentials()))
    results.append(("Order Creation", test_create_order()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {status}: {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    print(f"\n  Total: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n  ✓ All tests passed! Backend should be working correctly.")
        print("  If frontend still shows 'Failed to fetch', try:")
        print("    1. Hard refresh browser (Ctrl+Shift+R)")
        print("    2. Clear browser cache")
        print("    3. Test in incognito window")
        return 0
    else:
        print("\n  ✗ Some tests failed. Fix the issues above before proceeding.")
        return 1

if __name__ == '__main__':
    sys.exit(main())