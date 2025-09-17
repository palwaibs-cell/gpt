# 🚀 Deployment Guide - Tripay Integration & Multi-Account ChatGPT Management

## Overview
This guide provides step-by-step instructions for deploying the new Tripay payment gateway integration with multi-account ChatGPT management system.

## 📋 Pre-Deployment Checklist

### 1. Tripay Account Setup
- [ ] Create Tripay merchant account
- [ ] Get merchant code, API key, and private key
- [ ] Set up webhook URL: `https://aksesgptmurah.tech/callback/tripay`
- [ ] Test in sandbox environment first

### 2. Environment Configuration
Update your `.env` file with the new variables:

```env
# Tripay Configuration (Primary)
TRIPAY_BASE_URL=https://tripay.co.id/api-sandbox/
TRIPAY_MERCHANT_CODE=your-merchant-code
TRIPAY_API_KEY=your-api-key
TRIPAY_PRIVATE_KEY=your-private-key
TRIPAY_CALLBACK_URL=https://aksesgptmurah.tech/callback/tripay

# Keep existing Midtrans as fallback
MIDTRANS_SERVER_KEY=your-existing-server-key
MIDTRANS_CLIENT_KEY=your-existing-client-key
MIDTRANS_IS_PRODUCTION=false
```

### 3. Database Migration
Run the migration to add new tables:

```bash
cd backend
flask db upgrade
```

This will create:
- `chatgpt_accounts` table
- `account_assignments` table  
- `audit_logs` table
- New columns in `orders` table

## 🔧 Deployment Steps

### Step 1: Code Deployment
```bash
# Pull latest code
git pull origin main

# Install any new dependencies
pip install -r requirements.txt

# Update database schema
flask db upgrade
```

### Step 2: Initial Data Setup
Add some ChatGPT accounts to the pool:

```bash
# Using the admin API or directly in database
POST /api/admin/chatgpt-accounts
{
  "email": "account1@chatgpt.com",
  "note": "Primary account",
  "status": "AVAILABLE",
  "max_seats": null
}
```

### Step 3: Celery Worker Update
Restart Celery workers to include new tasks:

```bash
# Stop existing workers
pkill -f celery

# Start new workers with updated tasks
celery -A celery_worker.celery worker --loglevel=info &
celery -A celery_worker.celery beat --loglevel=info &
```

### Step 4: Test Webhook
Test the Tripay webhook endpoint:

```bash
curl -X POST https://aksesgptmurah.tech/callback/tripay \
  -H "Content-Type: application/json" \
  -H "X-Callback-Event: payment_status" \
  -H "X-Callback-Signature: test-signature" \
  -d '{"reference": "test", "status": "PAID"}'
```

## 🧪 Testing Checklist

### Payment Flow Testing
- [ ] Create new order - should return Tripay checkout URL
- [ ] Complete payment in Tripay sandbox
- [ ] Verify webhook received and processed
- [ ] Check account allocation happened
- [ ] Verify customer received email with account details

### Admin Interface Testing
- [ ] Access admin endpoints for account management
- [ ] Create new ChatGPT account
- [ ] View account assignments
- [ ] Test extend/revoke functionality
- [ ] Check audit logs

### Fallback Testing
- [ ] Remove Tripay config temporarily
- [ ] Verify system falls back to Midtrans
- [ ] Restore Tripay config

## 🔄 Migration Strategy

### Phase 1: Soft Launch (Recommended)
1. Deploy with Tripay in sandbox mode
2. Test with small volume of transactions
3. Monitor logs and webhook processing
4. Gradually add ChatGPT accounts to pool

### Phase 2: Production Rollout
1. Switch Tripay to production mode
2. Update webhook URL to production
3. Monitor transaction processing
4. Scale up ChatGPT account pool

### Phase 3: Legacy Cleanup (Optional)
1. Once stable, can remove Midtrans fallback
2. Clean up old payment references
3. Update documentation

## 🚨 Monitoring & Alerts

### Key Metrics to Monitor
- **Account Pool Status**: Available vs Assigned accounts
- **Webhook Processing**: Success rate and response times  
- **Assignment Duration**: Average assignment periods
- **Error Rates**: Failed allocations or webhook processing

### Logs to Watch
- Tripay webhook processing: `/var/log/app/tripay_webhooks.log`
- Account allocation: `/var/log/app/account_allocation.log`
- Celery tasks: `/var/log/celery/worker.log`

### Alert Conditions
- Account pool running low (< 5 available)
- Webhook processing failures
- Database connection issues
- Celery worker down

## 🔧 Common Issues & Solutions

### Issue: No Available Accounts
**Symptom**: Orders paid but stuck in "pending_stock"
**Solution**: Add more ChatGPT accounts to pool via admin API

### Issue: Webhook Signature Mismatch
**Symptom**: 401 errors in webhook logs
**Solution**: Verify TRIPAY_PRIVATE_KEY matches Tripay dashboard

### Issue: Account Not Released
**Symptom**: Accounts stuck in ASSIGNED status
**Solution**: Check Celery beat scheduler and cleanup task

### Issue: Fallback to Midtrans
**Symptom**: Still getting Midtrans payment URLs
**Solution**: Check all Tripay environment variables are set

## 📞 Support Contacts

### Development Team
- **Technical Issues**: Check GitHub issues
- **Configuration Help**: Review documentation
- **Emergency Support**: System logs + error details

### Third Party Services
- **Tripay Support**: [Tripay Documentation](https://tripay.co.id/docs)
- **ChatGPT Issues**: OpenAI support channels

## 🎯 Success Criteria

### Technical Metrics
- [ ] 99%+ webhook processing success rate
- [ ] < 2 second account allocation time
- [ ] 100% HMAC signature verification
- [ ] Automated account cleanup working

### Business Metrics  
- [ ] Reduced manual account management
- [ ] Faster customer onboarding
- [ ] Better payment success rates
- [ ] Improved customer experience

---

**Deployment Date**: ___________  
**Deployed By**: ___________  
**Rollback Plan**: Restore previous code + disable Tripay config