import json
import logging
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import and_
from sqlalchemy.orm import selectinload

from models import db, ChatGPTAccount, AccountAssignment, AuditLog

logger = logging.getLogger(__name__)


class AccountAllocator:
    """Service for managing ChatGPT account allocation and assignment"""
    
    @staticmethod
    def pick_available_account():
        """
        Pick an available ChatGPT account for assignment
        Returns the account or None if no account is available
        """
        try:
            # Find available accounts with SELECT FOR UPDATE to prevent race conditions
            available_account = db.session.query(ChatGPTAccount).filter(
                and_(
                    ChatGPTAccount.status == 'AVAILABLE',
                    db.or_(
                        ChatGPTAccount.max_seats.is_(None),  # No seat limit
                        ChatGPTAccount.current_seats_used < ChatGPTAccount.max_seats  # Has available seats
                    )
                )
            ).with_for_update().first()
            
            return available_account
            
        except Exception as e:
            logger.error(f"Error picking available account: {str(e)}")
            raise
    
    @staticmethod
    def assign_to_user(order, user_id, duration_days=30):
        """
        Assign a ChatGPT account to a user
        Args:
            order: Order object
            user_id: User identifier (email)
            duration_days: Assignment duration in days
        Returns:
            dict with success status and assignment details
        """
        try:
            # Start transaction
            with db.session.begin():
                # Pick available account
                account = AccountAllocator.pick_available_account()
                
                if not account:
                    logger.warning(f"No available ChatGPT accounts for order {order.order_id}")
                    return {
                        'success': False,
                        'error': 'No available ChatGPT accounts',
                        'requires_manual_action': True
                    }
                
                # Calculate assignment period
                start_at = datetime.utcnow()
                end_at = start_at + timedelta(days=duration_days)
                
                # Create assignment
                assignment = AccountAssignment(
                    order_id=order.id,
                    user_id=user_id,
                    chatgpt_account_id=account.id,
                    start_at=start_at,
                    end_at=end_at,
                    status='ACTIVE'
                )
                
                db.session.add(assignment)
                
                # Update account status/seats
                if account.max_seats is None:
                    # Single-user account, mark as assigned
                    account.status = 'ASSIGNED'
                else:
                    # Multi-seat account, increment used seats
                    account.current_seats_used += 1
                    if account.current_seats_used >= account.max_seats:
                        account.status = 'ASSIGNED'  # Mark as full
                
                account.updated_at = datetime.utcnow()
                
                # Create audit log
                audit_log = AuditLog(
                    actor=f"system",
                    action="account_assigned",
                    entity="account_assignment",
                    entity_id=str(assignment.id),
                    payload=json.dumps({
                        'order_id': order.order_id,
                        'user_id': user_id,
                        'account_email': account.email,
                        'duration_days': duration_days,
                        'start_at': start_at.isoformat(),
                        'end_at': end_at.isoformat()
                    })
                )
                db.session.add(audit_log)
                
                # Flush to get assignment ID
                db.session.flush()
                
                logger.info(f"Account {account.email} assigned to user {user_id} for order {order.order_id}")
                
                return {
                    'success': True,
                    'assignment_id': assignment.id,
                    'account_email': account.email,
                    'start_at': start_at,
                    'end_at': end_at
                }
                
        except Exception as e:
            logger.error(f"Error assigning account to user: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def release_assignment(assignment, reason="expired"):
        """
        Release an account assignment
        Args:
            assignment: AccountAssignment object
            reason: Reason for release
        Returns:
            dict with success status
        """
        try:
            with db.session.begin():
                # Get the associated account
                account = assignment.chatgpt_account
                
                # Update assignment status
                assignment.status = 'ENDED'
                assignment.reason = reason
                assignment.updated_at = datetime.utcnow()
                
                # Release account
                if account.max_seats is None:
                    # Single-user account, mark as available
                    account.status = 'AVAILABLE'
                else:
                    # Multi-seat account, decrement used seats
                    account.current_seats_used = max(0, account.current_seats_used - 1)
                    account.status = 'AVAILABLE'  # Mark as available again
                
                account.updated_at = datetime.utcnow()
                
                # Create audit log
                audit_log = AuditLog(
                    actor="system",
                    action="account_released",
                    entity="account_assignment",
                    entity_id=str(assignment.id),
                    payload=json.dumps({
                        'account_email': account.email,
                        'user_id': assignment.user_id,
                        'reason': reason,
                        'released_at': datetime.utcnow().isoformat()
                    })
                )
                db.session.add(audit_log)
                
                logger.info(f"Account {account.email} released from user {assignment.user_id}, reason: {reason}")
                
                return {
                    'success': True,
                    'account_email': account.email,
                    'user_id': assignment.user_id
                }
                
        except Exception as e:
            logger.error(f"Error releasing assignment: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def extend_assignment(assignment, additional_days):
        """
        Extend an existing assignment
        Args:
            assignment: AccountAssignment object
            additional_days: Days to add to current end_at
        Returns:
            dict with success status
        """
        try:
            with db.session.begin():
                old_end_at = assignment.end_at
                assignment.end_at = assignment.end_at + timedelta(days=additional_days)
                assignment.updated_at = datetime.utcnow()
                
                # Create audit log
                audit_log = AuditLog(
                    actor="admin",  # Assume admin action
                    action="assignment_extended",
                    entity="account_assignment",
                    entity_id=str(assignment.id),
                    payload=json.dumps({
                        'user_id': assignment.user_id,
                        'additional_days': additional_days,
                        'old_end_at': old_end_at.isoformat(),
                        'new_end_at': assignment.end_at.isoformat()
                    })
                )
                db.session.add(audit_log)
                
                logger.info(f"Assignment {assignment.id} extended by {additional_days} days")
                
                return {
                    'success': True,
                    'new_end_at': assignment.end_at
                }
                
        except Exception as e:
            logger.error(f"Error extending assignment: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_expired_assignments():
        """Get all expired assignments that need to be released"""
        try:
            now = datetime.utcnow()
            expired_assignments = db.session.query(AccountAssignment).filter(
                and_(
                    AccountAssignment.status == 'ACTIVE',
                    AccountAssignment.end_at <= now
                )
            ).options(selectinload(AccountAssignment.chatgpt_account)).all()
            
            return expired_assignments
            
        except Exception as e:
            logger.error(f"Error getting expired assignments: {str(e)}")
            return []
    
    @staticmethod
    def cleanup_expired_assignments():
        """Cleanup all expired assignments - meant to be run as a cron job"""
        try:
            expired_assignments = AccountAllocator.get_expired_assignments()
            
            released_count = 0
            for assignment in expired_assignments:
                result = AccountAllocator.release_assignment(assignment, "expired")
                if result['success']:
                    released_count += 1
            
            logger.info(f"Released {released_count} expired assignments")
            
            return {
                'success': True,
                'released_count': released_count,
                'total_expired': len(expired_assignments)
            }
            
        except Exception as e:
            logger.error(f"Error during expired assignments cleanup: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_assignment_for_user(user_id):
        """Get active assignment for a user"""
        try:
            assignment = db.session.query(AccountAssignment).filter(
                and_(
                    AccountAssignment.user_id == user_id,
                    AccountAssignment.status == 'ACTIVE'
                )
            ).options(selectinload(AccountAssignment.chatgpt_account)).first()
            
            return assignment
            
        except Exception as e:
            logger.error(f"Error getting assignment for user {user_id}: {str(e)}")
            return None