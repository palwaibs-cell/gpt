import os
import uuid
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import config
from models import db, Order, InvitationLog, Package, ChatGPTAccount, AccountAssignment, AuditLog
from utils.validators import validate_order_data
from utils.payment_gateway import get_payment_gateway
from utils.tripay_client import get_tripay_client
from utils.email_service import send_payment_confirmation, send_admin_notification
from services.account_allocator import AccountAllocator
from tasks import make_celery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Configure CORS
    CORS(app, origins=["http://localhost:3000", "http://localhost:5173"])
    
    # Configure rate limiting
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        storage_uri=app.config.get('RATELIMIT_STORAGE_URL')
    )
    
    # Initialize Celery
    celery = make_celery(app)
    
    # Import tasks after celery initialization
    from tasks import process_invitation_task
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        })
    
    @app.route('/api/orders', methods=['POST'])
    @limiter.limit("10 per minute")
    def create_order():
        """Create new order and initiate payment"""
        try:
            # Get request data
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Validate input data
            is_valid, errors, validated_data = validate_order_data(data)
            if not is_valid:
                return jsonify({'error': 'Validation failed', 'details': errors}), 400
            
            # Generate unique order ID
            order_id = f"ORD{uuid.uuid4().hex[:8].upper()}"
            
            # Get package information
            packages = app.config['PACKAGES']
            package = packages.get(validated_data['package_id'])
            
            if not package:
                return jsonify({'error': 'Invalid package_id'}), 400
            
            # Create order record
            order = Order(
                order_id=order_id,
                customer_email=validated_data['customer_email'],
                full_name=validated_data.get('full_name'),
                phone_number=validated_data.get('phone_number'),
                package_id=validated_data['package_id'],
                amount=package['price'],
                payment_status='pending',
                invitation_status='pending'
            )
            
            db.session.add(order)
            db.session.flush()  # Get the ID without committing
            
            # Create payment transaction
            payment_gateway = get_payment_gateway()
            payment_data = {
                'order_id': order_id,
                'customer_email': validated_data['customer_email'],
                'full_name': validated_data.get('full_name'),
                'phone_number': validated_data.get('phone_number'),
                'package_id': validated_data['package_id']
            }
            
            payment_result = payment_gateway.create_transaction(payment_data)
            
            if not payment_result['success']:
                db.session.rollback()
                logger.error(f"Payment gateway error: {payment_result['error']}")
                return jsonify({'error': 'Payment gateway error'}), 500
            
            # Update order with payment gateway reference
            if 'reference' in payment_result:
                # Tripay response
                order.payment_gateway_ref_id = payment_result['transaction_id']
                order.reference = payment_result['reference']
                if 'expired_time' in payment_result:
                    order.expired_at = datetime.fromtimestamp(payment_result['expired_time'])
            else:
                # Midtrans response
                order.payment_gateway_ref_id = payment_result['transaction_id']
            
            db.session.commit()
            
            logger.info(f"Order created successfully: {order_id}")
            
            return jsonify({
                'order_id': order_id,
                'payment_url': payment_result['payment_url'],
                'status': 'pending_payment'
            }), 201
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating order: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/orders/<order_id>/status', methods=['GET'])
    @limiter.limit("30 per minute")
    def get_order_status(order_id):
        """Get order status"""
        try:
            order = Order.query.filter_by(order_id=order_id).first()
            
            if not order:
                return jsonify({'error': 'Order not found'}), 404
            
            # Generate status message
            message = generate_status_message(order)
            
            return jsonify({
                'order_id': order.order_id,
                'payment_status': order.payment_status,
                'invitation_status': order.invitation_status,
                'message': message
            })
            
        except Exception as e:
            logger.error(f"Error getting order status: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/payment/webhook', methods=['POST'])
    def payment_webhook():
        """Handle payment gateway webhook"""
        try:
            # Get webhook data
            webhook_data = request.get_json()
            if not webhook_data:
                logger.error("No webhook data received")
                return jsonify({'error': 'No data'}), 400
            
            # Verify webhook signature
            payment_gateway = get_payment_gateway()
            
            order_id = webhook_data.get('order_id')
            status_code = webhook_data.get('status_code')
            gross_amount = webhook_data.get('gross_amount')
            signature_key = webhook_data.get('signature_key')
            
            if not all([order_id, status_code, gross_amount, signature_key]):
                logger.error("Missing required webhook fields")
                return jsonify({'error': 'Missing required fields'}), 400
            
            # Verify signature
            if not payment_gateway.verify_webhook_signature(order_id, status_code, gross_amount, signature_key):
                logger.error(f"Invalid webhook signature for order {order_id}")
                return jsonify({'error': 'Invalid signature'}), 401
            
            # Find order
            order = Order.query.filter_by(order_id=order_id).first()
            if not order:
                logger.error(f"Order not found: {order_id}")
                return jsonify({'error': 'Order not found'}), 404
            
            # Parse payment status
            new_status = payment_gateway.parse_webhook_status(webhook_data)
            old_status = order.payment_status
            
            # Update order status
            order.payment_status = new_status
            order.updated_at = datetime.utcnow()
            
            # If payment is successful, trigger invitation process
            if new_status == 'paid' and old_status != 'paid':
                order.invitation_status = 'processing'
                
                # Send payment confirmation email
                try:
                    send_payment_confirmation(order)
                except Exception as e:
                    logger.error(f"Failed to send payment confirmation: {str(e)}")
                
                # Trigger invitation task
                try:
                    process_invitation_task.delay(order.id)
                    logger.info(f"Invitation task queued for order {order_id}")
                except Exception as e:
                    logger.error(f"Failed to queue invitation task: {str(e)}")
                    order.invitation_status = 'failed'
            
            db.session.commit()
            
            logger.info(f"Webhook processed successfully for order {order_id}: {old_status} -> {new_status}")
            
            return jsonify({'status': 'success'}), 200
            
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/callback/tripay', methods=['POST'])
    def tripay_callback():
        """Handle Tripay payment callback"""
        try:
            # Get request data
            callback_data = request.get_json()
            
            if not callback_data:
                logger.error("No callback data received from Tripay")
                return jsonify({'error': 'No data'}), 400
            
            # Verify callback event and signature
            callback_event = request.headers.get('X-Callback-Event')
            callback_signature = request.headers.get('X-Callback-Signature')
            
            if callback_event != 'payment_status':
                logger.error(f"Invalid callback event: {callback_event}")
                return jsonify({'error': 'Invalid event'}), 400
            
            # Get transaction reference
            reference = callback_data.get('reference')
            if not reference:
                logger.error("Missing reference in callback data")
                return jsonify({'error': 'Missing reference'}), 400
            
            # Verify HMAC signature
            tripay_client = get_tripay_client()
            if not tripay_client.verify_callback_signature(reference, callback_signature):
                logger.error(f"Invalid callback signature for reference {reference}")
                return jsonify({'error': 'Invalid signature'}), 401
            
            # Find order by reference
            order = Order.query.filter_by(reference=reference).first()
            if not order:
                logger.error(f"Order not found for reference: {reference}")
                return jsonify({'error': 'Order not found'}), 404
            
            # Check for idempotency
            if order.payment_status in ['paid', 'failed', 'expired', 'refunded']:
                logger.info(f"Order {order.order_id} already processed with status {order.payment_status}")
                return jsonify({'status': 'OK'}), 200
            
            # Parse payment status
            new_status = tripay_client.parse_callback_status(callback_data)
            old_status = order.payment_status
            
            # Update order
            order.payment_status = new_status
            order.updated_at = datetime.utcnow()
            order.raw_callback_json = json.dumps(callback_data)
            
            if new_status == 'paid':
                order.paid_at = datetime.utcnow()
                order.invitation_status = 'processing'
                
                # Try to allocate ChatGPT account
                try:
                    allocation_result = AccountAllocator.assign_to_user(
                        order=order,
                        user_id=order.customer_email,
                        duration_days=30  # Default 30 days, can be made configurable
                    )
                    
                    if allocation_result['success']:
                        logger.info(f"Account allocated successfully for order {order.order_id}: {allocation_result['account_email']}")
                        
                        # Update invitation status to indicate account is ready
                        order.invitation_status = 'account_assigned'
                        
                        # Send notification email with account details
                        try:
                            send_payment_confirmation(order)
                        except Exception as e:
                            logger.error(f"Failed to send payment confirmation: {str(e)}")
                    
                    elif allocation_result.get('requires_manual_action'):
                        logger.warning(f"No available accounts for order {order.order_id}")
                        order.invitation_status = 'pending_stock'
                        
                        # Send admin notification about stock shortage
                        try:
                            send_admin_notification(
                                subject=f"Account Stock Alert - Order {order.order_id}",
                                message=f"No available ChatGPT accounts for paid order {order.order_id}. Customer: {order.customer_email}",
                                order=order
                            )
                        except Exception as e:
                            logger.error(f"Failed to send admin notification: {str(e)}")
                    
                    else:
                        logger.error(f"Account allocation failed for order {order.order_id}: {allocation_result.get('error')}")
                        order.invitation_status = 'allocation_failed'
                        
                except Exception as e:
                    logger.error(f"Error during account allocation for order {order.order_id}: {str(e)}")
                    order.invitation_status = 'allocation_failed'
            
            elif new_status in ['expired', 'failed']:
                # Release any existing assignments
                try:
                    existing_assignments = AccountAssignment.query.filter(
                        AccountAssignment.order_id == order.id,
                        AccountAssignment.status == 'ACTIVE'
                    ).all()
                    
                    for assignment in existing_assignments:
                        AccountAllocator.release_assignment(assignment, f"payment_{new_status}")
                        
                except Exception as e:
                    logger.error(f"Error releasing assignments for failed/expired order {order.order_id}: {str(e)}")
            
            db.session.commit()
            
            # Create audit log
            try:
                audit_log = AuditLog(
                    actor="tripay_webhook",
                    action="payment_status_updated",
                    entity="order",
                    entity_id=order.order_id,
                    payload=json.dumps({
                        'old_status': old_status,
                        'new_status': new_status,
                        'reference': reference,
                        'merchant_ref': callback_data.get('merchant_ref')
                    })
                )
                db.session.add(audit_log)
                db.session.commit()
            except Exception as e:
                logger.error(f"Failed to create audit log: {str(e)}")
            
            logger.info(f"Tripay callback processed successfully for order {order.order_id}: {old_status} -> {new_status}")
            
            return jsonify({'status': 'OK'}), 200
            
        except Exception as e:
            logger.error(f"Tripay callback processing error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/packages', methods=['GET'])
    def get_packages():
        """Get available packages"""
        try:
            packages = app.config['PACKAGES']
            return jsonify({'packages': packages})
        except Exception as e:
            logger.error(f"Error getting packages: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/admin/orders', methods=['GET'])
    @limiter.limit("100 per hour")
    def admin_get_orders():
        """Admin endpoint to get orders (basic implementation)"""
        try:
            # In production, add proper authentication here
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            
            orders = Order.query.order_by(Order.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return jsonify({
                'orders': [order.to_dict() for order in orders.items],
                'total': orders.total,
                'pages': orders.pages,
                'current_page': page
            })
            
        except Exception as e:
            logger.error(f"Error getting admin orders: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    # ChatGPT Account Management Endpoints
    @app.route('/api/admin/chatgpt-accounts', methods=['GET'])
    @limiter.limit("100 per hour")
    def admin_get_chatgpt_accounts():
        """Admin endpoint to get ChatGPT accounts"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            status_filter = request.args.get('status')
            
            query = ChatGPTAccount.query
            
            if status_filter:
                query = query.filter(ChatGPTAccount.status == status_filter.upper())
            
            accounts = query.order_by(ChatGPTAccount.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return jsonify({
                'accounts': [account.to_dict() for account in accounts.items],
                'total': accounts.total,
                'pages': accounts.pages,
                'current_page': page
            })
            
        except Exception as e:
            logger.error(f"Error getting ChatGPT accounts: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/admin/chatgpt-accounts', methods=['POST'])
    @limiter.limit("50 per hour")
    def admin_create_chatgpt_account():
        """Admin endpoint to create new ChatGPT account"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            email = data.get('email', '').strip()
            if not email:
                return jsonify({'error': 'Email is required'}), 400
            
            # Check if account already exists
            existing_account = ChatGPTAccount.query.filter_by(email=email).first()
            if existing_account:
                return jsonify({'error': 'Account with this email already exists'}), 400
            
            account = ChatGPTAccount(
                email=email,
                note=data.get('note', ''),
                status=data.get('status', 'AVAILABLE').upper(),
                max_seats=data.get('max_seats')
            )
            
            db.session.add(account)
            db.session.commit()
            
            # Create audit log
            audit_log = AuditLog(
                actor="admin",  # In production, get from authentication
                action="account_created",
                entity="chatgpt_account",
                entity_id=str(account.id),
                payload=json.dumps({
                    'email': email,
                    'status': account.status,
                    'max_seats': account.max_seats
                })
            )
            db.session.add(audit_log)
            db.session.commit()
            
            logger.info(f"ChatGPT account created: {email}")
            
            return jsonify({
                'success': True,
                'account': account.to_dict()
            }), 201
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating ChatGPT account: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/admin/chatgpt-accounts/<int:account_id>', methods=['PUT'])
    @limiter.limit("50 per hour")
    def admin_update_chatgpt_account(account_id):
        """Admin endpoint to update ChatGPT account"""
        try:
            account = ChatGPTAccount.query.get(account_id)
            if not account:
                return jsonify({'error': 'Account not found'}), 404
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            old_data = account.to_dict()
            
            # Update fields
            if 'note' in data:
                account.note = data['note']
            if 'status' in data:
                account.status = data['status'].upper()
            if 'max_seats' in data:
                account.max_seats = data['max_seats']
            
            account.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Create audit log
            audit_log = AuditLog(
                actor="admin",
                action="account_updated",
                entity="chatgpt_account",
                entity_id=str(account.id),
                payload=json.dumps({
                    'old_data': old_data,
                    'new_data': account.to_dict()
                })
            )
            db.session.add(audit_log)
            db.session.commit()
            
            logger.info(f"ChatGPT account updated: {account.email}")
            
            return jsonify({
                'success': True,
                'account': account.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating ChatGPT account: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/admin/account-assignments', methods=['GET'])
    @limiter.limit("100 per hour")
    def admin_get_account_assignments():
        """Admin endpoint to get account assignments"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            status_filter = request.args.get('status')
            user_filter = request.args.get('user_id')
            
            query = AccountAssignment.query
            
            if status_filter:
                query = query.filter(AccountAssignment.status == status_filter.upper())
            if user_filter:
                query = query.filter(AccountAssignment.user_id.ilike(f"%{user_filter}%"))
            
            assignments = query.order_by(AccountAssignment.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            # Enrich with related data
            assignment_data = []
            for assignment in assignments.items:
                assignment_dict = assignment.to_dict()
                assignment_dict['order'] = assignment.order.to_dict() if assignment.order else None
                assignment_dict['account'] = assignment.chatgpt_account.to_dict() if assignment.chatgpt_account else None
                assignment_data.append(assignment_dict)
            
            return jsonify({
                'assignments': assignment_data,
                'total': assignments.total,
                'pages': assignments.pages,
                'current_page': page
            })
            
        except Exception as e:
            logger.error(f"Error getting account assignments: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/admin/account-assignments/<int:assignment_id>/extend', methods=['POST'])
    @limiter.limit("50 per hour")
    def admin_extend_assignment(assignment_id):
        """Admin endpoint to extend an assignment"""
        try:
            assignment = AccountAssignment.query.get(assignment_id)
            if not assignment:
                return jsonify({'error': 'Assignment not found'}), 404
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            additional_days = data.get('additional_days', 0)
            if additional_days <= 0:
                return jsonify({'error': 'Additional days must be positive'}), 400
            
            result = AccountAllocator.extend_assignment(assignment, additional_days)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'assignment': assignment.to_dict(),
                    'new_end_at': result['new_end_at'].isoformat()
                })
            else:
                return jsonify({'error': result['error']}), 500
                
        except Exception as e:
            logger.error(f"Error extending assignment: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/admin/account-assignments/<int:assignment_id>/revoke', methods=['POST'])
    @limiter.limit("50 per hour")
    def admin_revoke_assignment(assignment_id):
        """Admin endpoint to revoke an assignment"""
        try:
            assignment = AccountAssignment.query.get(assignment_id)
            if not assignment:
                return jsonify({'error': 'Assignment not found'}), 404
            
            data = request.get_json() or {}
            reason = data.get('reason', 'admin_revoked')
            
            result = AccountAllocator.release_assignment(assignment, reason)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'assignment': assignment.to_dict()
                })
            else:
                return jsonify({'error': result['error']}), 500
                
        except Exception as e:
            logger.error(f"Error revoking assignment: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/admin/audit-logs', methods=['GET'])
    @limiter.limit("100 per hour")
    def admin_get_audit_logs():
        """Admin endpoint to get audit logs"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 50, type=int), 100)
            action_filter = request.args.get('action')
            entity_filter = request.args.get('entity')
            
            query = AuditLog.query
            
            if action_filter:
                query = query.filter(AuditLog.action == action_filter)
            if entity_filter:
                query = query.filter(AuditLog.entity == entity_filter)
            
            logs = query.order_by(AuditLog.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return jsonify({
                'logs': [log.to_dict() for log in logs.items],
                'total': logs.total,
                'pages': logs.pages,
                'current_page': page
            })
            
        except Exception as e:
            logger.error(f"Error getting audit logs: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def generate_status_message(order):
        """Generate human-readable status message"""
        if order.payment_status == 'pending':
            return "Menunggu pembayaran. Silakan selesaikan pembayaran sesuai instruksi."
        elif order.payment_status == 'failed':
            return "Pembayaran gagal. Silakan coba lagi atau hubungi support."
        elif order.payment_status == 'expired':
            return "Pembayaran kedaluwarsa. Silakan buat pesanan baru."
        elif order.payment_status == 'paid':
            if order.invitation_status == 'pending':
                return "Pembayaran berhasil. Proses undangan akan segera dimulai."
            elif order.invitation_status == 'processing':
                return "Pembayaran berhasil. Undangan sedang diproses dan akan dikirim dalam 5-30 menit."
            elif order.invitation_status == 'sent':
                return f"Undangan ChatGPT Plus telah dikirim ke {order.customer_email}. Silakan cek inbox dan spam folder."
            elif order.invitation_status == 'failed':
                return "Pembayaran berhasil, namun ada kendala dalam pengiriman undangan. Tim support akan menghubungi Anda."
            elif order.invitation_status == 'manual_review_required':
                return "Pembayaran berhasil. Undangan memerlukan review manual. Tim support akan menghubungi Anda segera."
        
        return "Status tidak diketahui. Silakan hubungi support."
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({'error': 'Method not allowed'}), 405
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({'error': 'Rate limit exceeded', 'message': str(e.description)}), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

def init_database(app):
    """Initialize database with default data"""
    with app.app_context():
        db.create_all()
        
        # Add default packages if they don't exist
        packages_config = app.config['PACKAGES']
        for package_id, package_data in packages_config.items():
            existing_package = Package.query.get(package_id)
            if not existing_package:
                package = Package(
                    id=package_id,
                    name=package_data['name'],
                    price=package_data['price'],
                    duration=package_data['duration'],
                    description=package_data['description']
                )
                db.session.add(package)
        
        db.session.commit()
        logger.info("Database initialized successfully")

if __name__ == '__main__':
    app = create_app()
    
    # Initialize database
    init_database(app)
    
    # Run development server
    app.run(host='0.0.0.0', port=5000, debug=True)