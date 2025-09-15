import uuid
import hashlib
import hmac
from datetime import datetime
from flask import current_app
import midtransclient

class MidtransPaymentGateway:
    def __init__(self):
        self.server_key = current_app.config['MIDTRANS_SERVER_KEY']
        self.client_key = current_app.config['MIDTRANS_CLIENT_KEY']
        self.is_production = current_app.config['MIDTRANS_IS_PRODUCTION']
        
        # Initialize Midtrans Snap
        self.snap = midtransclient.Snap(
            is_production=self.is_production,
            server_key=self.server_key,
            client_key=self.client_key
        )
        
        # Initialize Core API for transaction status
        self.core_api = midtransclient.CoreApi(
            is_production=self.is_production,
            server_key=self.server_key,
            client_key=self.client_key
        )
    
    def create_transaction(self, order_data):
        """Create payment transaction and return payment URL"""
        try:
            # Get package info
            packages = current_app.config['PACKAGES']
            package = packages.get(order_data['package_id'])
            
            if not package:
                raise ValueError(f"Invalid package_id: {order_data['package_id']}")
            
            # Prepare transaction parameters
            transaction_details = {
                'order_id': order_data['order_id'],
                'gross_amount': int(package['price'])
            }
            
            item_details = [{
                'id': order_data['package_id'],
                'price': int(package['price']),
                'quantity': 1,
                'name': package['name'],
                'category': 'ChatGPT Plus Subscription'
            }]
            
            customer_details = {
                'email': order_data['customer_email'],
                'first_name': order_data.get('full_name', '').split(' ')[0] if order_data.get('full_name') else 'Customer',
                'last_name': ' '.join(order_data.get('full_name', '').split(' ')[1:]) if order_data.get('full_name') and len(order_data.get('full_name', '').split(' ')) > 1 else '',
                'phone': order_data.get('phone_number', '')
            }
            
            # Transaction parameters
            param = {
                'transaction_details': transaction_details,
                'item_details': item_details,
                'customer_details': customer_details,
                'enabled_payments': [
                    'credit_card', 'bca_va', 'bni_va', 'bri_va', 'permata_va',
                    'other_va', 'gopay', 'shopeepay', 'qris', 'indomaret', 'alfamart'
                ],
                'callbacks': {
                    'finish': f"{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/confirmation?order_id={order_data['order_id']}"
                },
                'expiry': {
                    'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S +0700'),
                    'unit': 'hours',
                    'duration': 24
                }
            }
            
            # Create transaction
            transaction = self.snap.create_transaction(param)
            
            return {
                'success': True,
                'payment_url': transaction['redirect_url'],
                'token': transaction['token'],
                'transaction_id': order_data['order_id']
            }
            
        except Exception as e:
            current_app.logger.error(f"Midtrans transaction creation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_transaction_status(self, order_id):
        """Get transaction status from Midtrans"""
        try:
            status_response = self.core_api.transactions.status(order_id)
            return {
                'success': True,
                'status': status_response
            }
        except Exception as e:
            current_app.logger.error(f"Failed to get transaction status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_webhook_signature(self, order_id, status_code, gross_amount, signature_key):
        """Verify webhook signature from Midtrans"""
        try:
            # Create signature string
            signature_string = f"{order_id}{status_code}{gross_amount}{self.server_key}"
            
            # Generate hash
            generated_signature = hashlib.sha512(signature_string.encode('utf-8')).hexdigest()
            
            return generated_signature == signature_key
        except Exception as e:
            current_app.logger.error(f"Signature verification failed: {str(e)}")
            return False
    
    def parse_webhook_status(self, webhook_data):
        """Parse webhook data and return standardized status"""
        transaction_status = webhook_data.get('transaction_status')
        fraud_status = webhook_data.get('fraud_status')
        
        if transaction_status == 'capture':
            if fraud_status == 'challenge':
                return 'pending'
            elif fraud_status == 'accept':
                return 'paid'
            else:
                return 'failed'
        elif transaction_status == 'settlement':
            return 'paid'
        elif transaction_status in ['cancel', 'deny', 'expire']:
            return 'failed'
        elif transaction_status == 'pending':
            return 'pending'
        else:
            return 'unknown'

def get_payment_gateway():
    """Factory function to get payment gateway instance"""
    return MidtransPaymentGateway()