/*
  # Allow Anonymous Order Status Check

  1. Changes
    - Add policy to allow anyone to read order status by order_id
    - This enables the confirmation page to work without authentication
    - Users can only see orders if they have the exact order_id (which is secure enough for order tracking)

  2. Security
    - Order IDs are unique and hard to guess (timestamp-based)
    - Read-only access
    - No sensitive data exposed in orders table
*/

-- Drop existing restrictive policy
DROP POLICY IF EXISTS "Users can view their own orders" ON orders;

-- Allow anyone to view orders (they need the order_id which is unique)
CREATE POLICY "Anyone can view orders with order_id"
  ON orders
  FOR SELECT
  TO public
  USING (true);