# Deploy ke Production - Langkah Final

## Files yang Harus Di-Upload

Upload semua files dari folder `dist/` ke root website Anda:

```
dist/
  ├── index.html
  ├── .htaccess          ← PENTING untuk routing!
  ├── _redirects         ← Untuk Netlify
  ├── vercel.json        ← Untuk Vercel
  └── assets/
      ├── index-xxx.css
      └── index-xxx.js
```

## Cara Upload via cPanel/FTP

1. **Login ke cPanel** (https://aksesgptmurah.tech/cpanel)

2. **Buka File Manager**
   - Masuk ke folder `public_html/`

3. **Hapus file lama** (jika ada)
   - Pilih semua file
   - Delete

4. **Upload file baru**
   - Klik "Upload"
   - Drag & drop semua files dari folder `dist/`
   - Pastikan struktur folder tetap sama

5. **Set Permissions**
   - File `.htaccess` harus ada
   - Permission: 644

## Testing Setelah Upload

1. **Test Landing Page**
   ```
   https://aksesgptmurah.tech/
   ```
   Harus muncul homepage dengan package pricing

2. **Test Order Flow**
   - Klik "Mulai Berlangganan"
   - Isi form dengan email valid
   - Klik "Lanjutkan ke Pembayaran"
   - **Harus redirect ke Tripay** dengan nominal Rp 1.000

3. **Test Confirmation Page**
   - Setelah payment di Tripay, klik "Kembali ke Merchant"
   - **Harus muncul confirmation page** (bukan 404!)
   - URL: `https://aksesgptmurah.tech/confirmation?order_id=INV-xxx...`

## Troubleshooting

### Jika masih 404 setelah payment:

1. **Check .htaccess ada dan aktif**
   ```bash
   ls -la public_html/.htaccess
   ```

2. **Test mod_rewrite aktif**
   Buat file `test.php`:
   ```php
   <?php phpinfo(); ?>
   ```
   Cari "mod_rewrite" → harus "Enabled"

3. **Alternatif: Gunakan index.php redirect**
   Jika .htaccess tidak work, buat file `index.php`:
   ```php
   <?php
   header('Location: /index.html');
   exit;
   ?>
   ```

### Jika order tidak tersimpan:

1. Check Supabase connection di browser console
2. Verify VITE_SUPABASE_URL dan VITE_SUPABASE_ANON_KEY di build

## Environment Variables di Build

File `.env` sudah di-hardcode di `apiService.ts`, jadi build langsung include credentials:

```typescript
SUPABASE_URL = 'https://pwnzbpkprtvvwrxveixn.supabase.co'
SUPABASE_ANON_KEY = 'eyJhbGc...'
```

Tidak perlu setup env variables di server.

## Next Steps Setelah Deploy

1. **Update harga dari Rp 1.000 ke harga normal**
   ```sql
   UPDATE packages
   SET price = 29000
   WHERE id = 'chatgpt_plus_1_month';
   ```

2. **Test full flow dengan payment real**

3. **Setup webhook Tripay** (untuk auto-update payment status)
   - URL: `https://pwnzbpkprtvvwrxveixn.supabase.co/functions/v1/tripay-webhook`

4. **Monitoring**
   - Check Supabase Dashboard untuk orders baru
   - Monitor error logs

## Support

Jika ada masalah, check:
- Browser Console (F12) untuk errors
- Supabase Logs di dashboard
- Tripay transaction logs

---

**Build Date:** 2025-09-30
**Version:** 1.0.0