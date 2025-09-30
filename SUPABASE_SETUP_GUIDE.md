# Supabase Setup Guide - Fix "Failed to Fetch" Error

## THE PROBLEM

Backend menggunakan MySQL database yang **TIDAK ADA**, padahal **Supabase PostgreSQL database sudah tersedia dan siap pakai**.

Ini kenapa terus error 500 Internal Server Error!

## THE SOLUTION

Migrate backend dari MySQL ke Supabase PostgreSQL (already configured in this project).

## Step-by-Step Setup

### Step 1: Get Supabase Database Password

1. Buka Supabase Dashboard: https://supabase.com/dashboard
2. Pilih project: **0ec90b57d6e95fcbda19832f**
3. Go to: **Settings** → **Database**
4. Scroll ke **Connection string** section
5. Pilih tab: **Direct connection** (bukan pooled!)
6. Copy password dari connection string:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.0ec90b57d6e95fcbda19832f.supabase.co:5432/postgres
   ```

   Password adalah bagian antara `postgres:` dan `@db.`

### Step 2: Update Backend .env File

Edit file `backend/.env` dan update DATABASE_URL:

```bash
cd backend
nano .env
```

Update line ini:
```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.0ec90b57d6e95fcbda19832f.supabase.co:5432/postgres
```

Ganti `[YOUR-PASSWORD]` dengan password dari Step 1.

**Full backend/.env example:**
```env
# Supabase Database
DATABASE_URL=postgresql://postgres:your-actual-password-here@db.0ec90b57d6e95fcbda19832f.supabase.co:5432/postgres

# Flask
FLASK_ENV=production
SECRET_KEY=your-secret-key

# Tripay (already correct)
TRIPAY_API_KEY=VI4hfWUhlfX70OZIjiae18pATyHOvNq0WjvBT6ej
TRIPAY_MERCHANT_CODE=T45484
TRIPAY_PRIVATE_KEY=2PW1G-zUdkm-EGiwn-femXJ-yEtIO
TRIPAY_IS_PRODUCTION=true
TRIPAY_BASE_URL=https://tripay.co.id/api
TRIPAY_CALLBACK_URL=https://api.aksesgptmurah.tech/callback/tripay

# API URLs (already correct)
API_BASE_URL=https://api.aksesgptmurah.tech
FRONTEND_URL=https://aksesgptmurah.tech
ALLOWED_ORIGINS=https://aksesgptmurah.tech

# Other settings
ENABLE_CELERY=false
EMAIL_ENABLED=false
RATE_LIMIT_STORAGE_URL=memory://
```

### Step 3: Apply Database Migration

The migration file is already created. Just need to apply it to Supabase:

**Option A: Via Supabase Dashboard (RECOMMENDED)**

1. Go to Supabase Dashboard: https://supabase.com/dashboard
2. Select project: **0ec90b57d6e95fcbda19832f**
3. Go to: **SQL Editor**
4. Click: **New query**
5. Copy paste isi dari file: `supabase/migrations/20250930100000_create_orders_tables.sql`
6. Click: **Run**
7. Should see: "Success. No rows returned"

**Option B: Via Command Line**

```bash
# Install psql if not already installed
sudo apt install postgresql-client -y

# Run migration
psql "postgresql://postgres:[YOUR-PASSWORD]@db.0ec90b57d6e95fcbda19832f.supabase.co:5432/postgres" -f supabase/migrations/20250930100000_create_orders_tables.sql
```

### Step 4: Verify Database Setup

Check if tables are created:

```bash
# Via psql
psql "postgresql://postgres:[YOUR-PASSWORD]@db.0ec90b57d6e95fcbda19832f.supabase.co:5432/postgres" -c "\dt"

# Should show:
#  public | admin_accounts    | table | postgres
#  public | invitation_logs   | table | postgres
#  public | orders            | table | postgres
#  public | packages          | table | postgres
```

Or via Supabase Dashboard:
1. Go to: **Table Editor**
2. Should see tables: `packages`, `orders`, `invitation_logs`, `admin_accounts`

### Step 5: Install Python Dependencies

```bash
cd backend

# Install/update dependencies
pip3 install -r requirements.txt

# Important: psycopg2-binary must be installed for PostgreSQL
pip3 install psycopg2-binary python-dotenv
```

### Step 6: Restart Backend

```bash
cd backend

# Stop old backend
pkill -f "python.*app.py" 2>/dev/null

# Start new backend
python3 app.py

# Or with gunicorn for production
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app('production')" --access-logfile - --error-logfile -
```

### Step 7: Test Backend

```bash
# Test health
curl https://api.aksesgptmurah.tech/health

# Test packages
curl https://api.aksesgptmurah.tech/api/packages

# Test create order
curl -X POST https://api.aksesgptmurah.tech/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "test@gmail.com",
    "package_id": "chatgpt_plus_1_month",
    "full_name": "Test User",
    "phone_number": "+628123456789"
  }'

# Expected response:
# {
#   "success": true,
#   "order_id": "INV-1234567890",
#   "checkout_url": "https://tripay.co.id/checkout/...",
#   "reference": "T123456789",
#   "payment_method": "QRIS",
#   "amount": 25000
# }
```

### Step 8: Test Frontend

1. Open: https://aksesgptmurah.tech
2. Hard refresh: `Ctrl + Shift + R`
3. Pilih paket
4. Isi form
5. Klik "Lanjutkan Pembayaran"
6. **Should redirect to Tripay payment page** ✓

## What Changed

### Backend Changes

1. **config.py** - Updated to use PostgreSQL instead of MySQL:
   ```python
   SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://...'
   ```

2. **backend/.env** - Created with Supabase connection string

3. **New migration** - `supabase/migrations/20250930100000_create_orders_tables.sql`
   - Creates all required tables
   - Sets up RLS policies
   - Inserts default packages

### Why This Fixes the Issue

**Before:**
- Backend tries to connect to MySQL at `127.0.0.1:3306`
- MySQL not installed/running
- Database `gptapp_db` doesn't exist
- Result: **500 Internal Server Error**

**After:**
- Backend connects to Supabase PostgreSQL
- Database already running and accessible
- Tables created via migration
- Result: **Everything works!**

## Troubleshooting

### Error: "password authentication failed"

Fix: Update DATABASE_URL with correct password from Supabase dashboard.

### Error: "relation does not exist"

Fix: Run migration (Step 3).

### Error: "could not connect to server"

Fix: Check connection string format and network connectivity.

### Backend still returns 500

Check backend logs:
```bash
cd backend
python3 app.py
# Watch console output
```

Or run in debug mode:
```bash
cd backend
FLASK_ENV=development python3 app.py
# Will show detailed error messages
```

### Frontend still shows "Failed to fetch"

1. Verify backend is running:
   ```bash
   curl https://api.aksesgptmurah.tech/health
   ```

2. Hard refresh browser: `Ctrl + Shift + R`

3. Clear browser cache completely

4. Check browser console (F12) for actual error

## Database Connection Strings Reference

### Direct Connection (Use this for Backend)
```
postgresql://postgres:[PASSWORD]@db.0ec90b57d6e95fcbda19832f.supabase.co:5432/postgres
```

### Pooled Connection (DON'T use this)
```
postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```

Always use **Direct connection** for backend API servers.

## Verification Checklist

- [ ] Supabase dashboard accessible
- [ ] Database password obtained
- [ ] backend/.env updated with correct DATABASE_URL
- [ ] Migration applied successfully
- [ ] Tables visible in Supabase dashboard
- [ ] Python dependencies installed
- [ ] Backend restarted
- [ ] Health check returns 200
- [ ] Create order returns success (not 500)
- [ ] Frontend test successful

## Next Steps After Setup

1. **Test thoroughly** - Try multiple orders
2. **Monitor logs** - Watch for any errors
3. **Setup monitoring** - Use Supabase dashboard to monitor database
4. **Backup data** - Supabase auto-backups, but verify it's enabled

## Support

If masih error after following all steps:

1. **Check backend logs:**
   ```bash
   cd backend && python3 app.py
   ```

2. **Test database connection:**
   ```bash
   python3 -c "from app import create_app; app = create_app(); app.app_context().push(); from models import db; db.create_all(); print('Success')"
   ```

3. **Run diagnostic:**
   ```bash
   cd backend && python3 test_order_creation.py
   ```

Share output if needed help.