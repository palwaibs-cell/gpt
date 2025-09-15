# ChatGPT Plus Order System - Backend

Backend sistem untuk mengelola order dan otomatisasi invite ChatGPT Plus menggunakan Flask, PostgreSQL, Celery, dan Selenium.

## 🚀 Fitur Utama

- **Order Management**: API untuk membuat dan mengelola order
- **Payment Integration**: Integrasi dengan Midtrans payment gateway
- **Automated Invitations**: Otomatisasi invite ChatGPT Team menggunakan Selenium
- **Asynchronous Processing**: Background tasks dengan Celery dan Redis
- **Email Notifications**: Konfirmasi pembayaran dan invite menggunakan SendGrid
- **Admin Notifications**: Notifikasi ke admin untuk manual review
- **Rate Limiting**: Proteksi API dari abuse
- **Comprehensive Logging**: Logging detail untuk debugging dan monitoring

## 🛠️ Teknologi

- **Framework**: Flask 2.3.3
- **Database**: PostgreSQL dengan SQLAlchemy ORM
- **Task Queue**: Celery dengan Redis broker
- **Automation**: Selenium WebDriver dengan Chrome
- **Payment**: Midtrans payment gateway
- **Email**: SendGrid API
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

# Midtrans Payment Gateway
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

### Endpoints

#### 1. Create Order
```http
POST /api/orders
Content-Type: application/json

{
  "customer_email": "user@example.com",
  "package_id": "chatgpt_plus_1_month",
  "full_name": "John Doe",
  "phone_number": "+6281234567890"
}
```

**Response:**
```json
{
  "order_id": "ORD12345678",
  "payment_url": "https://app.sandbox.midtrans.com/snap/v2/vtweb/...",
  "status": "pending_payment"
}
```

#### 2. Get Order Status
```http
GET /api/orders/{order_id}/status
```

**Response:**
```json
{
  "order_id": "ORD12345678",
  "payment_status": "paid",
  "invitation_status": "sent",
  "message": "Undangan ChatGPT Plus telah dikirim ke user@example.com"
}
```

#### 3. Payment Webhook
```http
POST /api/payment/webhook
Content-Type: application/json

{
  "order_id": "ORD12345678",
  "status_code": "200",
  "gross_amount": "250000.00",
  "signature_key": "..."
}
```

#### 4. Health Check
```http
GET /health
```

#### 5. Get Packages
```http
GET /api/packages
```

## 🔄 Workflow

1. **Order Creation**: Frontend mengirim data order ke `/api/orders`
2. **Payment Processing**: Sistem membuat transaksi di Midtrans dan mengembalikan payment URL
3. **Payment Webhook**: Midtrans mengirim notifikasi status pembayaran
4. **Invitation Processing**: Jika pembayaran sukses, Celery task memproses invite otomatis
5. **Email Notifications**: Sistem mengirim konfirmasi ke customer dan notifikasi ke admin

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