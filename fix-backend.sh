#!/bin/bash

# Quick Fix Script - Migrate Backend to Supabase
# This script will guide you through fixing the "Failed to fetch" error

clear
echo "=========================================="
echo "BACKEND FIX - MIGRATE TO SUPABASE"
echo "=========================================="
echo ""
echo "Problem: Backend uses MySQL (doesn't exist)"
echo "Solution: Use Supabase PostgreSQL (already available)"
echo ""
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "Error: backend directory not found"
    echo "Please run this script from project root"
    exit 1
fi

# Step 1: Get Supabase password
echo "Step 1: Get Supabase Database Password"
echo "----------------------------------------"
echo ""
echo "1. Open: https://supabase.com/dashboard"
echo "2. Select project: 0ec90b57d6e95fcbda19832f"
echo "3. Go to: Settings → Database"
echo "4. Find: Connection string (Direct connection)"
echo "5. Copy password from:"
echo "   postgresql://postgres:[PASSWORD]@db.0ec90b57d6e95fcbda19832f.supabase.co:5432/postgres"
echo ""
read -p "Enter Supabase password: " SUPABASE_PASSWORD
echo ""

if [ -z "$SUPABASE_PASSWORD" ]; then
    echo "Error: Password cannot be empty"
    exit 1
fi

# Step 2: Update .env
echo "Step 2: Updating backend/.env"
echo "----------------------------------------"
echo ""

# Create .env file
cat > backend/.env <<EOF
# Supabase Database Configuration
DATABASE_URL=postgresql://postgres:${SUPABASE_PASSWORD}@db.0ec90b57d6e95fcbda19832f.supabase.co:5432/postgres

# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)

# Tripay Payment Gateway
TRIPAY_API_KEY=VI4hfWUhlfX70OZIjiae18pATyHOvNq0WjvBT6ej
TRIPAY_MERCHANT_CODE=T45484
TRIPAY_PRIVATE_KEY=2PW1G-zUdkm-EGiwn-femXJ-yEtIO
TRIPAY_IS_PRODUCTION=true
TRIPAY_BASE_URL=https://tripay.co.id/api
TRIPAY_CALLBACK_URL=https://api.aksesgptmurah.tech/callback/tripay

# API Configuration
API_BASE_URL=https://api.aksesgptmurah.tech
TRIPAY_CALLBACK_PATH=/callback/tripay
FRONTEND_URL=https://aksesgptmurah.tech

# CORS Configuration
ALLOWED_ORIGINS=https://aksesgptmurah.tech

# ChatGPT Admin
CHATGPT_ADMIN_URL=https://chatgpt.com/admin?tab=members

# Celery & Email (disabled)
ENABLE_CELERY=false
EMAIL_ENABLED=false
REDIS_URL=redis://localhost:6379/0

# Rate Limiting
RATE_LIMIT_STORAGE_URL=memory://

# Security
WEBHOOK_SECRET=$(openssl rand -hex 32)
ALLOWED_WEBHOOK_IPS=103.10.128.0/22,103.10.129.0/22
EOF

echo "✓ backend/.env created"
echo ""

# Step 3: Test database connection
echo "Step 3: Testing Database Connection"
echo "----------------------------------------"
echo ""

CONNECTION_STRING="postgresql://postgres:${SUPABASE_PASSWORD}@db.0ec90b57d6e95fcbda19832f.supabase.co:5432/postgres"

if command -v psql &> /dev/null; then
    echo "Testing connection..."
    if psql "$CONNECTION_STRING" -c "SELECT 1;" &> /dev/null; then
        echo "✓ Database connection successful"
    else
        echo "✗ Database connection failed"
        echo "  Check if password is correct"
        exit 1
    fi
else
    echo "⚠ psql not installed, skipping connection test"
    echo "  Install with: sudo apt install postgresql-client"
fi

echo ""

# Step 4: Apply migration
echo "Step 4: Apply Database Migration"
echo "----------------------------------------"
echo ""
echo "Choose migration method:"
echo "  1. Via Supabase Dashboard (Recommended)"
echo "  2. Via psql command line"
echo ""
read -p "Enter choice (1 or 2): " MIGRATION_CHOICE
echo ""

if [ "$MIGRATION_CHOICE" = "1" ]; then
    echo "Manual steps:"
    echo "1. Open: https://supabase.com/dashboard"
    echo "2. Go to: SQL Editor"
    echo "3. Click: New query"
    echo "4. Copy-paste from: supabase/migrations/20250930100000_create_orders_tables.sql"
    echo "5. Click: Run"
    echo ""
    read -p "Press Enter after completing migration..."
elif [ "$MIGRATION_CHOICE" = "2" ]; then
    if command -v psql &> /dev/null; then
        echo "Running migration..."
        if psql "$CONNECTION_STRING" -f supabase/migrations/20250930100000_create_orders_tables.sql; then
            echo "✓ Migration applied successfully"
        else
            echo "✗ Migration failed"
            exit 1
        fi
    else
        echo "✗ psql not installed"
        echo "  Install with: sudo apt install postgresql-client"
        exit 1
    fi
else
    echo "Invalid choice"
    exit 1
fi

echo ""

# Step 5: Verify tables
echo "Step 5: Verify Tables"
echo "----------------------------------------"
echo ""

if command -v psql &> /dev/null; then
    echo "Checking tables..."
    TABLES=$(psql "$CONNECTION_STRING" -t -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;" 2>/dev/null | tr -d ' ')

    if [ -n "$TABLES" ]; then
        echo "✓ Tables found:"
        echo "$TABLES" | sed 's/^/  - /'
    else
        echo "✗ No tables found"
        echo "  Migration might have failed"
        exit 1
    fi
else
    echo "⚠ Cannot verify tables (psql not installed)"
fi

echo ""

# Step 6: Install dependencies
echo "Step 6: Install Python Dependencies"
echo "----------------------------------------"
echo ""

cd backend

if command -v pip3 &> /dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt -q
    echo "✓ Dependencies installed"
else
    echo "⚠ pip3 not found"
    echo "  Install Python 3 and pip first"
fi

cd ..
echo ""

# Step 7: Restart backend
echo "Step 7: Restart Backend"
echo "----------------------------------------"
echo ""

echo "Stopping old backend..."
pkill -f "python.*app.py" 2>/dev/null
sleep 2

echo "Starting new backend..."
cd backend

# Check if we should run in background or foreground
read -p "Run backend in background? (y/n): " RUN_BG

if [ "$RUN_BG" = "y" ] || [ "$RUN_BG" = "Y" ]; then
    nohup python3 app.py > backend.log 2>&1 &
    echo "✓ Backend started in background"
    echo "  Logs: backend/backend.log"
    echo "  Stop with: pkill -f 'python.*app.py'"
else
    echo "Starting backend in foreground..."
    echo "Press Ctrl+C to stop"
    echo ""
    python3 app.py
fi

cd ..
echo ""

# Done
echo "=========================================="
echo "SETUP COMPLETE"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Test backend:"
echo "   curl https://api.aksesgptmurah.tech/health"
echo ""
echo "2. Test create order:"
echo "   curl -X POST https://api.aksesgptmurah.tech/api/orders \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"customer_email\":\"test@gmail.com\",\"package_id\":\"chatgpt_plus_1_month\",\"full_name\":\"Test\",\"phone_number\":\"+628123456789\"}'"
echo ""
echo "3. Test frontend:"
echo "   - Open: https://aksesgptmurah.tech"
echo "   - Hard refresh: Ctrl+Shift+R"
echo "   - Try creating order"
echo ""
echo "If still error, check:"
echo "  - Backend logs: tail -f backend/backend.log"
echo "  - Full guide: SUPABASE_SETUP_GUIDE.md"
echo ""