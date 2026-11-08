# FieldShift backend 0.1.0

API FastAPI/Python 3.11 untuk tahap 3 MVP. Data publik lokal dibaca saja; API tidak menjalankan scraper, menyimpan input petani, atau memakai database. Dataset harus berada pada folder proyek ini. Dependensi yang diuji ada di `requirements-lock.txt`.

Jalankan dari akar proyek dengan PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
.venv\Scripts\python.exe -m uvicorn backend.fieldshift.app:app --host 127.0.0.1 --port 8000
```

Buka [dokumentasi interaktif](http://127.0.0.1:8000/docs). Inisialisasi pertama memeriksa hash paket prepared dan supplemental; sumber yang hilang/rusak menghasilkan 503. Integritas diverifikasi sekali saat dimuat; restart setelah perubahan paket. Server mengikat loopback lokal. Hosting, autentikasi dan pembaruan sumber terjadwal belum termasuk tahap ini.

| Endpoint | Hasil |
|---|---|
| `GET /health` | Kesiapan aplikasi dan integritas paket saat dimuat |
| `GET /api/v1/catalog` | Cakupan, manifest, mode waktu, katalog sumber dan hash |
| `GET /api/v1/locations` | Dua titik contoh Klaten yang belum terverifikasi sebagai lahan |
| `GET /api/v1/crops` | Referensi padi, jagung dan kedelai |
| `GET /api/v1/input-contract` | JSON Schema dokumen parsial dan kebijakan pemakaian |
| `POST /api/v1/context` | Iklim, tanah, medan, vegetasi, GAEZ dan tutupan lahan |
| `POST /api/v1/climate/monthly` | Body sama dengan context (`window` wajib). Irisan bulanan layer iklim dengan aturan hari lengkap yang sama; bulan tidak lengkap tetap null, tanggal valid terakhir per metrik. Dipakai grafik frontend. |
| `POST /api/v1/compare` | Tiga slot strategi dan 12 pemeriksaan, status/missing inputs/sumber |
| `GET /api/v1/demo` | Request asumsi historis 2025 dan hasil yang dihitung ulang |

Jika `frontend/dist/index.html` ada saat server dimulai, aplikasi frontend hasil build juga disajikan di `/` (rute API tetap diutamakan). Panduan frontend: [frontend/README.md](../frontend/README.md).

Contoh request konteks:

```json
{
  "location": {"example_id": "klaten_cropland_primary"},
  "window": {"start_date": "2025-01-01", "end_exclusive": "2026-01-01"},
  "time_mode": "historical_replay"
}
```

Perbandingan menggunakan envelope `location`, `input_kind` (`scenario_assumption` atau `user_reported`), `assumptions`, `document` dan `slot_inputs` opsional. Request lengkap yang dapat diputar ulang ada di [backend-demo-request.json](../outputs/backend-demo-request.json); hasilnya di [backend-demo-response.json](../outputs/backend-demo-response.json). Tanggal akhir selalu eksklusif. Hari panen masih mengokupansi petak.

Dokumen memakai vocabulary kontrak 119 field yang diaudit. Field/anggota record boleh tidak dikirim; nilai hilang atau null tetap unknown. `planning.existing_sequence` berupa record tanaman; `planning.duration_by_crop` berupa daftar record durasi, bukan map. Asal durasi, konvensi hari nol dan sumber harus eksplisit sebelum kalender dihitung. Data durasi sumber dan catatan konversi dipertahankan; perubahan angka memerlukan kebijakan/catatan. Skenario asumsi wajib menyebutkan asumsinya dan tidak boleh menandai tanggal sebagai observasi.

`slot_inputs` eksplisit merupakan asumsi kalender bersama untuk alternatif pada posisi tersebut. Tanpa field ini, kalender diturunkan hanya dari record tanaman yang dikirim dan tidak dipakai untuk tanaman alternatif yang berbeda. Kalender tanaman pada prefix terkunci dipertahankan. Input parsial menghasilkan respons 200 dengan temuan `needs_input`, dan tidak menciptakan riwayat tanam atau prioritas. Konflik agronomi/okupansi yang bisa dianalisis tampil sebagai `input_conflict`; struktur, tipe, tanggal tidak valid, serta isian duplikat yang bertentangan menghasilkan 422.

Lokasi khusus memerlukan pasangan longitude/latitude; konteks POWER hanya dipakai bila `climate_context_id: "power_regional_yogyakarta"` dipilih eksplisit. Titik contoh memiliki konteks regional yang sudah dinyatakan. Layer lain memakai support sumber yang memuat titik, tanpa nearest fallback. Poligon non-null ditolak pada versi ini; luas tidak diturunkan dari titik. Referensi `context.*_reference_input` dan `layer_support` yang dikirim tidak menimpa ekstraksi layer lokal. Catatan laboratorium pengguna tetap dilabeli laporan yang belum diverifikasi. Field untuk fitur masa depan seperti ekonomi tidak mengaktifkan model hasil/profit.

Mode waktu: `historical_replay`, `recent_partial`, `historical_analogue_not_forecast`. Analog memakai kalender historis yang cocok, bukan prakiraan. Total dengan hari hilang tetap null per metrik. P−ETo adalah selisih bertanda, bukan kebutuhan irigasi. SoilGrids native memakai mask/CRS sumber; MODIS Terra/Aqua dipisahkan dengan QA strict-good dan gap tanpa interpolasi. BMKG dan FAO56 tambahan tetap referensi untuk pengembangan berikutnya; tidak dijadikan prakiraan musim atau model irigasi.

Tidak ada ranking, persentase hemat air, prediksi hasil, kredit nitrogen atau keuntungan. Prioritas hanya menyorot pemeriksaan; urutan alternatif deterministik dan bukan peringkat agronomi. Seluruh hasil masih `local_agronomic_validation: false`.

Batas input 256 KiB, maksimal 3 slot dan horizon 3.660 hari. CORS hanya origin localhost/127.0.0.1 port 5173 dan 3000. Kesalahan memiliki bentuk `{"error":{"code":"…","message":"…","details":[]}}`: 422 input invalid, 413 terlalu besar, 503 paket data unavailable, 500 kegagalan internal. Respons kesalahan tidak memantulkan payload atau jalur filesystem.

Verifikasi dan regenerasi artefak review:

```powershell
.venv\Scripts\python.exe scripts/verify_backend.py
```

Skrip menjalankan pengujian metode/backend, HTTP sungguhan pada port loopback sementara, memeriksa manifest, menulis [laporan](../outputs/backend-verification.json) serta [OpenAPI](../outputs/backend-openapi.json), lalu menghentikan server uji. Starlette 1.10 memberi peringatan deprecation untuk adapter TestClient/httpx; perilaku yang dipakai tetap diuji dan tidak mengubah dependensi runtime.
