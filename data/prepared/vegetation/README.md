# Data vegetasi contoh FieldShift

Paket ini berisi seri MODIS MOD13Q1 untuk **dua piksel contoh Klaten** selama
2021–2025, masing-masing 115 komposit. Titik dipilih setelah ESA WorldCover 2021
menunjukkan jangkar Yogyakarta lama (-7,8; 110,37) berada di kawasan built-up dan
jangkar Klaten lama (-7,72; 110,55) berada di kelas tree cover.

- **Primary** (`klaten_cropland_primary`): pusat grid turunan di sekitar
  (-7,721875; 110,553545). Pemeringkatan 74 footprint MODIS lengkap di dalam
  bbox contoh Klaten memilih piksel dengan **84,469% cropland, 11,727% grassland,
  3,803% tree cover, dan 0% built-up** menurut WorldCover 2021 (631 pusat sel).
  Digit panjang koordinat disimpan untuk konsistensi grid, bukan presisi GPS lahan.
- **Pembanding campuran** (`klaten_cropland_candidate`):
  (-7,7240416666666665; 110,546875), dengan **69,206% cropland, 19,683% tree cover,
  7,619% built-up, dan 3,492% grassland** pada footprint MODIS aktual (630 pusat sel).

Keduanya tetap **campuran penutup lahan**, bukan batas lahan pengguna, bukti
jenis tanaman, atau bukti bahwa penutup lahan masih sama pada 2026. Fraksi
berasal dari pusat sel WorldCover di dalam grid sinusoidal MODIS yang sebenarnya.
Angka 86,694% pada kotak pendekatan 250 m yang awalnya dipakai untuk mencari
pembanding bukan kemurnian piksel MODIS.

Bukti seleksi primary tersimpan pada
`data/prepared/soil-terrain/modis-cropland-pixel-candidates.json`; header respons
primary diperiksa ulang pada
`data/prepared/soil-terrain/modis-primary-footprint-landcover-summary.json` dan
`data/prepared/soil-terrain/processed/modis-primary-pixel-footprint.geojson`.
Fraksi tetap sama, 533/631 sel cropland. Bukti pembanding
ada pada `data/prepared/soil-terrain/modis-footprint-landcover-summary.json` dan
`data/prepared/soil-terrain/processed/modis-candidate-pixel-footprint.geojson`.
Flag MODIS `land_water=1` hanya berarti daratan, bukan bukti sawah.

## Berkas

- `modis_16day_qa.csv`: satu baris per titik dan komposit 16 hari, NDVI/EVI
  mentah dan terskala, hari observasi piksel, flag kualitas, alasan penolakan,
  dan nama respons sumber. Nilai berkualitas buruk tetap disimpan untuk audit.
- `modis_monthly_good_only.csv`: 60 bulan per piksel. Rata-rata NDVI/EVI hanya
  memakai baris `good_strict`. Sel kosong berarti tidak ada observasi yang lolos,
  bukan indeks nol. Bulan dengan satu nilai ditandai jarang/sparse.
- `summary.json`: jumlah observasi, flag kualitas, cakupan bulan, dan batch gagal.
- `verification_report.json`: hasil pemeriksaan tanggal, QA, skala, agregasi,
  dan integritas berkas sumber maupun turunan.
- `data-dictionary.json`: definisi kolom, unit, kode QA dan makna data kosong.
- `manifest.json`: URL, waktu pengambilan, ukuran, dan SHA-256 sumber serta hasil.
- `raw/`: respons tanggal tersedia dan subset satu piksel, maksimal 10 komposit
  per permintaan; setiap respons memiliki `.source.json`.
- `raw/excluded_context_points/`: semua unduhan jangkar Yogyakarta lama yang
  sempat diambil sebelum klasifikasi penutup lahan diperiksa. Dipertahankan
  untuk audit, **tidak dipakai** dalam CSV utama atau statistik. Path `file`
  dalam sidecar lama adalah path saat pengambilan, sebelum pengarsipan ke subfolder.
- `sources/`: metadata band API dan definisi bit QA NASA/LAADS yang disimpan.

## Unit, waktu, dan QA

Hasil pengambilan 8 November 2026: semua **230 komposit** 2021–2025 berhasil
diambil, tanpa batch gagal. Cakupan unduhan berbeda dari cakupan data yang lolos QA:

| Piksel | Good strict | Marginal untuk ditinjau | Dikecualikan | Bulan dengan good data | Bulan tanpa good data |
| --- | ---: | ---: | ---: | ---: | ---: |
| Primary | 42 | 21 | 52 | 31 dari 60 | 29 dari 60 |
| Pembanding campuran | 42 | 22 | 51 | 32 dari 60 | 28 dari 60 |

Deret utama masih memiliki banyak celah awan/kualitas dan **belum cukup untuk
menetapkan kalender tanam/panen atau rotasi pada lahan nyata**. Tidak ada celah
yang diisi dengan nol atau interpolasi. Versi prototipe perlu menampilkan
kekosongan ini; HLS atau sumber tambahan tetap memerlukan pemeriksaan akses/QA.

NDVI dan EVI merupakan indeks tanpa satuan. Nilai integer dikalikan **0,0001**
sesuai metadata band ORNL; rentang valid integer -2000–10000 dan fill -3000.
Metadata subset menyatakan ukuran sel proyeksi sinusoidal sekitar 231,656 m;
nama produk menggunakan resolusi nominal 250 m. Piksel dapat mencampur beberapa
petak atau penggunaan lahan.

`composite_start_date` adalah awal interval komposit, bukan selalu hari citra
terpilih. `selected_observation_date` berasal dari band hari-ke-dalam-tahun.
Ringkasan bulanan dikelompokkan menurut tanggal observasi terpilih. Jumlah
komposit menurut bulan awal interval disertakan terpisah. Tidak ada interpolasi,
pengisian awan, inferensi panen/tanam, atau prediksi musim.

Definisi QA mengikuti [NASA LAADS MOD13Q1 Collection 6.1 filespec](https://ladsweb.modaps.eosdis.nasa.gov/filespec/MODIS/61/MOD13Q1).
**Versi koleksi subset ORNL tidak disebutkan dalam respons**, sehingga paket ini
tidak mengklaim subset tersebut telah terbukti Collection 6.1. Definisi bit
didokumentasikan sebagai rujukan; flag mentah selalu dipertahankan.

Kebijakan seleksi konservatif proyek:

- `good_strict`: reliability=0, MODLAND=0, usefulness <=2, aerosol <=1,
  flag awan bersebelahan/awan campuran/salju/bayangan nol, pure-land=1,
  NDVI/EVI dan tanggal valid.
- `marginal_review`: reliability 0 atau 1, MODLAND <=1, usefulness <=10,
  aerosol <=2, flag awan/salju/bayangan nol dan pure-land=1, tetapi tidak memenuhi
  seleksi ketat. **Tidak dipakai** dalam rata-rata bulanan utama.
- `excluded`: semua baris lainnya, termasuk reliability=3 (berawan), dengan
  alasan terinci. Tidak dipakai untuk rekomendasi atau statistik bulanan utama.

Ambang usefulness/aerosol tersebut adalah keputusan seleksi proyek, bukan
ambang rekomendasi tanaman yang divalidasi NASA. Ketiadaan awan menurut QA
tidak membuktikan bebas semua kesalahan. Perubahan NDVI bukan bukti tunggal
jenis tanaman, kondisi hama, kesehatan tanah, atau manfaat suatu rotasi.

## Sumber dan penggunaan

Data NASA MODIS, didistribusikan oleh ORNL DAAC melalui
[REST API](https://modis.ornl.gov/data/modis_webservice.html). Cantumkan atribusi
NASA MODIS dan ORNL DAAC. Kebijakan sumber NASA tentang data terbuka tetap
berlaku; tidak diberikan lisensi baru untuk produk sumber oleh proyek ini.
Tidak diperlukan akun atau token untuk akses yang dipakai paket ini.

Skrip yang dapat dijalankan ulang dari root proyek:

```powershell
python scripts\data\vegetation\prepare_modis.py
python scripts\data\vegetation\prepare_modis.py --offline
python scripts\data\vegetation\verify_modis.py
```

Memakai Python standard library dan `curl.exe` Windows dengan verifikasi TLS
Schannel. Maksimal dua permintaan subset kecil berlangsung serentak. Data raw
yang sudah ada digunakan kembali agar server tidak diminta berulang. `--offline`
ditujukan untuk membangun ulang setelah semua raw tersimpan.
Batch yang gagal dicatat dan membuat exit code tidak nol; jumlah yang hilang
tidak dinyatakan lengkap. Lihat hasil verifikasi aktual di `summary.json`.
