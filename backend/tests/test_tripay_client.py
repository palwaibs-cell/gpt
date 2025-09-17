import unittest
import hashlib
import hmac
from unittest.mock import patch, MagicMock
from flask import Flask
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.tripay_client import TripayClient


class TestTripayClient(unittest.TestCase):
    def setUp(self):
        """Set up test app and client"""
        self.app = Flask(__name__)
        self.app.config.update({
            'TRIPAY_BASE_URL': 'https://tripay.co.id/api-sandbox/',
            'TRIPAY_MERCHANT_CODE': 'TEST123',
            'TRIPAY_API_KEY': 'test-api-key',
            'TRIPAY_PRIVATE_KEY': 'test-private-key',
            'PACKAGES': {
                'test_package': {
                    'name': 'Test Package',
                    'price': 100000
                }
            }
        })
    
    def test_verify_callback_signature(self):
        """Test HMAC signature verification"""
        with self.app.app_context():
            client = TripayClient()
            
            # Test data
            reference = 'TEST123456'
            private_key = 'test-private-key'
            
            # Generate expected signature
            expected_signature = hmac.new(
                private_key.encode('utf-8'),
                reference.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Test valid signature
            self.assertTrue(client.verify_callback_signature(reference, expected_signature))
            
            # Test invalid signature
            self.assertFalse(client.verify_callback_signature(reference, 'invalid-signature'))
    
    def test_parse_callback_status(self):
        """Test callback status parsing"""
        with self.app.app_context():
            client = TripayClient()
            
            # Test status mappings
            test_cases = [
                ({'status': 'PAID'}, 'paid'),
                ({'status': 'EXPIRED'}, 'expired'),
                ({'status': 'FAILED'}, 'failed'),
                ({'status': 'UNPAID'}, 'pending'),
                ({'status': 'REFUND'}, 'refunded'),
                ({'status': 'UNKNOWN'}, 'unknown'),
                ({}, 'unknown')
            ]
            
            for callback_data, expected_status in test_cases:
                result = client.parse_callback_status(callback_data)
                self.assertEqual(result, expected_status)
    
    @patch('requests.post')
    def test_create_transaction_success(self, mock_post):
        """Test successful transaction creation"""
        with self.app.app_context():
            # Mock successful response
            mock_response = MagicMock()
            mock_response.json.return_value = {
                'success': True,
                'data': {
                    'reference': 'TP123456789',
                    'checkout_url': 'https://tripay.co.id/checkout/TP123456789'
                }
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            client = TripayClient()
            
            order_data = {
                'order_id': 'ORD123',
                'package_id': 'test_package',
                'customer_email': 'test@example.com',
                'full_name': 'Test User',
                'phone_number': '081234567890'
            }
            
            result = client.create_transaction(order_data)
            
            # Verify result
            self.assertTrue(result['success'])
            self.assertEqual(result['reference'], 'TP123456789')
            self.assertEqual(result['checkout_url'], 'https://tripay.co.id/checkout/TP123456789')
            
            # Verify API call was made
            mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_create_transaction_failure(self, mock_post):
        """Test failed transaction creation"""
        with self.app.app_context():
            # Mock failed response
            mock_response = MagicMock()
            mock_response.json.return_value = {
                'success': False,
                'message': 'Invalid merchant code'
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            client = TripayClient()
            
            order_data = {
                'order_id': 'ORD123',
                'package_id': 'test_package',
                'customer_email': 'test@example.com'
            }
            
            result = client.create_transaction(order_data)
            
            # Verify result
            self.assertFalse(result['success'])
            self.assertIn('Invalid merchant code', result['error'])
    
    @patch('requests.get')
    def test_get_transaction_detail(self, mock_get):
        """Test transaction detail retrieval"""
        with self.app.app_context():
            # Mock successful response
            mock_response = MagicMock()
            mock_response.json.return_value = {
                'success': True,
                'data': {
                    'reference': 'TP123456789',
                    'status': 'PAID',
                    'amount': 100000
                }
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            client = TripayClient()
            result = client.get_transaction_detail('TP123456789')
            
            # Verify result
            self.assertTrue(result['success'])
            self.assertEqual(result['data']['reference'], 'TP123456789')
            self.assertEqual(result['data']['status'], 'PAID')
    
    def test_missing_config(self):
        """Test error handling with missing configuration"""
        app = Flask(__name__)
        
        with app.app_context():
            with self.assertRaises(ValueError):
                TripayClient()


if __name__ == '__main__':
    unittest.main()