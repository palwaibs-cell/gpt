import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from flask import Flask
import sys
import os
import json

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.account_allocator import AccountAllocator


class TestAccountAllocator(unittest.TestCase):
    def setUp(self):
        """Set up test app"""
        self.app = Flask(__name__)
        self.app.config.update({
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False
        })
    
    @patch('services.account_allocator.db')
    @patch('services.account_allocator.ChatGPTAccount')
    def test_pick_available_account_success(self, mock_chatgpt_account, mock_db):
        """Test picking an available account successfully"""
        # Mock available account
        mock_account = MagicMock()
        mock_account.id = 1
        mock_account.email = 'test@chatgpt.com'
        mock_account.status = 'AVAILABLE'
        mock_account.max_seats = None
        
        mock_db.session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = mock_account
        
        result = AccountAllocator.pick_available_account()
        
        self.assertEqual(result, mock_account)
    
    @patch('services.account_allocator.db')
    @patch('services.account_allocator.ChatGPTAccount')
    def test_pick_available_account_none_available(self, mock_chatgpt_account, mock_db):
        """Test picking account when none available"""
        mock_db.session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None
        
        result = AccountAllocator.pick_available_account()
        
        self.assertIsNone(result)
    
    @patch('services.account_allocator.db')
    @patch('services.account_allocator.AuditLog')
    @patch('services.account_allocator.AccountAssignment')
    def test_assign_to_user_success(self, mock_assignment, mock_audit_log, mock_db):
        """Test successful account assignment"""
        # Mock order and account
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_id = 'ORD123'
        
        mock_account = MagicMock()
        mock_account.id = 1
        mock_account.email = 'test@chatgpt.com'
        mock_account.status = 'AVAILABLE'
        mock_account.max_seats = None
        
        # Mock AccountAllocator.pick_available_account
        with patch.object(AccountAllocator, 'pick_available_account', return_value=mock_account):
            # Mock database session
            mock_db.session.begin.return_value.__enter__ = MagicMock()
            mock_db.session.begin.return_value.__exit__ = MagicMock()
            mock_db.session.add = MagicMock()
            mock_db.session.flush = MagicMock()
            
            result = AccountAllocator.assign_to_user(
                order=mock_order,
                user_id='user@example.com',
                duration_days=30
            )
            
            self.assertTrue(result['success'])
            self.assertEqual(result['account_email'], 'test@chatgpt.com')
            self.assertIn('assignment_id', result)
    
    @patch('services.account_allocator.db')
    def test_assign_to_user_no_accounts_available(self, mock_db):
        """Test assignment when no accounts available"""
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_id = 'ORD123'
        
        # Mock AccountAllocator.pick_available_account returning None
        with patch.object(AccountAllocator, 'pick_available_account', return_value=None):
            result = AccountAllocator.assign_to_user(
                order=mock_order,
                user_id='user@example.com',
                duration_days=30
            )
            
            self.assertFalse(result['success'])
            self.assertTrue(result['requires_manual_action'])
            self.assertIn('No available ChatGPT accounts', result['error'])
    
    @patch('services.account_allocator.db')
    @patch('services.account_allocator.AuditLog')
    def test_release_assignment_success(self, mock_audit_log, mock_db):
        """Test successful assignment release"""
        # Mock assignment and account
        mock_assignment = MagicMock()
        mock_assignment.id = 1
        mock_assignment.user_id = 'user@example.com'
        
        mock_account = MagicMock()
        mock_account.id = 1
        mock_account.email = 'test@chatgpt.com'
        mock_account.max_seats = None
        
        mock_assignment.chatgpt_account = mock_account
        
        # Mock database session
        mock_db.session.begin.return_value.__enter__ = MagicMock()
        mock_db.session.begin.return_value.__exit__ = MagicMock()
        mock_db.session.add = MagicMock()
        
        result = AccountAllocator.release_assignment(mock_assignment, 'expired')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['account_email'], 'test@chatgpt.com')
        self.assertEqual(result['user_id'], 'user@example.com')
    
    @patch('services.account_allocator.db')
    @patch('services.account_allocator.AccountAssignment')
    def test_get_expired_assignments(self, mock_assignment, mock_db):
        """Test getting expired assignments"""
        # Mock expired assignments
        mock_expired_assignment = MagicMock()
        mock_expired_assignment.id = 1
        mock_expired_assignment.status = 'ACTIVE'
        mock_expired_assignment.end_at = datetime.utcnow() - timedelta(hours=1)
        
        mock_db.session.query.return_value.filter.return_value.options.return_value.all.return_value = [mock_expired_assignment]
        
        result = AccountAllocator.get_expired_assignments()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], mock_expired_assignment)
    
    def test_cleanup_expired_assignments_success(self):
        """Test successful cleanup of expired assignments"""
        # Mock expired assignments
        mock_assignment1 = MagicMock()
        mock_assignment2 = MagicMock()
        
        with patch.object(AccountAllocator, 'get_expired_assignments', return_value=[mock_assignment1, mock_assignment2]):
            with patch.object(AccountAllocator, 'release_assignment', side_effect=[
                {'success': True}, {'success': True}
            ]):
                result = AccountAllocator.cleanup_expired_assignments()
                
                self.assertTrue(result['success'])
                self.assertEqual(result['released_count'], 2)
                self.assertEqual(result['total_expired'], 2)


if __name__ == '__main__':
    unittest.main()