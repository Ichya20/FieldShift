# Tambahan iklim dan vegetasi FieldShift

Snapshot audit **8 November 2026**. Paket ini terpisah dari `data/prepared/` yang
dibekukan. Tidak ada backend, bobot/skor, riwayat petani atau data lahan yang
dibuat. Semua berkas baru berada di folder supplemental ini atau skrip terkait.

## Kekurangan dan tambahan

Sebelum penambahan, vegetasi hanya terdiri atas Terra MOD13Q1 2021–2025 pada dua
piksel Klaten: 115 komposit per piksel, dengan strict-good pada 31/60 bulan
primary dan 32/60 bulan pembanding. Paket menambahkan:

- **MOD13Q1/Terra 2026**, sesuai tanggal yang benar-benar tersedia pada katalog;
  sampai komposit dengan tanggal awal 16 Oktober pada pemeriksaan ini.
- **MYD13Q1/Aqua 2021–2026**, sensor tambahan yang mempunyai jadwal komposit
  berbeda. Katalog 2026 yang diperiksa berakhir pada tanggal awal 8 Oktober.
- **NASA POWER 25 Oktober–7 November 2026**, pemeriksaan ulang 12 parameter di
  titik regional lama (-7,8; 110,37), dengan unit asli, nilai kosong dan ETo
  referensi FAO56 yang dihitung memakai persamaan serta guard yang sama.

Jumlah aktual, QA, tanggal observasi terakhir, perubahan ketersediaan dan
kekurangan tersisa tercatat dalam `summary.json`. Katalog komposit, tanggal
observasi piksel, waktu pemrosesan dan waktu unduh adalah waktu yang berbeda.
Tidak satu pun diberi label kondisi lahan real-time.

Hasil numerik terverifikasi: **304 komposit tambahan**, berupa 38 Terra dan
266 Aqua; 3.648 entri band-piksel mentah. Sebanyak 69 komposit lolos strict-good,
53 marginal dan 182 dikecualikan. Seluruh komposit yang diminta dan tersedia
pada katalog berhasil diambil; ini tidak berarti semua kebutuhan pengetahuan
agronomi atau kondisi lahan sudah lengkap.

| Riwayat 2021–2025 | Sebelum: bulan Terra strict-good | Sesudah: bulan dengan observasi good dari salah satu sensor | Tetap kosong pada keduanya |
| --- | ---: | ---: | ---: |
| Primary | 31/60 | 34/60 | 26/60 |
| Pembanding | 32/60 | 35/60 | 25/60 |

Tiga bulan tambahan primary: Agustus 2021, Maret 2022, Juni 2023. Tiga bulan
tambahan pembanding: Agustus 2021, Januari 2023, Juni 2023. Angka sesudah hanya
diagnostik ketersediaan, bukan seri indeks gabungan. Strict-good terbaru pada
snapshot ini adalah **21 September 2026 untuk Terra** dan **22 September 2026
untuk Aqua** pada kedua piksel; komposit Oktober yang tersedia tidak otomatis
lolos kualitas. Semua header footprint tambahan sama dengan grid Terra lama
(selisih maksimum 0 m pada x/y origin dan cellsize yang dilaporkan).

## Berkas dan identitas sensor

- `MOD13Q1-supplemental-qa.csv` dan `MOD13Q1-monthly-good-only.csv`: Terra 2026.
- `MYD13Q1-supplemental-qa.csv` dan `MYD13Q1-monthly-good-only.csv`: Aqua 2021–2026.
- `POWER-recent-recheck.csv`: pemeriksaan publikasi terbaru, **tidak mengganti**
  nilai historis atau null pada paket lama.
- `raw/` menyimpan respons asli beserta `.source.json`; `sources/` berisi
  metadata band dan rujukan QA yang berhasil diakses.
- `footprint-comparison.json`: header grid setiap respons dan selisih terhadap
  grid Terra lama. Tidak ada resampling atau penggabungan indeks antarsensor.
- `manifest.json`: URL, HTTP bila terekam, waktu UTC, upaya akses, ukuran, SHA-256
  sumber/turunan, serta hash input lama yang hanya dibaca.
- `frozen-prepared-before.json`: inventaris hash seluruh paket lama sebelum
  pengambilan tambahan; `verification.json` dan `local-verification.json`
  melaporkan hasil pengecekan.

Koordinat primary sekitar (-7,721875; 110,553545); pembanding sekitar
(-7,724042; 110,546875). Keduanya merupakan piksel contoh, bukan lahan terverifikasi.
WorldCover 2021 menunjukkan 84,469% dan 69,206% cropland pada footprint Terra
masing-masing. Angka historis tersebut tidak membuktikan tanaman atau penggunaan
lahan pada 2026; footprint Aqua tetap disimpan dan diperiksa tersendiri.

## QA dan interpretasi

NDVI/EVI tanpa satuan; integer dikalikan 0,0001. Fill dan nilai di luar rentang
valid tidak dipakai. Bit VI Quality dan pixel reliability diuraikan. Seleksi
strict-good mengikuti kebijakan konservatif lama: reliability=0, MODLAND=0,
usefulness<=2, aerosol<=1, awan/salju/bayangan tidak terdeteksi dan flag daratan.
Marginal dan excluded tetap disimpan untuk audit, tetapi tidak masuk mean utama.
Hari observasi dari band day-of-year harus dapat ditempatkan pada interval
komposit. Hari yang tidak bisa diselesaikan secara pasti dikecualikan, tanpa
menebak tahun atau mengisi data.

Terra dan Aqua ditampilkan sebagai **seri terpisah**. Diagnostik "bulan dengan
setidaknya satu observasi good dari salah satu sensor" hanyalah pemeriksaan
ketersediaan. Ia tidak menghasilkan mean gabungan, tidak mengisi seri Terra,
dan bukan hasil harmonisasi antarplatform. Bulan tanpa data tetap kosong;
tidak ada interpolasi, dugaan jenis tanaman, masa fallow, tanggal tanam/panen
atau manfaat rotasi dari indeks ini.

ORNL tidak menyebut versi koleksi pada respons subset. Definisi C6.1 yang
dirujuk tidak membuktikan versi koleksi subset. Metadata band Aqua diambil
tersendiri. URL LAADS khusus MYD13Q1 yang gagal dihentikan setelah tiga percobaan
dan kegagalannya disimpan; rujukan alternatif provider dicatat terpisah bila
berhasil. Rujukan bit MODIS VI NASA lama tetap tersedia dengan hash aslinya.

## Batas iklim dan penggunaan berikutnya

Pemeriksaan ulang POWER menunjukkan jeda publikasi yang sama: hujan/meteorologi
valid terakhir **5 November 2026**, radiasi dan ETo **2 November 2026**. Hari yang
belum dipublikasikan tetap null. Sebanyak 14 tanggal diperiksa ulang; tidak ada
nilai baru, revisi nilai atau penambahan tanggal valid dibanding paket beku.
ETo adalah referensi rumput, bukan ET tanaman
atau kebutuhan irigasi. P−ETo bukan neraca air tanah lengkap. EVPTRNS tetap
MJ/m²/hari; GWETROOT/GWETTOP tetap indikator kebasahan model tanpa satuan.
Hari memakai LST sumber, bukan pengelompokan hari WIB.

Prakiraan musim, iklim masa depan, kondisi petak, riwayat petani, irigasi,
varietas dan validasi agronomi lokal masih diperlukan untuk penggunaan yang
membutuhkannya. BMKG jangka pendek ditangani pada audit lain; paket ini tidak
menyalin atau menyamakan prakiraan tersebut dengan baseline atau prakiraan musim.

Reproduksi snapshot menggunakan Python 3.11 stdlib dan curl Windows:

```powershell
py -3.11 scripts/data/supplemental_environment/prepare_environment.py
py -3.11 scripts/data/supplemental_environment/verify_environment.py
```

Sesudah cache lengkap, gunakan `--offline` untuk pembentukan ulang. Maksimal dua
permintaan berjalan bersamaan dan maksimal tiga upaya per URL. Kegagalan yang
sudah tercatat tidak dicoba ulang secara otomatis. Untuk snapshot masa depan,
buat cakupan/tanggal baru secara eksplisit; jangan menamai data historis sebagai
prakiraan atau menimpa paket beku.
