# Quick Fix Guide - Failed to Fetch Error

## Current Status

✗ Backend API returns **500 Internal Server Error**
✗ Frontend shows **"Failed to fetch"**
✓ CORS headers are correct
✓ API is accessible

## The Problem

Backend error 500 berarti ada error internal di server. Berdasarkan analisa kode, 99% masalahnya adalah:

**DATABASE BELUM DI-SETUP** ← Fix this first!

## Quick Fix (3 Steps)

### Step 1: Setup Database

Run script ini di server production:

```bash
cd backend
bash setup_database.sh
```

Script ini akan:
- ✓ Check MySQL running
- ✓ Create database `gptapp_db`
- ✓ Create user `gptuser`
- ✓ Initialize tables
- ✓ Verify everything works

**Jika MySQL belum installed:**
```bash
sudo apt update
sudo apt install mysql-server -y
sudo systemctl start mysql
sudo systemctl enable mysql
```

### Step 2: Restart Backend

```bash
cd backend

# Stop old backend
pkill -f "python.*app.py"

# Start new backend
python3 app.py

# Or for production with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app('production')"
```

### Step 3: Test

```bash
# Test API
curl -X POST https://api.aksesgptmurah.tech/api/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_email":"test@gmail.com","package_id":"chatgpt_plus_1_month","full_name":"Test","phone_number":"+628123456789"}'
```

**Expected success response:**
```json
{
  "success": true,
  "order_id": "INV-1234567890",
  "checkout_url": "https://tripay.co.id/checkout/...",
  "reference": "T123456789",
  "payment_method": "QRIS",
  "amount": 25000
}
```

**If still error 500:**
```bash
cd backend
python3 debug_server.py
# This will show detailed error message
```

## If Still Not Working

### Run Full Diagnostic

```bash
cd backend
python3 test_order_creation.py
```

This will test:
1. Environment variables ✓
2. Database connection ✓
3. Tripay API ✓
4. Full order creation ✓

Output akan show exactly mana yang error.

### Check Backend Logs

```bash
cd backend

# If running with app.py
python3 app.py
# Watch console for errors when submitting order

# If running with gunicorn
tail -f /var/log/gunicorn/error.log

# Or system logs
journalctl -u backend -n 50
```

### Debug Mode

Run backend in debug mode untuk lihat detailed error:

```bash
cd backend
python3 debug_server.py
```

Kemudian test dari frontend atau curl. Console akan show exact error.

## Frontend Fix

Setelah backend fixed:

1. **Hard Refresh Browser**
   ```
   Ctrl + Shift + R (Windows/Linux)
   Cmd + Shift + R (Mac)
   ```

2. **Clear Browser Cache**
   - Open Developer Tools (F12)
   - Application tab → Clear Storage → Clear all
   - Refresh

3. **Test in Incognito**
   - Open incognito/private window
   - Go to https://aksesgptmurah.tech
   - Test order

## Common Issues & Solutions

### Issue 1: MySQL Not Running

**Symptoms:**
```
Error: Can't connect to MySQL server
```

**Solution:**
```bash
sudo systemctl start mysql
sudo systemctl enable mysql
```

### Issue 2: Database Doesn't Exist

**Symptoms:**
```
Error: Unknown database 'gptapp_db'
```

**Solution:**
```bash
cd backend
bash setup_database.sh
```

### Issue 3: Tripay API Error

**Symptoms:**
```
Error: Payment gateway error
```

**Solution:**
```bash
# Verify Tripay credentials
cd backend
cat .env | grep TRIPAY

# Test Tripay API
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://tripay.co.id/api/merchant/payment-channel
```

Should return:
```json
{"success":true,"data":[...]}
```

If error, check:
- API key correct?
- IP whitelisted? (Already done: 34.34.229.15)
- Network accessible?

### Issue 4: Environment Variables Not Loaded

**Symptoms:**
```
Error: Missing Tripay credentials
```

**Solution:**
```bash
cd backend

# Check if .env exists
ls -la .env

# Check if variables loaded
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('DB:', os.getenv('DATABASE_URL')[:30] if os.getenv('DATABASE_URL') else 'NOT SET'); print('TRIPAY:', os.getenv('TRIPAY_API_KEY')[:10] if os.getenv('TRIPAY_API_KEY') else 'NOT SET')"
```

## Success Checklist

✓ MySQL running and accessible
✓ Database `gptapp_db` exists
✓ Tables created (orders, packages, etc)
✓ Backend running without errors
✓ API health check returns 200
✓ Create order returns success (not 500)
✓ Frontend redirects to Tripay payment

## Test Commands

```bash
# 1. Health check
curl https://api.aksesgptmurah.tech/health

# 2. Packages
curl https://api.aksesgptmurah.tech/api/packages

# 3. Create order (this should work after fix)
curl -X POST https://api.aksesgptmurah.tech/api/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_email":"your.email@gmail.com","package_id":"chatgpt_plus_1_month","full_name":"Your Name","phone_number":"+628123456789"}'

# 4. Should return:
# {"success":true,"order_id":"INV-...","checkout_url":"https://tripay.co.id/..."}
```

## Need Help?

Run these and send output:

```bash
# 1. Diagnostic
cd backend
python3 test_order_creation.py > diagnostic.txt 2>&1

# 2. Database check
mysql -h 127.0.0.1 -u gptuser -p'GptUser123!' gptapp_db -e "SHOW TABLES;" > db_tables.txt 2>&1

# 3. API test
bash test_api_direct.sh > api_test.txt 2>&1

# 4. Backend logs
cd backend
python3 app.py > backend.log 2>&1 &
# Submit order from frontend
# Then check
cat backend.log
```

Send:
- diagnostic.txt
- db_tables.txt
- api_test.txt
- backend.log

To: admin@aksesgptmurah.tech