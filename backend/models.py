from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

db = SQLAlchemy()

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_email = db.Column(db.String(255), nullable=False, index=True)
    full_name = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    package_id = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_status = db.Column(db.String(50), nullable=False, default='pending', index=True)
    invitation_status = db.Column(db.String(50), nullable=False, default='pending', index=True)
    payment_gateway_ref_id = db.Column(db.String(255), nullable=True, index=True)
    reference = db.Column(db.String(255), nullable=True, unique=True, index=True)  # Tripay reference
    paid_at = db.Column(db.DateTime, nullable=True)
    expired_at = db.Column(db.DateTime, nullable=True)
    raw_callback_json = db.Column(db.Text, nullable=True)  # Store raw callback for audit
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    invitation_logs = db.relationship('InvitationLog', backref='order', lazy=True, cascade='all, delete-orphan')
    account_assignments = db.relationship('AccountAssignment', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Order {self.order_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'customer_email': self.customer_email,
            'full_name': self.full_name,
            'phone_number': self.phone_number,
            'package_id': self.package_id,
            'amount': float(self.amount),
            'payment_status': self.payment_status,
            'invitation_status': self.invitation_status,
            'payment_gateway_ref_id': self.payment_gateway_ref_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ChatGPTAccount(db.Model):
    __tablename__ = 'chatgpt_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    note = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='AVAILABLE', index=True)  # AVAILABLE, ASSIGNED, SUSPENDED
    max_seats = db.Column(db.Integer, nullable=True)  # Optional seat limit
    current_seats_used = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignments = db.relationship('AccountAssignment', backref='chatgpt_account', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ChatGPTAccount {self.email}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'note': self.note,
            'status': self.status,
            'max_seats': self.max_seats,
            'current_seats_used': self.current_seats_used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AccountAssignment(db.Model):
    __tablename__ = 'account_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    user_id = db.Column(db.String(255), nullable=False, index=True)  # Will be customer_email for now
    chatgpt_account_id = db.Column(db.Integer, db.ForeignKey('chatgpt_accounts.id'), nullable=False, index=True)
    start_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='ACTIVE', index=True)  # ACTIVE, ENDED, REVOKED
    reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<AccountAssignment {self.id} - Order {self.order_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'user_id': self.user_id,
            'chatgpt_account_id': self.chatgpt_account_id,
            'start_at': self.start_at.isoformat() if self.start_at else None,
            'end_at': self.end_at.isoformat() if self.end_at else None,
            'status': self.status,
            'reason': self.reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    actor = db.Column(db.String(255), nullable=False)  # Who performed the action
    action = db.Column(db.String(100), nullable=False, index=True)  # What action was performed
    entity = db.Column(db.String(100), nullable=False, index=True)  # What entity was affected
    entity_id = db.Column(db.String(100), nullable=True, index=True)  # ID of the affected entity
    payload = db.Column(db.Text, nullable=True)  # JSON payload with details
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<AuditLog {self.id} - {self.action} on {self.entity}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'actor': self.actor,
            'action': self.action,
            'entity': self.entity,
            'entity_id': self.entity_id,
            'payload': self.payload,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class InvitationLog(db.Model):
    __tablename__ = 'invitation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    attempt_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False)  # 'success', 'failure', 'retry'
    error_message = db.Column(db.Text, nullable=True)
    screenshot_path = db.Column(db.String(255), nullable=True)
    retry_count = db.Column(db.Integer, nullable=False, default=0)
    
    def __repr__(self):
        return f'<InvitationLog {self.id} - Order {self.order_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'attempt_timestamp': self.attempt_timestamp.isoformat() if self.attempt_timestamp else None,
            'status': self.status,
            'error_message': self.error_message,
            'screenshot_path': self.screenshot_path,
            'retry_count': self.retry_count
        }

class Package(db.Model):
    __tablename__ = 'packages'
    
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Package {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': float(self.price),
            'duration': self.duration,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }