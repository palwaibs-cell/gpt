# 👨‍💼 Admin Management Guide - ChatGPT Account Pool

## Overview
This guide explains how to manage the ChatGPT account pool and monitor the multi-account system.

## 🏗️ Initial Setup

### 1. Add ChatGPT Accounts to Pool
Use the admin API to add accounts:

```bash
curl -X POST https://aksesgptmurah.tech/api/admin/chatgpt-accounts \
  -H "Content-Type: application/json" \
  -d '{
    "email": "account1@yourdomain.com",
    "note": "Primary account - Team lead",
    "status": "AVAILABLE",
    "max_seats": null
  }'
```

### 2. Bulk Import Accounts
For multiple accounts, you can create a script:

```python
import requests

accounts = [
    {"email": "team1@yourdomain.com", "note": "Team 1 account", "max_seats": 5},
    {"email": "team2@yourdomain.com", "note": "Team 2 account", "max_seats": 3},
    {"email": "individual1@yourdomain.com", "note": "Individual account", "max_seats": null}
]

for account in accounts:
    response = requests.post(
        "https://aksesgptmurah.tech/api/admin/chatgpt-accounts",
        json=account
    )
    print(f"Added {account['email']}: {response.status_code}")
```

## 📊 Daily Management Tasks

### Monitor Account Pool Status
```bash
# Check available accounts
curl https://aksesgptmurah.tech/api/admin/chatgpt-accounts?status=AVAILABLE

# Check assigned accounts
curl https://aksesgptmurah.tech/api/admin/chatgpt-accounts?status=ASSIGNED
```

### View Active Assignments
```bash
# Get all active assignments
curl https://aksesgptmurah.tech/api/admin/account-assignments?status=ACTIVE

# Check assignments ending soon (implement custom filter)
curl https://aksesgptmurah.tech/api/admin/account-assignments?status=ACTIVE&ending_soon=true
```

### Review Recent Activity
```bash
# Check recent audit logs
curl https://aksesgptmurah.tech/api/admin/audit-logs?page=1&per_page=50
```

## 🔧 Common Admin Operations

### Extend Customer Access
When customer requests extension:

```bash
curl -X POST https://aksesgptmurah.tech/api/admin/account-assignments/123/extend \
  -H "Content-Type: application/json" \
  -d '{"additional_days": 30}'
```

### Revoke Access (Refund/Violation)
```bash
curl -X POST https://aksesgptmurah.tech/api/admin/account-assignments/123/revoke \
  -H "Content-Type: application/json" \
  -d '{"reason": "Customer refund requested"}'
```

### Suspend Account (Maintenance)
```bash
curl -X PUT https://aksesgptmurah.tech/api/admin/chatgpt-accounts/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "SUSPENDED", "note": "Under maintenance"}'
```

### Reactivate Account
```bash
curl -X PUT https://aksesgptmurah.tech/api/admin/chatgpt-accounts/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "AVAILABLE", "note": "Back in service"}'
```

## 📈 Monitoring & Alerts

### Daily Metrics to Check
1. **Available Account Count**: Should maintain minimum buffer
2. **Assignment Success Rate**: Should be near 100%
3. **Average Assignment Duration**: Track usage patterns
4. **Customer Satisfaction**: Monitor support tickets

### Weekly Tasks
1. **Review Audit Logs**: Check for anomalies
2. **Account Utilization**: Identify underused accounts
3. **Capacity Planning**: Forecast account needs
4. **Performance Review**: Check system metrics

### Monthly Tasks
1. **Account Pool Optimization**: Add/remove accounts as needed
2. **Access Pattern Analysis**: Understand customer behavior
3. **System Health Check**: Database, performance, logs
4. **Documentation Updates**: Keep procedures current

## 🚨 Emergency Procedures

### Out of Accounts Alert
**When**: Available accounts < 5
**Action**:
1. Add emergency accounts immediately
2. Check for stuck assignments
3. Contact ChatGPT account team
4. Notify development team

### Mass Account Failure
**When**: Multiple accounts suspended/failed
**Action**:
1. Switch to manual assignment mode
2. Investigate root cause
3. Contact ChatGPT support
4. Prepare customer communication

### System Downtime
**When**: API/webhook failures
**Action**:
1. Check system status
2. Review error logs
3. Contact technical team
4. Implement fallback procedures

## 📋 Account Types & Configuration

### Single-User Accounts
```json
{
  "email": "individual@example.com",
  "max_seats": null,
  "note": "Single user account"
}
```
- One customer per account
- Account marked as ASSIGNED when in use
- Automatically released on expiration

### Multi-Seat Team Accounts
```json
{
  "email": "team@example.com", 
  "max_seats": 5,
  "note": "Team account - 5 seats"
}
```
- Multiple customers can use same account
- Tracks seat usage with `current_seats_used`
- Marked ASSIGNED when all seats taken

## 🔍 Troubleshooting Guide

### Customer Can't Access Account
1. Check assignment status in admin panel
2. Verify account is ACTIVE
3. Check assignment end date
4. Review audit logs for issues

### Account Stuck in ASSIGNED
1. Check for active assignments
2. Review assignment end dates
3. Manual release if needed
4. Check Celery cleanup task

### Payment Processed but No Account Assigned
1. Check webhook processing logs
2. Verify account pool has availability
3. Review order status
4. Manual assignment if needed

## 📊 Reporting & Analytics

### Weekly Report Template
```
Week of: [Date]

Account Pool Status:
- Total Accounts: X
- Available: X
- Assigned: X  
- Suspended: X

Assignment Metrics:
- New Assignments: X
- Expired Assignments: X
- Manual Extensions: X
- Revocations: X

Issues:
- [List any issues and resolutions]

Actions Needed:
- [List upcoming tasks]
```

### Monthly Business Review
- Account utilization rates
- Customer retention metrics
- System performance trends
- Capacity planning recommendations

---

**Remember**: Always test admin operations in staging environment first!

**Support Contact**: Keep this guide updated as system evolves.