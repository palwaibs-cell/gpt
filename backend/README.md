# ChatGPT Plus Order System - Backend

Backend sistem untuk mengelola order dan otomatisasi invite ChatGPT Plus menggunakan Flask, PostgreSQL, Celery, dan Selenium dengan dukungan multi-akun ChatGPT dan integrasi Tripay payment gateway.

## 🚀 Fitur Utama

- **Order Management**: API untuk membuat dan mengelola order
- **Tripay Payment Integration**: Integrasi dengan Tripay payment gateway (utama)
- **Midtrans Support**: Dukungan legacy Midtrans untuk migrasi
- **Multi-Account ChatGPT Management**: Sistem manajemen pool akun ChatGPT dengan alokasi otomatis
- **Automated Account Assignment**: Otomatisasi assignment akun ChatGPT ke customer
- **Account Pool Management**: CRUD dan monitoring akun ChatGPT
- **Asynchronous Processing**: Background tasks dengan Celery dan Redis
- **Email Notifications**: Konfirmasi pembayaran dan notifikasi akun
- **Admin Panel**: Interface admin untuk mengelola akun dan assignment
- **Audit Logging**: Logging aktivitas sistem untuk compliance
- **Rate Limiting**: Proteksi API dari abuse
- **Comprehensive Testing**: Unit tests untuk komponen utama

## 🛠️ Teknologi

- **Framework**: Flask 2.3.3
- **Database**: PostgreSQL dengan SQLAlchemy ORM
- **Task Queue**: Celery dengan Redis broker
- **Payment Gateway**: Tripay (utama), Midtrans (legacy)
- **Email**: SendGrid API
- **Security**: HMAC signature verification
- **Testing**: pytest dengan mocking
- **Containerization**: Docker & Docker Compose

## 📋 Prerequisites

- Python 3.9+
- PostgreSQL 14+
- Redis 6+
- Google Chrome & ChromeDriver
- Docker & Docker Compose (untuk deployment)

## 🔧 Installation & Setup

### 0. Prerequisites - ChatGPT Team Account

**PENTING**: Anda memerlukan akun ChatGPT Team (bukan Plus individual) sebagai admin:

1. **Buat ChatGPT Team Account**:
   - Kunjungi https://chatgpt.com/team
   - Subscribe ke ChatGPT Team ($25-30/bulan)
   - Anda akan menjadi Admin dengan kemampuan invite member

2. **Dapatkan Team URL**:
   - Format: `https://chatgpt.com/team/your-team-id`
   - Simpan URL ini untuk konfigurasi

3. **Role Structure**:
   - **Admin** (Anda): Manage team, invite/remove member
   - **Member** (Customer): Full ChatGPT Plus access, tidak bisa manage team
   - Sistem akan invite customer sebagai **Member**

### 1. Clone Repository

```bash
git clone <repository-url>
cd backend
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env file dengan konfigurasi Anda
nano .env
```

### 3. Konfigurasi Environment Variables

Edit file `.env` dengan konfigurasi yang sesuai:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/chatgpt_orders

# Flask
SECRET_KEY=your-secret-key-here

# Tripay Payment Gateway (Primary)
TRIPAY_BASE_URL=https://tripay.co.id/api-sandbox/
TRIPAY_MERCHANT_CODE=your-merchant-code
TRIPAY_API_KEY=your-api-key
TRIPAY_PRIVATE_KEY=your-private-key
TRIPAY_CALLBACK_URL=https://aksesgptmurah.tech/callback/tripay

# Midtrans Payment Gateway (Legacy/Fallback)
MIDTRANS_SERVER_KEY=your-midtrans-server-key
MIDTRANS_CLIENT_KEY=your-midtrans-client-key
MIDTRANS_IS_PRODUCTION=false

# ChatGPT Admin Credentials
CHATGPT_ADMIN_EMAIL=your-admin@example.com
CHATGPT_ADMIN_PASSWORD=your-admin-password
CHATGPT_TEAM_URL=https://chatgpt.com/team/your-team-id

# Redis
REDIS_URL=redis://localhost:6379/0

# SendGrid Email
SENDGRID_API_KEY=your-sendgrid-api-key
FROM_EMAIL=noreply@yourdomain.com

# Admin Notifications
ADMIN_EMAIL=admin@yourdomain.com
```

### 4. Local Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Run Flask development server
python app.py
```

### 5. Celery Worker Setup

Buka terminal baru dan jalankan:

```bash
# Start Celery worker
celery -A celery_worker.celery worker --loglevel=info

# Start Celery beat (scheduler) - terminal terpisah
celery -A celery_worker.celery beat --loglevel=info

# Monitor dengan Flower (opsional)
celery -A celery_worker.celery flower
```

## 🐳 Docker Deployment

### 1. Build dan Run dengan Docker Compose

```bash
# Build dan start semua services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 2. Services yang Berjalan

- **Backend API**: http://localhost:5000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Flower (Celery Monitor)**: http://localhost:5555

## 📚 API Documentation

### Payment Endpoints

#### POST /api/orders
Membuat order baru dan inisiasi pembayaran (menggunakan Tripay)

**Request Body:**
```json
{
  "customer_email": "customer@example.com",
  "full_name": "Customer Name",
  "phone_number": "081234567890",
  "package_id": "chatgpt_plus_1_month"
}
```

**Response:**
```json
{
  "order_id": "ORD12345678",
  "payment_url": "https://tripay.co.id/checkout/TP1234567890",
  "status": "pending_payment"
}
```

#### POST /callback/tripay
Webhook endpoint untuk menerima notifikasi pembayaran dari Tripay

**Headers:**
- `X-Callback-Event`: payment_status
- `X-Callback-Signature`: HMAC SHA256 signature

**Request Body:**
```json
{
  "reference": "TP1234567890",
  "merchant_ref": "ORD-12345678-abcd1234",
  "status": "PAID",
  "payment_method": "QRIS",
  "amount": 99000,
  "paid_at": 1699999999
}
```

#### GET /api/orders/{order_id}/status
Mendapatkan status order

**Response:**
```json
{
  "order_id": "ORD12345678",
  "payment_status": "paid",
  "invitation_status": "account_assigned",
  "message": "Akun ChatGPT telah dialokasikan dan siap digunakan"
}
```

### Admin Account Management Endpoints

#### GET /api/admin/chatgpt-accounts
Mendapatkan daftar akun ChatGPT

**Query Parameters:**
- `page`: Halaman (default: 1)
- `per_page`: Item per halaman (max: 100)
- `status`: Filter berdasarkan status (AVAILABLE, ASSIGNED, SUSPENDED)

**Response:**
```json
{
  "accounts": [
    {
      "id": 1,
      "email": "account1@chatgpt.com",
      "status": "AVAILABLE",
      "max_seats": null,
      "current_seats_used": 0,
      "note": "Primary account",
      "created_at": "2024-01-15T10:00:00"
    }
  ],
  "total": 10,
  "pages": 1,
  "current_page": 1
}
```

#### POST /api/admin/chatgpt-accounts
Membuat akun ChatGPT baru

**Request Body:**
```json
{
  "email": "newaccount@chatgpt.com",
  "note": "New account for testing",
  "status": "AVAILABLE",
  "max_seats": 5
}
```

#### PUT /api/admin/chatgpt-accounts/{account_id}
Update akun ChatGPT

**Request Body:**
```json
{
  "note": "Updated note",
  "status": "SUSPENDED",
  "max_seats": 3
}
```

#### GET /api/admin/account-assignments
Mendapatkan daftar assignment akun

**Query Parameters:**
- `page`: Halaman
- `per_page`: Item per halaman
- `status`: Filter status (ACTIVE, ENDED, REVOKED)
- `user_id`: Filter berdasarkan user email

#### POST /api/admin/account-assignments/{assignment_id}/extend
Perpanjang assignment

**Request Body:**
```json
{
  "additional_days": 30
}
```

#### POST /api/admin/account-assignments/{assignment_id}/revoke
Cabut assignment

**Request Body:**
```json
{
  "reason": "Customer refund"
}
```

#### GET /api/admin/audit-logs
Mendapatkan audit logs

### Legacy Endpoints (Midtrans)

#### POST /api/payment/webhook
Legacy webhook untuk Midtrans

## 🔄 Workflow

### New Tripay-based Workflow (Default)

1. **Order Creation**: Frontend mengirim data order ke `/api/orders`
2. **Payment Processing**: Sistem membuat transaksi di Tripay dan mengembalikan checkout URL
3. **Payment Webhook**: Tripay mengirim callback ke `/callback/tripay` dengan status pembayaran
4. **Account Allocation**: Jika pembayaran sukses, sistem mengalokasikan akun ChatGPT dari pool
5. **Assignment Management**: Sistem membuat assignment dan mengatur durasi akses
6. **Email Notifications**: Sistem mengirim konfirmasi dengan detail akun ke customer
7. **Auto Cleanup**: Cron job otomatis release akun yang expired

### Legacy Midtrans Workflow (Fallback)

1. **Order Creation**: Frontend mengirim data order ke `/api/orders`
2. **Payment Processing**: Sistem membuat transaksi di Midtrans dan mengembalikan payment URL
3. **Payment Webhook**: Midtrans mengirim notifikasi status pembayaran
4. **Invitation Processing**: Jika pembayaran sukses, Celery task memproses invite otomatis
5. **Email Notifications**: Sistem mengirim konfirmasi ke customer dan notifikasi ke admin

## 🏗️ Multi-Account Architecture

### ChatGPT Account Pool
- **Pool Management**: Admin dapat menambah/edit akun ChatGPT ke pool
- **Status Tracking**: AVAILABLE, ASSIGNED, SUSPENDED
- **Seat Management**: Dukungan single-user dan multi-seat accounts
- **Automatic Allocation**: Sistem otomatis pilih akun available saat payment PAID

### Account Assignment
- **Duration-based**: Assignment dengan tanggal mulai dan berakhir
- **Status Tracking**: ACTIVE, ENDED, REVOKED
- **Audit Trail**: Log semua aktivitas assignment
- **Admin Controls**: Extend, revoke, atau reassign akun

### Security & Compliance
- **HMAC Verification**: Semua webhook Tripay diverifikasi dengan HMAC SHA256
- **Idempotent Processing**: Callback yang sama tidak diproses ulang
- **Audit Logging**: Semua aktivitas tercatat untuk compliance
- **Data Masking**: Sensitive data di-mask dalam logs

## 🤖 Selenium Automation

### ChatGPT Team Inviter

Modul `automation/chatgpt_inviter.py` menangani:

- Login ke akun admin ChatGPT
- Navigasi ke halaman team management
- Pengiriman invite ke member baru
- Verifikasi status invite
- Error handling dan retry mechanism
- Screenshot untuk debugging

### Anti-Detection Features

- Custom user agent
- Randomized delays
- Headless mode untuk production
- Error handling yang robust

## 📊 Monitoring & Logging

### Celery Monitoring dengan Flower

Akses http://localhost:5555 untuk melihat:
- Active tasks
- Task history
- Worker status
- Queue monitoring

### Logging

Logs tersimpan di:
- Console output untuk development
- File logs untuk production
- Database logs untuk invitation attempts

## 🔒 Security Features

- **Input Validation**: Validasi ketat untuk semua input
- **Rate Limiting**: Proteksi dari abuse dan DDoS
- **Webhook Verification**: Verifikasi signature dari payment gateway
- **Environment Variables**: Kredensial disimpan aman
- **SQL Injection Protection**: Menggunakan SQLAlchemy ORM
- **CORS Configuration**: Konfigurasi CORS yang tepat

## 🚨 Error Handling

### Payment Errors
- Gateway timeout
- Invalid credentials
- Network issues

### Selenium Errors
- Element not found
- Timeout exceptions
- WebDriver crashes
- CAPTCHA detection

### Database Errors
- Connection issues
- Transaction rollbacks
- Migration errors

## 📈 Performance Optimization

- **Connection Pooling**: Database connection pooling
- **Async Processing**: Background tasks dengan Celery
- **Caching**: Redis untuk caching dan session storage
- **Resource Management**: Proper cleanup untuk WebDriver
- **Retry Mechanisms**: Exponential backoff untuk failed tasks

## 🔧 Maintenance

### Database Migrations

```bash
# Create migration
flask db migrate -m "Description"

# Apply migration
flask db upgrade

# Rollback migration
flask db downgrade
```

### Monitoring Tasks

```bash
# Check Celery workers
celery -A celery_worker.celery inspect active

# Purge queue
celery -A celery_worker.celery purge

# Restart workers
docker-compose restart celery-worker
```

### Backup Database

```bash
# Backup
pg_dump -h localhost -U postgres chatgpt_orders > backup.sql

# Restore
psql -h localhost -U postgres chatgpt_orders < backup.sql
```

## 🐛 Troubleshooting

### Common Issues

1. **ChromeDriver Issues**
   ```bash
   # Update ChromeDriver
   pip install --upgrade webdriver-manager
   ```

2. **Database Connection**
   ```bash
   # Check PostgreSQL status
   systemctl status postgresql
   ```

3. **Redis Connection**
   ```bash
   # Check Redis status
   redis-cli ping
   ```

4. **Celery Workers Not Processing**
   ```bash
   # Restart workers
   docker-compose restart celery-worker
   ```

### Debug Mode

Set environment variables untuk debugging:
```env
FLASK_ENV=development
SELENIUM_HEADLESS=false
```

## 📞 Support

Untuk bantuan teknis atau pertanyaan:
- Email: admin@yourdomain.com
- WhatsApp: +6281234567890

## 📄 License

[MIT License](LICENSE)