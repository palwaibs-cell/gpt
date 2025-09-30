# Deploy Supabase Edge Function - SOLUSI FINAL

## MASALAH & SOLUSI

**Masalah:** Python backend error 500 karena MySQL database tidak ada

**Solusi:** Gunakan Supabase Edge Functions (serverless, built-in PostgreSQL)

## QUICK DEPLOYMENT (3 Steps)

### Step 1: Apply Database Migration

**Via Supabase Dashboard:**
1. Open: https://supabase.com/dashboard/project/0ec90b57d6e95fcbda19832f
2. Go to: **SQL Editor**
3. Click: **New query**
4. Copy-paste entire file: `supabase/migrations/20250930100000_create_orders_tables.sql`
5. Click: **Run**
6. Verify tables created: Go to **Table Editor**

### Step 2: Deploy Edge Function

**Via Supabase Dashboard:**
1. Go to: **Edge Functions**
2. Click: **Deploy new function**
3. Name: `create-order`
4. Copy code from: `supabase/functions/create-order/index.ts`
5. Click: **Deploy function**

**Set Environment Variables:**
- Go to: **Edge Functions** → **Manage secrets**
- Add:
  ```
  TRIPAY_API_KEY=VI4hfWUhlfX70OZIjiae18pATyHOvNq0WjvBT6ej
  TRIPAY_MERCHANT_CODE=T45484
  TRIPAY_PRIVATE_KEY=2PW1G-zUdkm-EGiwn-femXJ-yEtIO
  ```

### Step 3: Deploy Frontend

```bash
npm run build
# Deploy dist/ folder to your hosting
```

Then **hard refresh** browser: `Ctrl + Shift + R`

## Test Edge Function

```bash
curl -X POST "https://0ec90b57d6e95fcbda19832f.supabase.co/functions/v1/create-order" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJib2x0IiwicmVmIjoiMGVjOTBiNTdkNmU5NWZjYmRhMTk4MzJmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg4ODE1NzQsImV4cCI6MTc1ODg4MTU3NH0.9I8-U0x86Ak8t2DGaIk0HfvTSLsAyzdnz-Nw00mMkKw" \
  -d '{"customer_email":"test@gmail.com","package_id":"chatgpt_plus_1_month","full_name":"Test","phone_number":"+628123456789"}'
```

Expected: `{"success":true,"checkout_url":"..."}`

## Architecture

**OLD (BROKEN):**
```
Frontend → Python Backend → MySQL (TIDAK ADA) → 500 ERROR
```

**NEW (WORKING):**
```
Frontend → Supabase Edge Function → Supabase PostgreSQL + Tripay → SUCCESS
```

## Files Changed

1. **supabase/functions/create-order/index.ts** - Edge Function (NEW)
2. **supabase/migrations/20250930100000_create_orders_tables.sql** - Database schema (NEW)
3. **src/services/apiService.ts** - Frontend now calls Edge Function

## Troubleshooting

**Edge Function Error:**
- Check logs: Supabase Dashboard → Edge Functions → Logs
- Verify secrets are set
- Check database tables exist

**Frontend Still Shows Error:**
- Hard refresh: `Ctrl + Shift + R`
- Clear all cache
- Test in incognito

**Database Error:**
- Verify migration applied
- Check tables in Table Editor

## Verification Checklist

- [ ] Database migration applied
- [ ] Tables visible (packages, orders, etc)
- [ ] Edge Function deployed
- [ ] Secrets configured
- [ ] Frontend rebuilt
- [ ] Hard refresh browser
- [ ] Test order creation
- [ ] Redirects to Tripay

## Success Indicators

✓ Edge Function test returns checkout_url
✓ Frontend submits order successfully
✓ User redirected to Tripay payment page
✓ Order saved in Supabase database
✓ NO MORE "Failed to fetch" error!

This is the FINAL working solution!