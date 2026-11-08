# Kesiapan data FieldShift

Pembaruan setelah tahap 2: [audit dan pengayaan terbaru sebelum backend](audit-kelengkapan-data-fieldshift.md) serta [paket lengkap versi 2](fieldshift-data-publik-v2-2026-11-08.zip). Angka dan gap di bawah mempertahankan laporan snapshot awal; tambahan native tanah, Terra/Aqua dan kontrak input tersedia pada audit terbaru.

Disiapkan 8 November 2026 (Asia/Jakarta). Wilayah contoh Yogyakarta–Klaten; tanaman padi, jagung, kedelai.

**Pengumpulan dan penyiapan data publik inti selesai untuk prototipe area contoh.** Data mentah, data numerik terolah, sumber, metode, QA dan skrip reproduksi tersedia. Aplikasi belum dibuat. Rekomendasi spesifik lahan belum tervalidasi karena data lahan/petani belum tersedia.

## Data numerik yang tersedia

| Bagian | Cakupan nyata | Batas penggunaan |
|---|---|---|
| NASA POWER | 13.095 baris tanggal; 12 parameter; 1991–2025 serta 2026 parsial. Baseline 1991–2020: 10.958 hari / 360 bulan, tiap bulan kalender 30 tahun valid. | Konteks regional puluhan km. Nilai meteorologi terbaru valid 5 November 2026; radiasi dan ETo terakhir valid 2 November. Hari kosong setelah itu tetap kosong. |
| Air dari forcing iklim | ETo referensi FAO56 dan indikator P−ETo harian/bulanan. Persamaan dicek dengan contoh numerik FAO dan agregat diperiksa independen. | ETo referensi rumput; P−ETo bukan kebutuhan irigasi atau air tersedia pada akar. EVPTRNS asli tetap MJ/m²/hari. |
| MODIS vegetasi | Dua piksel pedesaan, masing-masing 115 komposit 2021–2025, NDVI/EVI, tanggal observasi dan flag kualitas. | Filter awan/QA wajib. Bulan tanpa komposit good tetap kosong; tidak diinterpolasi. Versi koleksi subset tidak diklaim bila API tidak menyebutkan. |
| SoilGrids | 180 raster kecil: 12 sifat × 5 kedalaman (0–100 cm) × mean/persentil 5/persentil 95. pH, tekstur, karbon, total N, CEC, bulk density, coarse fragments dan retensi air. | Prediksi 250 m, bukan uji laboratorium. 1.056 sel bernilai nol belum terjelaskan dan dikecualikan; bukan nodata terkonfirmasi atau nol fisik. |
| Elevasi dan lereng | Copernicus DEM GLO-30; subset Klaten, proyeksi UTM49S 30m, lereng dalam derajat. | Sumber ini Copernicus DSM, bukan NASADEM. Kanopi/bangunan dapat memengaruhi permukaan. |
| Tutupan lahan | ESA WorldCover 2021; klasifikasi titik, subset dan footprint MODIS sebenarnya. | Tahun 2021, bukan kondisi live atau bukti tanaman tertentu. |
| Agronomi dan GAEZ | 3 profil tanaman, 9 aturan bersyarat, contoh varietas Indonesia, 12 ekstraksi titik GAEZ (dua titik × tiga tanaman × dua rezim). | GAEZ baseline 2001–2020/AGERA5/HIST, grid 5 arc-minute. Kode kategori mengikuti legend resmi, bukan skor 0–100, hasil panen atau rekomendasi petak. |

## Kualitas dan pemilihan sampel vegetasi

Titik awal Yogyakarta ternyata **built-up** pada WorldCover 2021; titik awal Klaten berupa **tree cover** dan lingkungan campuran. Seri pertanian dipindahkan ke dua footprint MODIS di area rural Klaten. Piksel utama sekitar 84,47% cropland dan tanpa built-up; pembanding sekitar 69,21% cropland. Keduanya tetap mixed pixel dan tidak membuktikan batas lahan atau spesies tanaman.

| Piksel | Komposit tersimpan | Good strict | Marginal | Dikecualikan | Bulan punya data good |
|---|---:|---:|---:|---:|---:|
| klaten_cropland_primary | 115 | 42 | 21 | 52 | 31/60 |
| klaten_cropland_candidate | 115 | 42 | 22 | 51 | 32/60 |

Statistik bulanan utama memakai good strict saja. Marginal tersedia terpisah untuk peninjauan. Tanggal tanam/panen, fase tanaman, maupun masa lahan kosong tidak boleh disimpulkan otomatis dari seri yang jarang atau bercampur tutupan lahan.

## Data yang masih harus berasal dari petani atau validasi lokal

Batas/luas lahan, rotasi berjalan dan tanggal semai/tanam/panen, varietas, sumber/kapasitas irigasi dan drainase, riwayat tanah/hama/pengelolaan, sumber daya serta prioritas. Template 91 field dan tiga slot strategi tersedia dengan nilai kosong; varietas referensi bukan varietas yang telah dipilih petani.

Perbandingan pendapatan memerlukan harga jual, pembeli, biaya dan hasil panen yang relevan. Forecast musim operasional belum diambil. Model rotasi, kalibrasi varietas, nilai kredit nitrogen, perubahan kesehatan tanah dan peningkatan profit belum dihitung atau diklaim.

## Sumber tambahan

HLS, SMAP, GPM, ECOSTRESS, NASADEM dan GRACE tersimpan sebagai discovery/metadata pada audit awal, belum sebagai seri piksel ilmiah siap pakai. Status dan kebutuhan akses dicatat dalam `data/prepared/optional-sources.json`. Produk tambahan dapat dipilih sesuai kebutuhan; semua misi tersebut tidak wajib digunakan sekaligus. Tidak ada akun dibuat, integrasi Earth Engine dijalankan, atau arsip global diunduh.

## Struktur dan penggunaan

- `data/prepared/analysis-profile.json`: cakupan, aturan skala/waktu dan kebutuhan analisis.
- `data/prepared/climate/`: raw POWER, daily/monthly, baseline, kamus unit dan metode.
- `data/prepared/vegetation/`: raw MODIS, tabel komposit 16 hari + QA dan bulanan good-only.
- `data/prepared/soil-terrain/`: GeoTIFF, angka sel tanah, elevasi/lereng, WorldCover, footprint dan QA.
- `data/prepared/agronomy/`: referensi, bukti, GAEZ, template input dan strategi.
- `data/prepared/validation-report.json` dan `file-manifest.json`: pemeriksaan konsistensi dan SHA-256.
- `scripts/data/`: skrip data; dependency vendor lokal tidak dimasukkan ke ZIP.

Jalankan `py -3.11 scripts/data/validate_prepared_data.py` untuk pemeriksaan paket tanpa unduhan. Skrip per modul dan README menjelaskan reproduksi/unduhan masing-masing. Nilai numerik kosong tetap kosong. Setiap layer mempertahankan sumber, dukungan ruang, periode dan ketidakpastiannya saat digunakan bersama.

Sumber primer: [NASA POWER](https://power.larc.nasa.gov/docs/services/api/temporal/daily/), [ORNL DAAC MODIS](https://modis.ornl.gov/data/modis_webservice.html), [ISRIC SoilGrids](https://docs.isric.org/globaldata/soilgrids/), [FAO56](https://www.fao.org/4/x0490e/x0490e00.htm), [FAO GAEZ](https://gaez.fao.org/), [ESA WorldCover](https://esa-worldcover.org/). URL ekstraksi, waktu akses dan atribusi spesifik tersedia di manifest setiap modul.
