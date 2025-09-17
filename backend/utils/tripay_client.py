import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta
from flask import current_app
import requests


class TripayClient:
    """Tripay Payment Gateway Client"""
    
    def __init__(self):
        self.base_url = current_app.config['TRIPAY_BASE_URL']
        self.merchant_code = current_app.config['TRIPAY_MERCHANT_CODE']
        self.api_key = current_app.config['TRIPAY_API_KEY']
        self.private_key = current_app.config['TRIPAY_PRIVATE_KEY']
        
        if not all([self.base_url, self.merchant_code, self.api_key, self.private_key]):
            raise ValueError("Missing required Tripay configuration")
    
    def _get_headers(self):
        """Get headers for API requests"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'ChatGPT-Plus-Order-System/1.0'
        }
    
    def _make_request(self, method, endpoint, data=None):
        """Make HTTP request to Tripay API"""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Tripay API request failed: {str(e)}")
            raise Exception(f"Tripay API error: {str(e)}")
    
    def create_transaction(self, order_data):
        """Create payment transaction"""
        try:
            # Get package info
            packages = current_app.config['PACKAGES']
            package = packages.get(order_data['package_id'])
            
            if not package:
                raise ValueError(f"Invalid package_id: {order_data['package_id']}")
            
            # Generate unique merchant reference
            merchant_ref = f"ORD-{order_data['order_id']}-{uuid.uuid4().hex[:8]}"
            
            # Calculate expiry time (4 hours from now)
            expired_time = int((datetime.now() + timedelta(hours=4)).timestamp())
            
            # Prepare transaction payload
            payload = {
                'method': order_data.get('payment_method', 'QRIS'),  # Default to QRIS
                'merchant_ref': merchant_ref,
                'amount': int(package['price']),
                'customer_name': order_data.get('full_name', 'Customer'),
                'customer_email': order_data['customer_email'],
                'customer_phone': order_data.get('phone_number', ''),
                'order_items': [
                    {
                        'sku': order_data['package_id'],
                        'name': package['name'],
                        'price': int(package['price']),
                        'quantity': 1
                    }
                ],
                'return_url': f"{current_app.config.get('FRONTEND_URL', 'https://aksesgptmurah.tech')}/confirmation?order_id={order_data['order_id']}",
                'expired_time': expired_time,
                'signature': ''  # Will be calculated below
            }
            
            # Calculate signature
            signature_string = self.merchant_code + merchant_ref + str(payload['amount'])
            signature = hmac.new(
                self.private_key.encode('utf-8'),
                signature_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            payload['signature'] = signature
            
            # Make API request
            response = self._make_request('POST', 'transaction/create', payload)
            
            if response.get('success'):
                data = response.get('data', {})
                return {
                    'success': True,
                    'reference': data.get('reference'),
                    'merchant_ref': merchant_ref,
                    'checkout_url': data.get('checkout_url'),
                    'amount': payload['amount'],
                    'expired_time': expired_time
                }
            else:
                error_msg = response.get('message', 'Unknown error from Tripay')
                current_app.logger.error(f"Tripay transaction creation failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            current_app.logger.error(f"Error creating Tripay transaction: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_transaction_detail(self, reference):
        """Get transaction details by reference"""
        try:
            response = self._make_request('GET', f'transaction/detail?reference={reference}')
            
            if response.get('success'):
                return {
                    'success': True,
                    'data': response.get('data', {})
                }
            else:
                return {
                    'success': False,
                    'error': response.get('message', 'Unknown error')
                }
                
        except Exception as e:
            current_app.logger.error(f"Error getting transaction detail: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_callback_signature(self, reference, signature_from_header):
        """Verify callback signature"""
        try:
            # Calculate expected signature
            signature_string = hmac.new(
                self.private_key.encode('utf-8'),
                reference.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return signature_string == signature_from_header
            
        except Exception as e:
            current_app.logger.error(f"Error verifying callback signature: {str(e)}")
            return False
    
    def parse_callback_status(self, callback_data):
        """Parse callback data and return standardized status"""
        status = callback_data.get('status', '').upper()
        
        status_mapping = {
            'PAID': 'paid',
            'EXPIRED': 'expired',
            'FAILED': 'failed',
            'UNPAID': 'pending',
            'REFUND': 'refunded'
        }
        
        return status_mapping.get(status, 'unknown')


def get_tripay_client():
    """Factory function to get Tripay client instance"""
    return TripayClient()