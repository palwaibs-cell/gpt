#!/bin/bash

# Database Setup Script
# This script will:
# 1. Check if MySQL is running
# 2. Create database if doesn't exist
# 3. Create user if doesn't exist
# 4. Initialize tables

echo "=========================================="
echo "DATABASE SETUP SCRIPT"
echo "=========================================="
echo ""

# Database credentials from .env
DB_NAME="gptapp_db"
DB_USER="gptuser"
DB_PASS="GptUser123!"
DB_HOST="127.0.0.1"

# Step 1: Check MySQL service
echo "1. Checking MySQL service..."
if systemctl is-active --quiet mysql; then
    echo "   ✓ MySQL is running"
elif systemctl is-active --quiet mariadb; then
    echo "   ✓ MariaDB is running"
else
    echo "   ✗ MySQL/MariaDB is not running"
    echo "   Starting MySQL..."
    sudo systemctl start mysql 2>/dev/null || sudo systemctl start mariadb 2>/dev/null

    if systemctl is-active --quiet mysql || systemctl is-active --quiet mariadb; then
        echo "   ✓ MySQL started successfully"
    else
        echo "   ✗ Failed to start MySQL"
        echo "   Please install MySQL first:"
        echo "     sudo apt update"
        echo "     sudo apt install mysql-server"
        exit 1
    fi
fi

echo ""

# Step 2: Check if we can connect to MySQL
echo "2. Testing MySQL connection..."
if mysql -h "$DB_HOST" -u root -e "SELECT 1;" >/dev/null 2>&1; then
    echo "   ✓ Can connect to MySQL as root (no password)"
    MYSQL_CMD="mysql -h $DB_HOST -u root"
elif mysql -h "$DB_HOST" -u root -p -e "SELECT 1;" >/dev/null 2>&1; then
    echo "   ✓ Can connect to MySQL as root (with password)"
    echo "   Please enter MySQL root password when prompted"
    MYSQL_CMD="mysql -h $DB_HOST -u root -p"
else
    echo "   ✗ Cannot connect to MySQL"
    echo "   Please check MySQL installation and root password"
    exit 1
fi

echo ""

# Step 3: Create database
echo "3. Creating database..."
$MYSQL_CMD <<EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF

if [ $? -eq 0 ]; then
    echo "   ✓ Database '$DB_NAME' created/exists"
else
    echo "   ✗ Failed to create database"
    exit 1
fi

echo ""

# Step 4: Create user and grant privileges
echo "4. Creating database user..."
$MYSQL_CMD <<EOF
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';
CREATE USER IF NOT EXISTS '$DB_USER'@'127.0.0.1' IDENTIFIED BY '$DB_PASS';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'127.0.0.1';
FLUSH PRIVILEGES;
EOF

if [ $? -eq 0 ]; then
    echo "   ✓ User '$DB_USER' created/updated with privileges"
else
    echo "   ✗ Failed to create user"
    exit 1
fi

echo ""

# Step 5: Test user connection
echo "5. Testing user connection..."
if mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "SELECT 1;" >/dev/null 2>&1; then
    echo "   ✓ Can connect as '$DB_USER'"
else
    echo "   ✗ Cannot connect as '$DB_USER'"
    echo "   Database created but user connection failed"
    exit 1
fi

echo ""

# Step 6: Initialize tables using Python
echo "6. Initializing database tables..."
if [ -f "init_db.py" ]; then
    python3 init_db.py
    if [ $? -eq 0 ]; then
        echo "   ✓ Database tables initialized"
    else
        echo "   ✗ Failed to initialize tables"
        echo "   Trying manual initialization..."
        python3 -c "from app import create_app; from models import db; app = create_app('production'); app.app_context().push(); db.create_all(); print('Tables created')"
    fi
else
    echo "   ⚠ init_db.py not found, creating tables directly..."
    python3 -c "from app import create_app; from models import db; app = create_app('production'); app.app_context().push(); db.create_all(); print('✓ Tables created')"
fi

echo ""

# Step 7: Verify tables
echo "7. Verifying tables..."
TABLES=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "SHOW TABLES;" 2>/dev/null | tail -n +2)

if [ -z "$TABLES" ]; then
    echo "   ✗ No tables found"
    exit 1
else
    echo "   ✓ Tables found:"
    echo "$TABLES" | sed 's/^/     - /'
fi

echo ""
echo "=========================================="
echo "DATABASE SETUP COMPLETE"
echo "=========================================="
echo ""
echo "Connection details:"
echo "  Host: $DB_HOST"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: $DB_PASS"
echo ""
echo "Test connection:"
echo "  mysql -h $DB_HOST -u $DB_USER -p'$DB_PASS' $DB_NAME"
echo ""
echo "Next step: Start/restart backend"
echo "  cd backend"
echo "  python3 app.py"
echo ""