# Fix "Failed to Fetch" Error - SOLUSI LENGKAP

## MASALAH DITEMUKAN ✓

Backend menggunakan **MySQL database yang TIDAK ADA**, padahal **Supabase PostgreSQL sudah tersedia dan siap pakai**.

Ini sebabnya terus error 500 dan frontend menampilkan "Failed to fetch".

## SOLUSI (2 CARA)

### Cara 1: Automatic Script (PALING MUDAH)

Jalankan script ini di server production:

```bash
bash fix-backend.sh
```

Script akan guide step-by-step untuk:
1. Input Supabase password
2. Update backend/.env
3. Test database connection
4. Apply migration
5. Restart backend

**Estimasi waktu: 5 menit**

### Cara 2: Manual Setup

Baca guide lengkap: **[SUPABASE_SETUP_GUIDE.md](./SUPABASE_SETUP_GUIDE.md)**

## Quick Steps (Manual)

### 1. Get Supabase Password

Go to: https://supabase.com/dashboard
- Project: **0ec90b57d6e95fcbda19832f**
- Settings → Database → Connection string (Direct)
- Copy password dari:
  ```
  postgresql://postgres:[PASSWORD]@db.0ec90b57d6e95fcbda19832f.supabase.co:5432/postgres
  ```

### 2. Update backend/.env

```bash
cd backend
nano .env
```

Add:
```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.0ec90b57d6e95fcbda19832f.supabase.co:5432/postgres
TRIPAY_API_KEY=VI4hfWUhlfX70OZIjiae18pATyHOvNq0WjvBT6ej
TRIPAY_MERCHANT_CODE=T45484
TRIPAY_PRIVATE_KEY=2PW1G-zUdkm-EGiwn-femXJ-yEtIO
TRIPAY_IS_PRODUCTION=true
TRIPAY_CALLBACK_URL=https://api.aksesgptmurah.tech/callback/tripay
API_BASE_URL=https://api.aksesgptmurah.tech
FRONTEND_URL=https://aksesgptmurah.tech
ALLOWED_ORIGINS=https://aksesgptmurah.tech
```

### 3. Apply Migration

**Via Supabase Dashboard:**
1. Go to: SQL Editor
2. New query
3. Copy-paste from: `supabase/migrations/20250930100000_create_orders_tables.sql`
4. Run

**Or via psql:**
```bash
psql "postgresql://postgres:[PASSWORD]@db.0ec90b57d6e95fcbda19832f.supabase.co:5432/postgres" -f supabase/migrations/20250930100000_create_orders_tables.sql
```

### 4. Restart Backend

```bash
cd backend
pkill -f "python.*app.py"
python3 app.py
```

### 5. Test

```bash
curl https://api.aksesgptmurah.tech/health
# Should return: {"status":"healthy"}

curl -X POST https://api.aksesgptmurah.tech/api/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_email":"test@gmail.com","package_id":"chatgpt_plus_1_month","full_name":"Test","phone_number":"+628123456789"}'
# Should return: {"success":true,"checkout_url":"..."}
```

## Verifikasi Sukses

✓ Backend health check returns 200
✓ Create order returns success (bukan 500)
✓ Frontend redirect ke Tripay payment page
✓ Tidak ada error "Failed to fetch"

## Files yang Diubah

1. **backend/config.py** - Ganti MySQL ke PostgreSQL
2. **backend/.env** - Tambah Supabase connection string
3. **supabase/migrations/20250930100000_create_orders_tables.sql** - Create tables

## Dokumentasi Lengkap

- **[SUPABASE_SETUP_GUIDE.md](./SUPABASE_SETUP_GUIDE.md)** - Complete setup guide
- **[QUICK_FIX_GUIDE.md](./QUICK_FIX_GUIDE.md)** - Quick troubleshooting
- **[BACKEND_TROUBLESHOOTING.md](./BACKEND_TROUBLESHOOTING.md)** - Detailed debugging

## Troubleshooting

### Masih error setelah setup?

**Check logs:**
```bash
cd backend
python3 app.py
# Watch console for errors
```

**Test database:**
```bash
psql "postgresql://postgres:[PASSWORD]@db.0ec90b57d6e95fcbda19832f.supabase.co:5432/postgres" -c "\dt"
# Should show: packages, orders, invitation_logs, admin_accounts
```

**Run diagnostic:**
```bash
cd backend
python3 test_order_creation.py
# Will show exactly what's wrong
```

## Kenapa Ini Terjadi?

Backend code awalnya di-setup untuk MySQL:
```python
DATABASE_URL = 'mysql+pymysql://gptuser:GptUser123!@127.0.0.1/gptapp_db'
```

Tapi MySQL tidak installed di server, dan database `gptapp_db` tidak ada.

Ketika backend mencoba `db.session.add(order)`, akan throw exception karena tidak bisa connect ke database.

Result: **500 Internal Server Error**

Frontend melihat 500 response dan menampilkan: **"Failed to fetch"**

## Solusi Final

Gunakan Supabase PostgreSQL yang sudah available:
```python
DATABASE_URL = 'postgresql://postgres:[PASSWORD]@db.0ec90b57d6e95fcbda19832f.supabase.co:5432/postgres'
```

Database berfungsi, tables created, backend works, frontend works!

## Need Help?

1. Pastikan sudah jalankan `fix-backend.sh` atau ikuti manual steps
2. Check backend logs untuk error messages
3. Verify database connection dengan psql
4. Test API endpoints dengan curl
5. Jika masih stuck, share error logs

## Success Indicators

Ketika sudah berhasil:
- Health check: ✓ 200 OK
- Create order: ✓ Returns checkout_url
- Frontend: ✓ Redirect ke Tripay
- No more "Failed to fetch" error
- Orders saved to Supabase database

Happy fixing!