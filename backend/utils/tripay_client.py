import os
import hmac
import hashlib
import json
import requests
import logging
from datetime import datetime
from flask import current_app

logger = logging.getLogger(__name__)

class TripayClient:
    def __init__(self):
        self.api_key = current_app.config['TRIPAY_API_KEY']
        self.merchant_code = current_app.config['TRIPAY_MERCHANT_CODE']
        self.private_key = current_app.config['TRIPAY_PRIVATE_KEY']
        self.is_production = current_app.config['TRIPAY_IS_PRODUCTION']
        self.api_base_url = current_app.config['API_BASE_URL']
        self.callback_path = current_app.config['TRIPAY_CALLBACK_PATH']
        
        # Tripay API endpoints
        if self.is_production:
            self.tripay_base_url = "https://tripay.co.id/api"
        else:
            self.tripay_base_url = "https://tripay.co.id/api-sandbox"
    
    def create_transaction(self, order_data, method="QRIS"):
        """
        Create transaction with Tripay
        
        Args:
            order_data (dict): Order information containing:
                - order_id: unique order identifier
                - customer_email: customer email
                - customer_name: customer name (optional)
                - amount: transaction amount
                - package_name: package name for order items
            method (str): Payment method (QRIS, BRIVA, BCAVA, etc.)
        
        Returns:
            dict: Transaction result with checkout_url, reference, status, payment_method
        """
        try:
            # Build callback and return URLs
            callback_url = f"{self.api_base_url}{self.callback_path}"
            return_url = f"{current_app.config.get('FRONTEND_URL', self.api_base_url)}/confirmation?order_id={order_data['order_id']}"
            
            # Prepare request payload
            payload = {
                'method': method,
                'merchant_ref': order_data['order_id'],
                'amount': int(order_data['amount']),
                'customer_name': order_data.get('customer_name', order_data.get('full_name', 'Customer')),
                'customer_email': order_data['customer_email'],
                'customer_phone': order_data.get('phone_number', ''),
                'order_items': [
                    {
                        'sku': order_data.get('package_id', 'chatgpt_plus'),
                        'name': order_data.get('package_name', 'ChatGPT Plus Subscription'),
                        'price': int(order_data['amount']),
                        'quantity': 1
                    }
                ],
                'return_url': return_url,
                'expired_time': int((datetime.now().timestamp() + 24 * 3600)),  # 24 hours
                'signature': self._generate_signature({
                    'merchant_ref': order_data['order_id'],
                    'amount': int(order_data['amount'])
                })
            }
            
            # Add callback URL if configured
            if callback_url:
                payload['callback_url'] = callback_url
            
            # Make request to Tripay
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{self.tripay_base_url}/transaction/create",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            logger.info(f"Tripay create transaction request: {payload}")
            logger.info(f"Tripay response status: {response.status_code}")
            logger.info(f"Tripay response: {response.text}")
            
            if response.status_code != 200:
                raise Exception(f"Tripay API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            if not result.get('success', False):
                raise Exception(f"Tripay transaction failed: {result.get('message', 'Unknown error')}")
            
            data = result.get('data', {})
            
            return {
                'success': True,
                'checkout_url': data.get('checkout_url'),
                'reference': data.get('reference'),
                'status': data.get('status', 'UNPAID'),
                'payment_method': method,
                'expired_time': data.get('expired_time'),
                'qr_string': data.get('qr_string'),  # For QRIS
                'pay_code': data.get('pay_code'),    # For VA
                'pay_url': data.get('pay_url')       # Alternative payment URL
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Tripay request error: {str(e)}")
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Tripay transaction creation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_callback_signature(self, payload_dict):
        """
        Verify Tripay callback signature using HMAC-SHA256
        
        Args:
            payload_dict (dict): Callback payload from Tripay
        
        Returns:
            bool: True if signature is valid, False otherwise
        """
        try:
            received_signature = payload_dict.get('signature')
            if not received_signature:
                logger.error("No signature found in callback payload")
                return False
            
            # Build signature string according to Tripay documentation
            # Format: merchant_ref + reference + amount + status + private_key
            signature_string = (
                str(payload_dict.get('merchant_ref', '')) +
                str(payload_dict.get('reference', '')) +
                str(payload_dict.get('total_amount', payload_dict.get('amount', ''))) +
                str(payload_dict.get('status', '')) +
                str(self.private_key)
            )
            
            # Generate HMAC-SHA256 signature
            calculated_signature = hmac.new(
                self.private_key.encode('utf-8'),
                signature_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            is_valid = hmac.compare_digest(received_signature, calculated_signature)
            
            if not is_valid:
                logger.error(f"Signature verification failed. Expected: {calculated_signature}, Received: {received_signature}")
                logger.error(f"Signature string: {signature_string}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Signature verification error: {str(e)}")
            return False
    
    def _generate_signature(self, data):
        """
        Generate signature for Tripay API request
        
        Args:
            data (dict): Data to sign
        
        Returns:
            str: Generated signature
        """
        try:
            # Build signature string for transaction creation
            signature_string = (
                str(self.merchant_code) +
                str(data['merchant_ref']) +
                str(data['amount']) +
                str(self.private_key)
            )
            
            signature = hmac.new(
                self.private_key.encode('utf-8'),
                signature_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return signature
            
        except Exception as e:
            logger.error(f"Signature generation error: {str(e)}")
            return ""
    
    def get_payment_methods(self):
        """
        Get available payment methods from Tripay
        
        Returns:
            dict: Available payment methods
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.tripay_base_url}/merchant/payment-channel",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'data': result.get('data', [])
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except Exception as e:
            logger.error(f"Failed to get payment methods: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

def get_tripay_client():
    """Factory function to get Tripay client instance"""
    return TripayClient()