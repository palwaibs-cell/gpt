# Backend Troubleshooting Guide

## Current Issue

API endpoint `/api/orders` mengembalikan **500 Internal Server Error** ketika mencoba create order.

### Test Results:
```bash
curl -X POST https://api.aksesgptmurah.tech/api/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_email":"test@gmail.com","package_id":"chatgpt_plus_1_month","full_name":"Test","phone_number":"+628123456789"}'

Response: {"error":"Internal server error"}
HTTP Status: 500
```

## Root Causes (Berdasarkan Analisa Kode)

### 1. Database Connection Issue (PALING UMUM)

Backend menggunakan MySQL database. Jika database tidak bisa diakses, order creation akan gagal di line 112:

```python
db.session.add(order)  # Akan throw exception jika DB tidak accessible
```

**Cek:**
```bash
cd backend
python3 test_order_creation.py
```

Atau manual check:
```bash
mysql -h 127.0.0.1 -u gptuser -p'GptUser123!' gptapp_db -e "SHOW TABLES;"
```

**Solusi:**
```bash
# 1. Pastikan MySQL running
sudo systemctl status mysql

# 2. Create database jika belum ada
mysql -u root -p
CREATE DATABASE IF NOT EXISTS gptapp_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'gptuser'@'localhost' IDENTIFIED BY 'GptUser123!';
GRANT ALL PRIVILEGES ON gptapp_db.* TO 'gptuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# 3. Initialize database tables
cd backend
python3 init_db.py
```

### 2. Tripay API Credentials Issue

Jika Tripay credentials salah atau API tidak bisa diakses, akan gagal di line 116-127:

```python
tripay_client = get_tripay_client()  # Line 116
payment_result = tripay_client.create_transaction(...)  # Line 127
```

**Cek:**
```bash
cd backend
python3 test_order_creation.py
```

Script ini akan test:
- ✓ Environment variables loaded
- ✓ Tripay API accessible
- ✓ Payment channels available

**Solusi:**

Verify credentials di `.env`:
```bash
cd backend
cat .env | grep TRIPAY
```

Should show:
```
TRIPAY_API_KEY=VI4hfWUhlfX70OZIjiae18pATyHOvNq0WjvBT6ej
TRIPAY_MERCHANT_CODE=T45484
TRIPAY_PRIVATE_KEY=2PW1G-zUdkm-EGiwn-femXJ-yEtIO
TRIPAY_IS_PRODUCTION=true
TRIPAY_BASE_URL=https://tripay.co.id/api
TRIPAY_CALLBACK_URL=https://api.aksesgptmurah.tech/callback/tripay
```

Test Tripay API manual:
```bash
curl -H "Authorization: Bearer VI4hfWUhlfX70OZIjiae18pATyHOvNq0WjvBT6ej" \
  https://tripay.co.id/api/merchant/payment-channel
```

### 3. Backend Not Running / Old Version Running

Backend mungkin tidak running, atau running old version tanpa latest changes.

**Cek:**
```bash
ps aux | grep "python.*app.py"
```

**Solusi:**
```bash
# Stop old backend
pkill -f "python.*app.py"

# Start new backend
cd backend
python3 app.py

# Atau dengan gunicorn untuk production
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app('production')"
```

### 4. Missing Dependencies

Python dependencies mungkin belum ter-install.

**Cek:**
```bash
cd backend
pip3 list | grep -E "Flask|SQLAlchemy|requests"
```

**Solusi:**
```bash
cd backend
pip3 install -r requirements.txt
```

### 5. Environment Variables Not Loaded

File `.env` ada tapi tidak ter-load oleh Flask app.

**Cek:**
```bash
cd backend
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('DB:', os.getenv('DATABASE_URL')[:30]); print('TRIPAY:', os.getenv('TRIPAY_API_KEY')[:10])"
```

**Solusi:**
Pastikan `python-dotenv` installed:
```bash
pip3 install python-dotenv
```

## Diagnostic Steps (In Order)

### Step 1: Check Backend Logs

Logs akan menunjukkan exact error:

```bash
cd backend

# If running with app.py
python3 app.py
# Watch for errors when you submit order

# If running with gunicorn
tail -f /var/log/gunicorn/error.log

# Or check system logs
journalctl -u backend -f
```

### Step 2: Run Diagnostic Script

```bash
cd backend
python3 test_order_creation.py
```

Output akan menunjukkan exact issue:
- ✓ Environment variables OK
- ✗ Database connection FAILED ← Issue found!
- ...

### Step 3: Test API Manually

```bash
bash test_api_direct.sh
```

Atau manual:
```bash
# Test health
curl https://api.aksesgptmurah.tech/health

# Test create order
curl -X POST https://api.aksesgptmurah.tech/api/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_email":"test@gmail.com","package_id":"chatgpt_plus_1_month","full_name":"Test","phone_number":"+628123456789"}'
```

### Step 4: Check Database

```bash
# Test MySQL connection
mysql -h 127.0.0.1 -u gptuser -p'GptUser123!' -e "SELECT 1;"

# Check if database exists
mysql -h 127.0.0.1 -u gptuser -p'GptUser123!' -e "SHOW DATABASES;" | grep gptapp_db

# Check if tables exist
mysql -h 127.0.0.1 -u gptuser -p'GptUser123!' gptapp_db -e "SHOW TABLES;"
```

If database doesn't exist:
```bash
cd backend
python3 init_db.py
```

### Step 5: Check Tripay API

```bash
curl -H "Authorization: Bearer VI4hfWUhlfX70OZIjiae18pATyHOvNq0WjvBT6ej" \
  https://tripay.co.id/api/merchant/payment-channel
```

Expected response:
```json
{
  "success": true,
  "message": "Success",
  "data": [...]
}
```

## Frontend "Failed to fetch" Issue

Frontend error "Failed to fetch" bisa disebabkan:

### 1. Backend 500 Error (Current Issue)

Backend mengembalikan 500, browser menampilkan "Failed to fetch" karena response tidak valid.

**Solusi:** Fix backend issue terlebih dahulu (lihat sections di atas)

### 2. CORS Issue

Browser block request karena CORS policy.

**Cek di Browser Console:**
- Buka Developer Tools (F12)
- Tab Console
- Cari error: "CORS policy" atau "Access-Control-Allow-Origin"

**Solusi:**
```bash
# Update backend/app.py CORS config
cd backend
# Restart backend
pkill -f "python.*app.py"
python3 app.py
```

### 3. Browser Cache

Browser menggunakan cached version dari frontend.

**Solusi:**
- Hard refresh: `Ctrl + Shift + R`
- Clear cache: Developer Tools → Application → Clear Storage
- Incognito window: Test di private/incognito mode

### 4. Wrong API URL

Frontend menggunakan wrong API URL (localhost instead of production).

**Cek di Browser Console:**
```javascript
console.log(import.meta.env.VITE_API_URL)
// Should output: https://api.aksesgptmurah.tech
```

**Solusi:**
```bash
# Frontend root
cat .env | grep VITE_API_URL
# Should show: VITE_API_URL=https://api.aksesgptmurah.tech

# Rebuild frontend
npm run build

# Deploy ulang
```

## Quick Fix Checklist

Run these commands in order:

```bash
# 1. Check if backend is running
curl https://api.aksesgptmurah.tech/health

# 2. Check if database is accessible
mysql -h 127.0.0.1 -u gptuser -p'GptUser123!' gptapp_db -e "SHOW TABLES;"

# 3. Initialize database if needed
cd backend && python3 init_db.py

# 4. Verify environment variables
cd backend && cat .env | grep -E "DATABASE_URL|TRIPAY_API_KEY"

# 5. Restart backend
pkill -f "python.*app.py"
cd backend && python3 app.py

# 6. Test order creation
curl -X POST https://api.aksesgptmurah.tech/api/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_email":"test@gmail.com","package_id":"chatgpt_plus_1_month","full_name":"Test","phone_number":"+628123456789"}'

# 7. If still error, run diagnostic
cd backend && python3 test_order_creation.py
```

## Success Indicators

### Backend Working Correctly:

**Health check:**
```bash
curl https://api.aksesgptmurah.tech/health
# Returns: {"status":"healthy",...}
```

**Create order:**
```bash
curl -X POST https://api.aksesgptmurah.tech/api/orders -H "Content-Type: application/json" -d '{...}'
# Returns: {"success":true,"order_id":"INV-...","checkout_url":"https://tripay.co.id/checkout/..."}
```

**Backend logs:**
```
INFO - Order created successfully: INV-1234567890
INFO - Tripay transaction created successfully
```

### Frontend Working Correctly:

1. Open website: https://aksesgptmurah.tech
2. Pilih paket
3. Isi form
4. Klik "Lanjutkan Pembayaran"
5. **Redirected ke Tripay payment page** ← This is success!

## Contact Support

Jika masih error setelah semua steps di atas:

1. **Jalankan diagnostic script:**
   ```bash
   cd backend
   python3 test_order_creation.py > diagnostic_output.txt 2>&1
   ```

2. **Collect logs:**
   ```bash
   # Backend logs
   tail -100 backend/app.log > backend_logs.txt 2>&1

   # Or if running directly
   python3 backend/app.py > backend_output.txt 2>&1 &
   # Submit order, then
   cat backend_output.txt
   ```

3. **Test API and save output:**
   ```bash
   bash test_api_direct.sh > api_test_results.txt 2>&1
   ```

4. **Send these files:**
   - diagnostic_output.txt
   - backend_logs.txt / backend_output.txt
   - api_test_results.txt

Email to: admin@aksesgptmurah.tech