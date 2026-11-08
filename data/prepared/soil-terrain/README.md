# Data tanah, topografi, dan tutupan lahan FieldShift

Disiapkan 8 November 2026 untuk area contoh Yogyakarta–Klaten. Paket ini berisi data numerik yang benar-benar diunduh dan diperiksa, bukan hanya metadata. Belum ada batas lahan pengguna yang terverifikasi.

## Isi dan hasil pemeriksaan

- **SoilGrids:** 180 GeoTIFF kecil = 12 sifat × 5 kedalaman × mean/Q0.05/Q0.95. Kedalaman 0–5, 5–15, 15–30, 30–60, dan 60–100 cm; bbox 110.54,−7.73,110.56,−7.71. Tiap raster keluaran 9×8 sel WGS84; resolusi sumber nominal 250 m. Lima raster `cfvo` Q0.05 seluruhnya nol dan belum diinterpretasikan. Sebanyak 175 raster mempunyai nilai nonzero yang bisa diperiksa.
- `processed/soil-cells.csv`: **12.960 baris sel**, mencakup **11.900 nilai yang dipertahankan untuk interpretasi**, **1.056 nol ambigu**, dan **4 sentinel −32768**. `raw_value` selalu dipertahankan. Kolom `value` kosong untuk nilai yang dikecualikan; periksa `qa_status`.
- `processed/soil-summary.csv`: ringkasan per sifat/kedalaman/statistik. Semua grid selaras. Tidak ditemukan nilai di luar batas fisik dasar yang diperiksa. Q0.05 ≤ Q0.95 pada pasangan yang mempunyai nilai valid; lima pasangan `cfvo` tidak bisa diperiksa karena Q0.05 semuanya nol. Jumlah mean pasir+debu+liat **99,9–100,1%**. Mean retensi air monoton turun dari 10→33→1500 kPa pada seluruh sel yang dapat dibandingkan.
- **Copernicus DEM GLO-30 DSM:** subset 74×74 sel sumber. Ini fallback topografi publik; NASADEM masih metadata pada audit sebelumnya. Elevasi diproyeksikan bilinear ke **EPSG:32749, grid 30 m**, kemudian lereng dihitung dengan beda hingga terpusat dalam satuan meter. Elevasi sekitar **158,4–202,6 m**, lereng valid sekitar **0,02–10,68°**. Lereng pada tepi grid dikecualikan. DSM mencakup vegetasi/bangunan dan bukan survei elevasi tanah kosong.
- **ESA WorldCover 2021 v200:** subset 10 m untuk dua lokasi awal, serta masker footprint MODIS terpilih. Label 2021 tidak menjamin kondisi 2026 atau spesies tanaman saat ini.

## Lokasi observasi yang ditetapkan

Lokasi telah dibekukan setelah pemeriksaan tutupan lahan. Semua tetap merupakan piksel observasi contoh dan bukan batas petak milik pengguna.

| Peran | Lintang, bujur | Fraksi cropland WorldCover 2021 dalam footprint MODIS aktual |
|---|---|---:|
| Utama | −7.721875031299882, 110.55354472008753 | 533/631 sel = **84,469%**; 0% built-up |
| Pembanding | −7.7240416666666665, 110.546875 | 436/630 sel = **69,206%**; 7,619% built-up |

Fraksi ini dihitung dalam batas piksel sinusoidal **yang dilaporkan REST MODIS**, bukan kotak 250 m yang digambar di sekitar koordinat permintaan. Grid nominal produk adalah 250 m; ukuran sel sinusoidal yang dilaporkan 231,656358264 m. Polygon didensifikasi, ditransformasi memakai proyeksi sinusoidal sphere R=6371007.181, lalu sel WorldCover dipilih berdasarkan titik tengah di dalam polygon. GeoJSON dan masker raster tersimpan di `processed/`.

Kedua piksel masih campuran; NDVI/EVI tidak boleh disebut hasil satu petak sawah. Pada titik awal Yogyakarta (−7.8,110.37), WorldCover menunjukkan built-up dan kotak konteks 250 m sekitar 99,45% built-up. Titik awal Klaten (−7.72,110.55) berkelas tree cover. Keduanya hanya konteks historis uji akses. Hasil kotak proxy 250 m yang lebih lama tetap disimpan dengan labelnya dan tidak digunakan sebagai fraksi footprint MODIS.

## Sifat dan konversi satuan

Angka mentah dibagi faktor berikut menurut tabel FAQ SoilGrids yang disimpan di `raw/soilgrids-faq.html`.

| Sifat | Pembagi | Satuan hasil |
|---|---:|---|
| phh2o | 10 | pH air |
| sand, silt, clay | 10 | % massa |
| soc | 10 | g/kg karbon organik |
| nitrogen | 100 | g/kg nitrogen total |
| cec | 10 | cmol(c)/kg |
| bdod | 100 | g/cm³, setara kg/dm³ |
| cfvo | 10 | % volume fragmen kasar |
| wv0010, wv0033, wv1500 | 10 | % volume air pada 10, 33, 1500 kPa |

Coverage WCS 33 kPa bernama `wv0033`; tabel FAQ menyingkatnya sebagai `wv003`. Tidak dihitung kapasitas air profil dalam mm, air yang tersedia saat ini, atau kebutuhan irigasi. Nitrogen total tidak sama dengan nitrogen tersedia bagi tanaman. Tidak tersedia data laboratorium P/K tersedia, salinitas, drainase, muka air tanah, maupun riwayat pemupukan pengguna.

## Nol, ketidakpastian, dan batas penggunaan

GeoTIFF WCS ini tidak memuat tag nodata. Header VRT sumber untuk sembilan sifat tanah pokok menyatakan −32768 sebagai nodata. **Nol tidak otomatis dinyatakan nodata**, dan nol `cfvo` Q0.05 dapat merupakan nilai rendah yang sah. Sel nol tetap disimpan tetapi sementara dikecualikan dari ringkasan/konversi, termasuk empat sel nol pada pH contoh lama. Ini kebijakan konservatif, bukan klaim bahwa setiap nol salah. Header VRT pada jalur yang dicoba untuk tiga sifat retensi air mendapat 404; unduhan WCS ketiganya tetap berhasil dan satuannya didokumentasikan FAQ.

Q0.05 dan Q0.95 merupakan batas interval prediksi 90% marginal per sel/sifat. Mengambil rata-rata batas piksel tidak menghasilkan interval kepercayaan rata-rata wilayah. Semua properti merupakan prediksi SoilGrids; angka tidak menggantikan uji tanah, validasi agronomi lokal, atau verifikasi petak. Resolusi grid hasil reproyeksi tidak menciptakan informasi yang lebih rinci.

## Sumber, lisensi, dan reproduksi

- [ISRIC SoilGrids FAQ dan satuan](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html), [WCS](https://docs.isric.org/globaldata/soilgrids/wcs.html). Atribusi **ISRIC SoilGrids**, CC BY 4.0.
- [Copernicus DEM pada AWS](https://registry.opendata.aws/copernicus-dem/), metadata [Planetary Computer](https://planetarycomputer.microsoft.com/api/stac/v1/collections/cop-dem-glo-30). Gunakan lisensi Copernicus DEM yang ditautkan sumber tersebut saat mempublikasikan; produk ini bukan data NASADEM. Atribusi **Copernicus DEM / European Union / ESA / Airbus / DLR**.
- [ESA WorldCover data access](https://esa-worldcover.org/en/data-access). CC BY 4.0; atribusi **ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium**.

`manifest.json` memuat URL, waktu akses, checksum berkas, versi runtime, dan inventaris. `quality-report.json` memuat pemeriksaan numerik. Berkas `*-source-vrt-head.xml` sengaja hanya 8.192 byte pertama dan dapat berupa XML yang tidak lengkap. Tidak ada arsip raster global diunduh; transfer COG memakai pembacaan jendela/range dan total byte jaringan range tidak diukur.

Skrip berada di `scripts/data/soil-terrain/`. Gunakan Python 3.12 dengan `numpy` dan `rasterio`; instal dependensi lokal dengan `python -m pip install --target scripts/data/soil-terrain/_vendor -r scripts/data/soil-terrain/requirements.txt`. Folder `_vendor` merupakan runtime lokal dan **tidak perlu disertakan dalam paket data**. Jalankan berurutan:

```text
python scripts/data/soil-terrain/prepare_soil_terrain.py all
python scripts/data/soil-terrain/prepare_landcover.py
python scripts/data/soil-terrain/fetch_metadata.py
python scripts/data/soil-terrain/check_modis_footprint.py primary
python scripts/data/soil-terrain/check_modis_footprint.py
python scripts/data/soil-terrain/validate_and_catalog.py
```

Pemeriksaan footprint pembanding membaca raw seri MODIS di folder `vegetation`. Peringkat kandidat sebelumnya disimpan untuk jejak audit, dan tidak perlu menjalankan eksplorasi lokasi lagi.
