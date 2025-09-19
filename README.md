# ChatGPT Plus Order System

Sistem order otomatis untuk ChatGPT Plus dengan integrasi payment gateway dan otomatisasi invite menggunakan Selenium.

## 🚀 Fitur Utama

### Frontend (React + TypeScript)
- **Landing Page Modern**: Showcase paket ChatGPT Plus dengan desain premium
- **Order Form**: Form checkout dengan validasi real-time
- **Status Tracking**: Halaman konfirmasi dengan tracking pembayaran dan invite
- **Responsive Design**: Optimized untuk semua device
- **FAQ Section**: Accordion interaktif untuk pertanyaan umum

### Backend (Flask + Python)
- **API Endpoints**: RESTful API untuk order management
- **Payment Integration**: Integrasi Midtrans payment gateway
- **Selenium Automation**: Otomatisasi invite ChatGPT Team
- **Asynchronous Tasks**: Celery dengan Redis untuk background processing
- **Email Notifications**: SendGrid untuk konfirmasi dan notifikasi
- **Database**: PostgreSQL dengan SQLAlchemy ORM

## 🛠️ Teknologi

- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite
- **Backend**: Flask, SQLAlchemy, Celery, Redis
- **Database**: PostgreSQL
- **Payment**: Midtrans Gateway
- **Automation**: Selenium WebDriver
- **Email**: SendGrid API
- **Deployment**: Docker & Docker Compose

## 📋 Prerequisites

- Node.js 18+
- Python 3.9+
- PostgreSQL 14+
- Redis 6+
- Docker & Docker Compose (untuk deployment)

## 🔧 Installation & Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd chatgpt-plus-order-system
```

### 2. Frontend Setup

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

### 3. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Copy environment file
cp .env.example .env

# Edit .env dengan konfigurasi Anda
nano .env

# Install Python dependencies
pip install -r requirements.txt

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Start Flask development server
python app.py
```

### 4. Celery Workers

Buka terminal baru untuk setiap service:

```bash
# Terminal 1: Celery Worker
npm run backend:worker

# Terminal 2: Celery Beat (Scheduler)
npm run backend:beat

# Terminal 3: Flower (Monitoring)
npm run backend:flower
```

## 🐳 Docker Deployment

### Quick Start dengan Docker Compose

```bash
# Build dan start semua services
npm run docker:up

# View logs
npm run docker:logs

# Stop services
npm run docker:down
```

### Services yang Berjalan

- **Frontend**: http://localhost:3000
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

#### 2. Get Order Status
```http
GET /api/orders/{order_id}/status
```

#### 3. Payment Webhook
```http
POST /api/payment/webhook
```

#### 4. Health Check
```http
GET /health
```

## 🔄 Workflow

1. **Order Creation**: User memilih paket dan mengisi form
2. **Payment Processing**: Sistem membuat transaksi Midtrans
3. **Payment Webhook**: Midtrans mengirim notifikasi status
4. **Invitation Processing**: Celery task memproses invite otomatis
5. **Email Notifications**: Konfirmasi ke customer dan admin

## 🤖 Selenium Automation

### ChatGPT Team Inviter Features

- Login otomatis ke akun admin ChatGPT
- Navigasi ke halaman team management
- Pengiriman invite ke member baru
- Verifikasi status invite
- Error handling dan retry mechanism
- Screenshot untuk debugging

### Anti-Detection Features

- Custom user agent dan browser settings
- Randomized delays
- Headless mode untuk production
- Robust error handling

## 📊 Monitoring & Logging

### Celery Monitoring dengan Flower

Akses http://localhost:5555 untuk melihat:
- Active tasks
- Task history
- Worker status
- Queue monitoring

### Database Schema

**Orders Table:**
- `id`, `order_id`, `customer_email`
- `package_id`, `amount`, `payment_status`
- `invitation_status`, `created_at`, `updated_at`

**Invitation Logs Table:**
- `id`, `order_id`, `attempt_timestamp`
- `status`, `error_message`, `screenshot_path`

## 🔒 Security Features

- Input validation dan sanitization
- Rate limiting untuk API endpoints
- Webhook signature verification
- Environment-based credential management
- CORS configuration
- SQL injection protection

## 🚨 Error Handling

### Payment Errors
- Gateway timeout dan network issues
- Invalid credentials
- Transaction failures

### Selenium Errors
- Element not found
- Timeout exceptions
- WebDriver crashes
- CAPTCHA detection

## 📈 Performance Optimization

- Connection pooling untuk database
- Async processing dengan Celery
- Redis caching
- Resource management untuk WebDriver
- Retry mechanisms dengan exponential backoff

## 🔧 Development Scripts

```bash
# Frontend
npm run dev              # Start frontend dev server
npm run build           # Build for production
npm run preview         # Preview production build

# Backend
npm run backend:dev     # Start Flask dev server
npm run backend:worker  # Start Celery worker
npm run backend:beat    # Start Celery beat scheduler
npm run backend:flower  # Start Flower monitoring

# Docker
npm run docker:up       # Start all services
npm run docker:down     # Stop all services
npm run docker:logs     # View logs
```

## 🐛 Troubleshooting

### Common Issues

1. **ChromeDriver Issues**
   ```bash
   pip install --upgrade webdriver-manager
   ```

2. **Database Connection**
   ```bash
   # Check PostgreSQL status
   systemctl status postgresql
   ```

3. **Redis Connection**
   ```bash
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
EMAIL_ENABLED=false
SELENIUM_HEADLESS=false
```

## 🧪 Testing Endpoints

### Test Order Creation
```bash
curl -X POST http://151.240.0.79/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "test@example.com",
    "package_id": "chatgpt_plus_1_month",
    "full_name": "Test User",
    "phone_number": "+6281234567890"
  }'
```

### Test Callback (for testing)
```bash
curl -X POST http://151.240.0.79/callback/tripay \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_ref": "ORD00000001",
    "reference": "TF123456789",
    "status": "PAID",
    "total_amount": 25000,
    "signature": "calculated_signature"
  }'
```

## 📞 Support

Untuk bantuan teknis atau pertanyaan:
- Email: admin@yourdomain.com
- WhatsApp: +6281234567890

## 📄 License

[MIT License](LICENSE)