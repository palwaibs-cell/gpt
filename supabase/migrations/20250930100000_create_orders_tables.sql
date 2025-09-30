/*
  # Create Orders System Tables

  1. New Tables
    - `packages` - Available ChatGPT Plus packages
      - `id` (text, primary key) - Package identifier
      - `name` (text) - Package name
      - `price` (numeric) - Package price in IDR
      - `duration` (text) - Package duration
      - `description` (text) - Package description
      - `is_active` (boolean) - Whether package is active
      - `created_at` (timestamptz) - Creation timestamp

    - `orders` - Customer orders
      - `id` (integer, primary key) - Auto-increment ID
      - `order_id` (text, unique) - Merchant reference/order ID
      - `customer_email` (text) - Customer email
      - `full_name` (text) - Customer full name
      - `phone_number` (text) - Customer phone number
      - `package_id` (text) - Foreign key to packages
      - `amount` (numeric) - Order amount
      - `payment_status` (text) - Payment status (pending, paid, failed, expired)
      - `invitation_status` (text) - Invitation status (pending, processing, sent, failed)
      - `checkout_url` (text) - Tripay checkout URL
      - `payment_method` (text) - Payment method used
      - `reference` (text) - Tripay reference
      - `created_at` (timestamptz) - Creation timestamp
      - `updated_at` (timestamptz) - Last update timestamp

    - `invitation_logs` - Invitation attempt logs
      - `id` (integer, primary key) - Auto-increment ID
      - `order_id` (integer) - Foreign key to orders
      - `attempt_timestamp` (timestamptz) - Attempt timestamp
      - `status` (text) - Attempt status (success, failure, retry)
      - `error_message` (text) - Error message if failed
      - `screenshot_path` (text) - Screenshot path
      - `retry_count` (integer) - Number of retries

    - `admin_accounts` - ChatGPT admin accounts for sending invitations
      - `id` (integer, primary key) - Auto-increment ID
      - `email` (text, unique) - Admin email
      - `password` (text) - Admin password
      - `is_active` (boolean) - Whether account is active
      - `last_used` (timestamptz) - Last time account was used
      - `failed_attempts` (integer) - Number of failed attempts
      - `created_at` (timestamptz) - Creation timestamp

  2. Security
    - Enable RLS on all tables
    - Add policies for authenticated access

  3. Indexes
    - Add indexes on frequently queried columns
*/

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create packages table
CREATE TABLE IF NOT EXISTS packages (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  price NUMERIC(10, 2) NOT NULL,
  duration TEXT NOT NULL,
  description TEXT,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
  id SERIAL PRIMARY KEY,
  order_id TEXT UNIQUE NOT NULL,
  customer_email TEXT NOT NULL,
  full_name TEXT,
  phone_number TEXT,
  package_id TEXT NOT NULL REFERENCES packages(id),
  amount NUMERIC(10, 2) NOT NULL,
  payment_status TEXT NOT NULL DEFAULT 'pending',
  invitation_status TEXT NOT NULL DEFAULT 'pending',
  checkout_url TEXT,
  payment_method TEXT,
  reference TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create invitation_logs table
CREATE TABLE IF NOT EXISTS invitation_logs (
  id SERIAL PRIMARY KEY,
  order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  attempt_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  status TEXT NOT NULL,
  error_message TEXT,
  screenshot_path TEXT,
  retry_count INTEGER NOT NULL DEFAULT 0
);

-- Create admin_accounts table
CREATE TABLE IF NOT EXISTS admin_accounts (
  id SERIAL PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT true,
  last_used TIMESTAMPTZ,
  failed_attempts INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_orders_order_id ON orders(order_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer_email ON orders(customer_email);
CREATE INDEX IF NOT EXISTS idx_orders_payment_status ON orders(payment_status);
CREATE INDEX IF NOT EXISTS idx_orders_invitation_status ON orders(invitation_status);
CREATE INDEX IF NOT EXISTS idx_orders_reference ON orders(reference);
CREATE INDEX IF NOT EXISTS idx_invitation_logs_order_id ON invitation_logs(order_id);
CREATE INDEX IF NOT EXISTS idx_admin_accounts_email ON admin_accounts(email);
CREATE INDEX IF NOT EXISTS idx_admin_accounts_is_active ON admin_accounts(is_active);
CREATE INDEX IF NOT EXISTS idx_admin_accounts_last_used ON admin_accounts(last_used);

-- Enable RLS
ALTER TABLE packages ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE invitation_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_accounts ENABLE ROW LEVEL SECURITY;

-- RLS Policies for packages (public read)
CREATE POLICY "Anyone can view active packages"
  ON packages FOR SELECT
  USING (is_active = true);

CREATE POLICY "Service role can manage packages"
  ON packages FOR ALL
  USING (auth.role() = 'service_role');

-- RLS Policies for orders (users can view their own orders)
CREATE POLICY "Users can view their own orders"
  ON orders FOR SELECT
  USING (customer_email = current_setting('request.jwt.claims', true)::json->>'email');

CREATE POLICY "Service role can manage orders"
  ON orders FOR ALL
  USING (auth.role() = 'service_role');

-- RLS Policies for invitation_logs (service role only)
CREATE POLICY "Service role can manage invitation logs"
  ON invitation_logs FOR ALL
  USING (auth.role() = 'service_role');

-- RLS Policies for admin_accounts (service role only)
CREATE POLICY "Service role can manage admin accounts"
  ON admin_accounts FOR ALL
  USING (auth.role() = 'service_role');

-- Insert default packages
INSERT INTO packages (id, name, price, duration, description, is_active) VALUES
  ('chatgpt_plus_1_month', 'Individual Plan', 25000, '1 Bulan', 'Akses GPT-4 Unlimited dengan email pribadi sebagai Member', true),
  ('team_package', 'Team Plan', 95000, '1 Bulan', 'Sampai 5 akun tim sebagai Member dengan akses penuh', true)
ON CONFLICT (id) DO NOTHING;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();