# Panduan Whitelist IP di Tripay

## IP Server yang Perlu Di-Whitelist

```
34.34.229.15
```

**⚠️ PENTING:** IP ini HARUS di-whitelist di dashboard Tripay agar callback payment bisa diterima oleh sistem!

## Langkah-langkah Whitelist IP:

### 1. Login ke Dashboard Tripay
- Buka: https://tripay.co.id/member
- Login dengan akun Merchant Tripay Anda

### 2. Masuk ke Menu Settings
- Di sidebar, klik **"Settings"** atau **"Merchant Settings"**
- Atau langsung ke: https://tripay.co.id/member/merchant-setting

### 3. Cari Section "Callback IP Whitelist"
- Scroll ke bawah sampai menemukan section **"Callback IP Whitelist"**
- Biasanya ada di bagian "Security" atau "Webhook Settings"

### 4. Tambah IP Server
- Klik tombol **"Add IP"** atau **"Tambah IP"**
- Masukkan IP: `34.34.229.15`
- Klik **"Save"** atau **"Simpan"**

### 5. Verifikasi
- Pastikan IP `34.34.229.15` muncul di list whitelist
- Status harus **Active** atau **Enabled**

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