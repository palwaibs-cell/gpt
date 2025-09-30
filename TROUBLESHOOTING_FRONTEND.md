# Troubleshooting: Frontend "Failed to fetch" Error

## Problem
Frontend menampilkan error "Failed to fetch" ketika submit order form, padahal backend API sudah running.

## Root Cause
Ada beberapa kemungkinan:

### 1. Environment Variable Tidak Ter-load
Frontend masih menggunakan old environment variable atau fallback ke localhost.

**Solusi:**
```bash
# Pastikan .env file ada dan benar
cat .env

# Harus ada line:
# VITE_API_URL=https://api.aksesgptmurah.tech

# Rebuild frontend
npm run build

# Deploy ulang ke server
```

### 2. Browser Cache
Browser masih menggunakan cached version dari frontend yang lama (mode demo).

**Solusi:**
- **Hard Refresh**: Tekan `Ctrl + Shift + R` (Windows/Linux) atau `Cmd + Shift + R` (Mac)
- **Clear Cache**:
  1. Buka Developer Tools (F12)
  2. Klik kanan pada tombol Refresh
  3. Pilih "Empty Cache and Hard Reload"
- **Incognito Mode**: Buka website di incognito/private window

### 3. Service Worker Cache
Service worker masih serving old cached version.

**Solusi:**
1. Buka Developer Tools (F12)
2. Pergi ke tab "Application" atau "Storage"
3. Klik "Service Workers" di sidebar kiri
4. Klik "Unregister" pada semua service workers
5. Refresh halaman

### 4. CORS Issue
Backend belum restart setelah update CORS configuration.

**Solusi:**
```bash
# Restart backend
cd backend
pkill -f "python app.py"
python app.py
```

### 5. Backend Database Tidak Tersedia
Backend mengalami error karena database tidak bisa diakses.

**Solusi:**
```bash
# Cek backend logs
cd backend
tail -f app.log

# Atau cek langsung error di console
python app.py

# Test database connection
python -c "from models import db; from app import create_app; app = create_app(); app.app_context().push(); db.create_all(); print('DB OK')"
```

## Quick Test - Backend API Manual

Test backend langsung dengan curl:

```bash
# Test health
curl https://api.aksesgptmurah.tech/health

# Test create order
curl -X POST https://api.aksesgptmurah.tech/api/orders \
  -H "Content-Type: application/json" \
  -H "Origin: https://aksesgptmurah.tech" \
  -d '{
    "customer_email": "your.email@gmail.com",
    "package_id": "chatgpt_plus_1_month",
    "full_name": "Your Name",
    "phone_number": "+628123456789"
  }'
```

Expected response (success):
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

Expected response (error):
```json
{
  "error": "Internal server error"
}
```

Jika dapat "Internal server error", cek backend logs untuk detail error.

## Quick Test - Frontend API URL

Buka browser console (F12) dan jalankan:

```javascript
// Check API URL yang digunakan
console.log(import.meta.env.VITE_API_URL);

// Should output: https://api.aksesgptmurah.tech
```

Jika output `undefined` atau `http://localhost:5000`, berarti environment variable tidak ter-load.

## Solution Steps (In Order)

1. **Hard Refresh Browser**
   - Ctrl+Shift+R atau Empty Cache and Hard Reload

2. **Verify Environment Variable**
   ```bash
   cat .env | grep VITE_API_URL
   ```

3. **Rebuild Frontend**
   ```bash
   npm run build
   ```

4. **Restart Backend**
   ```bash
   cd backend
   python app.py
   ```

5. **Clear Browser Cache + Incognito Test**
   - Test di incognito window

6. **Check Backend Logs**
   ```bash
   cd backend
   tail -f app.log
   # atau
   python app.py  # lihat error di console
   ```

## Still Not Working?

### Check Network Tab
1. Buka Developer Tools (F12)
2. Pergi ke tab "Network"
3. Try submit form lagi
4. Lihat request yang gagal
5. Check:
   - Request URL: Harus ke `https://api.aksesgptmurah.tech/api/orders`
   - Status: Jika 0 atau failed = network/CORS issue
   - Response: Lihat error message

### Common Network Tab Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Failed to fetch` | CORS/Network issue | Clear cache, restart backend |
| `net::ERR_CERT_AUTHORITY_INVALID` | SSL certificate issue | Fix SSL cert on server |
| `net::ERR_CONNECTION_REFUSED` | Backend not running | Start backend server |
| `HTTP 500` | Backend internal error | Check backend logs |
| `HTTP 404` | Wrong endpoint | Verify API URL |

## Contact Support

Jika masih error, kirim informasi berikut:
1. Screenshot error di browser console
2. Screenshot Network tab
3. Backend logs (`tail -50 backend/app.log`)
4. Output dari: `curl https://api.aksesgptmurah.tech/health`