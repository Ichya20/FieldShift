# FieldShift frontend 0.1.0

Landing page responsif dengan diorama 3D (three.js) dan alat eksplorasi dalam satu halaman: kondisi lokasi, susun skenario, perbandingan tiga strategi, serta sumber & metode. Semua angka berasal dari API FastAPI di `backend/`; frontend tidak menyimpan isian.

Stack: React 19, TypeScript 7, Vite 8, three.js r187, Leaflet 1.9, Libre Franklin (self-hosted), ikon Lucide.

## Menjalankan

Backend harus berjalan lebih dulu (dari akar proyek):

```powershell
.venv\Scripts\python.exe -m uvicorn backend.fieldshift.app:app --port 8000
```

Mode pengembangan (hot reload, proxy `/api` dan `/health` ke 127.0.0.1:8000):

```powershell
cd frontend
npm install
npm run dev
```

Buka http://localhost:5173. Untuk mencoba dari HP di jaringan yang sama, jalankan `npx vite --host` lalu buka alamat Network yang ditampilkan.

Satu server saja: `npm run build` menghasilkan `frontend/dist`. Setelah backend di-restart, FastAPI menyajikan aplikasi di http://127.0.0.1:8000/ dan rute API tetap diutamakan.

`npm run typecheck` memeriksa tipe tanpa build. Variabel opsional `VITE_API_BASE` mengarahkan frontend ke API di origin lain.

## Struktur

| Lokasi | Isi |
|---|---|
| `src/diorama/` | Scene three.js: blok tanah 1 m dengan penampang horizon (shader), pematang, padi/jagung/kedelai prosedural ber-instancing, cahaya matahari tunggal, bayangan kontak. Render on-demand, berhenti saat di luar layar, statis untuk reduced motion. |
| `src/components/` | Header, hero, kondisi lokasi (peta Leaflet, grafik SVG), formulir bertahap, perbandingan (papan, kalender, matriks 12 pemeriksaan, tampilan per aspek di HP), drawer bukti & sumber. |
| `src/lib/` | Klien API, tipe respons, format angka/tanggal Indonesia, label status/aturan, pembentuk request `/api/v1/compare`. |
| `public/textures/` | Tekstur tanah CC0 dari Poly Haven (lihat README di folder itu). |

## Batas yang dijaga

- Nilai kosong dikirim sebagai field yang dihilangkan (unknown), bukan nol. “Tidak ada catatan” dikirim sebagai daftar kosong.
- Tanggal akhir di formulir inklusif dan diubah ke `end_exclusive` (+1 hari).
- Grafik iklim bulanan memakai `POST /api/v1/climate/monthly`; bulan dengan hari tidak lengkap tidak digambar. Grafik MODIS hanya titik `good_strict`, Terra dan Aqua terpisah, gap diarsir.
- Tidak ada ranking, skor, prediksi hasil, persen hemat air, atau profit. Diorama berlabel “Ilustrasi skenario”.
- Peta dasar memakai tile OpenStreetMap (digrayscale lewat CSS hanya pada lapisan tile); jika gagal, pemilih contoh dan koordinat tetap berfungsi.
