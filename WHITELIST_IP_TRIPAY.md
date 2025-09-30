# Whitelist IP Supabase di Tripay - FIX TERAKHIR!

## STATUS SEKARANG

✅ Edge Function deployed
✅ Database ready
✅ Frontend built
❌ **Tripay IP belum whitelisted** ← FIX THIS NOW!

## IP yang Perlu Di-Whitelist

**Supabase Edge Functions IP Range:**
```
2600:1f1c:e:2300::/52
```

Atau tambah semua IP ini:
```
2600:1f1c:e:2300::/56
2600:1f1c:e:2304::/56
2600:1f1c:e:2306::/56
```

**⚠️ PENTING:** IP ini HARUS di-whitelist agar Edge Function bisa call Tripay API!

## Langkah-langkah Whitelist IP:

### 1. Login ke Dashboard Tripay
- Buka: https://tripay.co.id/member
- Login dengan merchant **T45484**

### 2. Masuk ke API Settings
- Di sidebar, klik **"API Settings"** atau **"Whitelist IP"**
- Atau langsung ke: https://tripay.co.id/member/api-setting

### 3. Tambah IP Supabase
- Klik tombol **"Add IP"** atau **"Tambah IP"**
- Masukkan salah satu:
  - `2600:1f1c:e:2300::/52` (recommended - covers all)
  - Atau `0.0.0.0/0` (allow all - easiest but less secure)
- Klik **"Save"**

### 4. Test Immediately
```bash
curl -X POST "https://pwnzbpkprtvvwrxveixn.supabase.co/functions/v1/create-order" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB3bnpicGtwcnR2dndyeHZlaXhuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkyMjY2OTEsImV4cCI6MjA3NDgwMjY5MX0.XN5F7FZrITcSMp95VIVHdELDF_A5oHvl95LC72BH-lo" \
  -d '{"customer_email":"test@gmail.com","package_id":"chatgpt_plus_1_month","full_name":"Test","phone_number":"+628123456789"}'
```

**Expected:** `{"success":true,"checkout_url":"..."}`

## Mengapa Whitelist IP Diperlukan?

Tripay menggunakan whitelist IP sebagai keamanan tambahan untuk webhook callback. Ketika ada transaksi yang berhasil/gagal, Tripay akan mengirim callback ke URL:

```
https://api.aksesgptmurah.tech/callback/tripay
```

Jika IP server tidak di-whitelist, Tripay akan **MENOLAK** untuk mengirim callback, sehingga:
- ❌ Status payment tidak terupdate di database
- ❌ Auto-invite ChatGPT tidak jalan
- ❌ Customer tidak mendapat invite

## Troubleshooting

### Callback Tidak Diterima?

1. **Cek IP di Tripay Dashboard**
   - Pastikan IP `34.34.229.15` ada di whitelist
   - Pastikan statusnya Active

2. **Cek Backend Logs**
   ```bash
   tail -f backend/app.log
   ```
   Cari log: "Tripay callback received"

3. **Test Manual Callback**
   - Buat transaksi test di Tripay Sandbox
   - Cek apakah callback masuk ke backend

4. **Cek Callback URL di Tripay**
   - Pastikan callback URL sudah diset: `https://api.aksesgptmurah.tech/callback/tripay`

## Kontak Support

Jika masih ada masalah:
- Email: admin@aksesgptmurah.tech
- WhatsApp: +6281234567890

---

**Status saat ini:**
- ✅ Backend API: Running
- ✅ Callback URL: Configured
- ⚠️ IP Whitelist: **PERLU DITAMBAHKAN MANUAL**