# Integration Notes

## Status: Website Go Live ✓

Website telah diubah dari demo mode ke production mode.

### Changes Made:

1. **Demo Mode Disabled**
   - `src/services/apiService.ts` - `USE_MOCK_API = false`
   - `src/components/DemoControls.tsx` - Demo controls tidak akan muncul lagi

2. **Backend Configuration**
   - File `backend/.env` telah dibuat dengan kredensial Tripay dan ChatGPT
   - API URL di frontend sudah dikonfigurasi: `https://api.aksesgptmurah.tech`

3. **Payment Gateway Integration (Tripay)**
   - Tripay API Key: `VI4hfWUhlfX70OZIjiae18pATyHOvNq0WjvBT6ej`
   - Merchant Code: `T45484`
   - Callback URL: `https://api.aksesgptmurah.tech/callback/tripay`
   - Production Mode: `true`

4. **ChatGPT Auto-Invite**
   - Admin Email: `cucbichvu34@gmail.com`
   - Admin URL: `https://chatgpt.com/admin?tab=members`

## Tripay IP Whitelist

Untuk menerima callback dari Tripay, Anda perlu menambahkan IP server backend ke whitelist Tripay:

### IP yang Perlu Di-Whitelist:
**Server backend Anda harus mendapatkan IP public yang nanti di-whitelist di dashboard Tripay.**

Cara mendapatkan IP server:
```bash
curl ifconfig.me
```

### Cara Whitelist IP di Tripay:
1. Login ke dashboard Tripay: https://tripay.co.id/member
2. Pergi ke menu **Settings** atau **Merchant Settings**
3. Cari bagian **Callback IP Whitelist**
4. Tambahkan IP server backend Anda
5. Simpan perubahan

**PENTING:** Tanpa whitelist IP, callback payment dari Tripay tidak akan diterima oleh sistem!

## Testing Payment Flow

### Test dengan Akun Tripay Production:
1. Jalankan backend:
   ```bash
   cd backend
   python app.py
   ```

2. Akses website di browser

3. Pilih paket dan isi form order

4. Klik "Lanjutkan Pembayaran"

5. **Expected Result:**
   - Order dibuat di database
   - User diarahkan ke halaman pembayaran Tripay (checkout_url)
   - Setelah pembayaran sukses, Tripay mengirim callback ke backend
   - Status order berubah menjadi 'paid'
   - Proses auto-invite ChatGPT dimulai

### Troubleshooting Payment:

Jika payment tidak bekerja, cek:

1. **Backend logs** - Lihat error di console backend
   ```bash
   tail -f backend/app.log
   ```

2. **Tripay API Response** - Cek response dari Tripay API di logs

3. **Database** - Cek apakah order tercreate di database:
   ```sql
   SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;
   ```

4. **IP Whitelist** - Pastikan IP server sudah di-whitelist di Tripay

## Testing ChatGPT Auto-Invite

### Manual Test:

```bash
cd backend
python test_chatgpt_invite.py test@example.com
```

Untuk debugging (browser visible):
```bash
python test_chatgpt_invite.py test@example.com
```

Untuk production (headless):
```bash
python test_chatgpt_invite.py test@example.com --headless
```

### Expected Behavior:
1. Script login ke ChatGPT dengan akun admin
2. Navigate ke halaman admin members
3. Klik "Invite member" button
4. Fill email dan select "Member" role
5. Click "Next" atau "Send"
6. Verify invitation sent

### Troubleshooting Auto-Invite:

Jika auto-invite gagal, cek:

1. **Selenium logs** - Lihat error di console
2. **Screenshots** - Cek folder `backend/screenshots/` untuk debugging
3. **ChromeDriver** - Pastikan ChromeDriver terinstall:
   ```bash
   which chromedriver
   ```
4. **Credentials** - Pastikan kredensial ChatGPT benar di `.env`

## Next Steps

1. ✓ Deploy backend ke server production
2. ✓ Set environment variables di server
3. ⚠ **WHITELIST IP SERVER** di dashboard Tripay
4. ✓ Test payment flow end-to-end
5. ✓ Test auto-invite functionality
6. ✓ Monitor logs untuk errors

## Support Contacts

- WhatsApp Support: +6281234567890 (update di ConfirmationPage.tsx line 294)
- Admin Email: admin@aksesgptmurah.tech

## Important Files Modified:

- `src/services/apiService.ts` - API integration
- `src/components/OrderForm.tsx` - Payment redirect
- `src/components/DemoControls.tsx` - Demo mode disabled
- `.env` - Frontend environment variables
- `backend/.env` - Backend credentials
- `backend/test_chatgpt_invite.py` - Manual testing script