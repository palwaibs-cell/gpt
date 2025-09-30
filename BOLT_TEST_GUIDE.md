# Testing di Bolt Environment - Step by Step

## IP BOLT UNTUK WHITELIST

**IPv4:** `34.34.229.13`
**IPv6:** `2600:1900:0:2e01::601`

**IP Range (recommended):**
```
34.34.229.0/24
2600:1900:0:2e01::/64
```

## LANGKAH TEST DI BOLT

### Option 1: Whitelist IP Bolt di Tripay (RECOMMENDED)

**Step 1: Whitelist IP di Tripay Dashboard**

1. Login: https://tripay.co.id/member (merchant T45484)
2. Go to: **Settings** → **API Settings** → **Whitelist IP**
3. Add IP:
   ```
   34.34.229.13
   2600:1900:0:2e01::601
   ```
   Atau add range:
   ```
   34.34.229.0/24
   2600:1900:0:2e01::/64
   ```
4. Save

**Step 2: Test API dari Bolt**

```bash
curl -X POST "https://pwnzbpkprtvvwrxveixn.supabase.co/functions/v1/create-order" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB3bnpicGtwcnR2dndyeHZlaXhuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkyMjY2OTEsImV4cCI6MjA3NDgwMjY5MX0.XN5F7FZrITcSMp95VIVHdELDF_A5oHvl95LC72BH-lo" \
  -d '{"customer_email":"test@gmail.com","package_id":"chatgpt_plus_1_month","full_name":"Test User","phone_number":"628123456789"}'
```

**Expected Success Response:**
```json
{
  "success": true,
  "order_id": "INV-1727689123456",
  "checkout_url": "https://tripay.co.id/checkout/T123456789ABCDE",
  "reference": "T123456789ABCDE",
  "payment_method": "QRIS",
  "amount": "25000",
  "status": "pending_payment"
}
```

**Step 3: Test dari Website**

1. Jalankan dev server: `npm run dev`
2. Open: http://localhost:5173
3. Fill form & submit
4. **Should redirect to Tripay!** ✅

---

### Option 2: Test Mode (Tanpa Tripay Real)

Jika belum mau whitelist IP, gunakan test mode dengan mock payment.

**Step 1: Enable Demo Mode**

Sudah saya siapkan demo mode di OrderForm component. Klik tombol "Demo Mode" di kanan atas form.

**Step 2: Test Fitur**

Dengan demo mode:
- ✅ Form validation works
- ✅ Package selection works
- ✅ Order summary updates
- ✅ Mock payment flow
- ❌ Real Tripay redirect (butuh IP whitelist)

---

## TESTING CHECKLIST

### Frontend Tests (No IP whitelist needed)

- [ ] Landing page loads
- [ ] Package cards display correctly
- [ ] Click "Pesan Sekarang" goes to order page
- [ ] Package selection works
- [ ] Form validation works
- [ ] Email validation
- [ ] Phone number validation
- [ ] Order summary updates correctly
- [ ] Price calculation correct

### Backend Tests (Need IP whitelist)

- [ ] Create order API returns success
- [ ] Order saved to database
- [ ] Tripay payment created
- [ ] Checkout URL returned
- [ ] Redirect to Tripay works
- [ ] Order status tracked

### Database Tests

```bash
# Check packages
curl -X POST "https://pwnzbpkprtvvwrxveixn.supabase.co/rest/v1/rpc/get_packages" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json"

# Check orders (after creating one)
# Login to Supabase Dashboard → Table Editor → orders
```

---

## TROUBLESHOOTING

### Error: "Payment gateway error"

**Cause:** IP belum di-whitelist di Tripay

**Solution:**
1. Whitelist IP Bolt: `34.34.229.13` atau `2600:1900:0:2e01::601`
2. Atau gunakan demo mode untuk test frontend saja

### Error: "Failed to fetch"

**Cause:** Edge Function belum deployed atau URL salah

**Solution:**
```bash
# Verify Edge Function
curl https://pwnzbpkprtvvwrxveixn.supabase.co/functions/v1/create-order
# Should return 400 (not 404)
```

### Error: "Invalid package"

**Cause:** Package ID tidak ada di database

**Solution:** Check packages table di Supabase dashboard

---

## SETELAH TEST SUKSES DI BOLT

### Step 1: Note Down What Works

Catat semua fitur yang sudah tested dan working:
- [ ] Form validation
- [ ] API calls
- [ ] Database saves
- [ ] Tripay integration
- [ ] Redirect flow

### Step 2: Prepare for VPS Deployment

1. **Get VPS IP:**
   ```bash
   # SSH to VPS
   curl https://api.ipify.org
   ```

2. **Update Tripay Whitelist:**
   - Remove Bolt IP (or keep for testing)
   - Add VPS IP
   - Save

3. **Deploy Frontend to VPS:**
   ```bash
   npm run build
   # Upload dist/ to VPS
   ```

4. **Test on VPS:**
   - Open your domain
   - Test full flow
   - Verify production works

### Step 3: Go Live Checklist

- [ ] VPS IP whitelisted di Tripay
- [ ] Frontend deployed to production domain
- [ ] Database verified (Supabase)
- [ ] Edge Function working
- [ ] Test order creation
- [ ] Test payment flow
- [ ] Test callback (setelah payment)
- [ ] Monitor logs

---

## BOLT IPs SUMMARY

**For Tripay Whitelist (saat testing di Bolt):**
```
34.34.229.13
2600:1900:0:2e01::601
```

**For Production (nanti):**
```
[Your VPS IP here]
```

---

## QUICK TEST COMMANDS

**Test Edge Function (from Bolt):**
```bash
curl -X POST "https://pwnzbpkprtvvwrxveixn.supabase.co/functions/v1/create-order" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB3bnpicGtwcnR2dndyeHZlaXhuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkyMjY2OTEsImV4cCI6MjA3NDgwMjY5MX0.XN5F7FZrITcSMp95VIVHdELDF_A5oHvl95LC72BH-lo" \
  -d '{"customer_email":"test@gmail.com","package_id":"chatgpt_plus_1_month","full_name":"Test","phone_number":"628123456789"}'
```

**Test Database:**
```bash
# Via Supabase Dashboard
# Go to: Table Editor → orders
# Should see test orders
```

**Test Frontend:**
```bash
npm run dev
# Open: http://localhost:5173
```

---

## SUPPORT

Jika ada error atau pertanyaan:
1. Check browser console (F12)
2. Check Edge Function logs (Supabase Dashboard)
3. Check error message details
4. Refer to TROUBLESHOOTING section above

Good luck testing! 🚀