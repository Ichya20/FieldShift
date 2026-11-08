# Audit data untuk Field Shift: Adapting Farms with NASA Data

Tanggal pemeriksaan: **8 November 2026** (Asia/Jakarta). Area contoh: Yogyakarta dan Klaten, Indonesia. Lokasi ini dipakai untuk menguji akses, belum merupakan lahan pengguna yang terverifikasi. Pekerjaan ini hanya pencarian dan pemeriksaan data; aplikasi belum dibuat.

## Kesimpulan

**NASA POWER saja belum lengkap.** Sebagian besar sumber untuk membangun aplikasi sesuai arah challenge tersedia, tetapi perlu menggabungkan data NASA, peta tanah, referensi tanaman, dan informasi dari petani. Belum ada paket rekomendasi rotasi siap pakai yang sudah tervalidasi untuk satu lahan.

[Halaman challenge](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/) mengarahkan penggunaan observasi Bumi NASA bersama informasi tanah, karakteristik tanaman, dan prioritas petani. Daftar misi yang disebut merupakan pilihan sumber, bukan kewajiban memakai semuanya. Halaman yang diperiksa menyebut Resources baru tersedia **Jumat, 13 November 2026**, sehingga daftar resource akhir dari penyelenggara belum bisa diperiksa hari ini.

## Pemetaan kebutuhan dan sumber

| Kebutuhan | Dataset dan kemampuan | Skala | Status yang benar-benar diperiksa |
|---|---|---|---|
| Suhu, hujan, radiasi, kelembapan, angin | [NASA POWER Daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) | Harian; meteorologi MERRA-2 sekitar 0,5° × 0,625°, atau puluhan kilometer | **Data numerik berhasil diunduh**: 12 variabel, satu titik, 2021–2025. |
| Kelembapan tanah | [SMAP SPL3SMP_E v006](https://nsidc.org/data/spl3smp_e/versions/6), [SPL4SMGP v008](https://nsidc.org/data/spl4smgp/versions/8) | Grid 9 km; L3 harian, L4 rata-rata 3 jam | Metadata beririsan Yogyakarta ditemukan; nilai piksel belum diunduh. L3 permukaan; L4 zona akar merupakan hasil asimilasi model. |
| Curah hujan lebih rinci | [GPM IMERG](https://gpm.nasa.gov/data/imerg), produk harian Final/Late | 0,1°, sekitar 11 km | Metadata ditemukan. Final V07 terakhir 30 September 2025; Late tersedia sampai 6 November 2026 pada probe ini. |
| Vegetasi dan pola musim | [MOD13Q1 / MODIS NDVI–EVI](https://modis.gsfc.nasa.gov/data/dataprod/mod13.php) | Nominal 250 m; komposit 16 hari | **Sampel angka berhasil diunduh** melalui [REST ORNL DAAC](https://modis.ornl.gov/data/modis_webservice.html). Contoh perlu filter kualitas. |
| Vegetasi lebih rinci | [HLS L30/S30 dan HLS-VI v2.0](https://hls.gsfc.nasa.gov/data-access-and-tools/) | 30 m; observasi berulang, bergantung awan | Metadata scene dan band NDVI ditemukan. Raster ilmiah belum diunduh. Jalur NASA memerlukan Earthdata Login. |
| Suhu permukaan, evapotranspirasi, stres evaporatif | [ECOSTRESS LST v003](https://doi.org/10.5067/ECOSTRESS/ECO_L2T_LSTE.003), [JET v003](https://doi.org/10.5067/ECOSTRESS/ECO_L3T_JET.003), ESI v003 | 70 m; sesuai lintasan, tidak menjamin data harian | Metadata LST, ET dan ESI ditemukan untuk tile 49MDM; nilai piksel dan mask belum diuji. |
| Elevasi dan lereng | [NASADEM_HGT.001](https://doi.org/10.5067/MEASURES/NASADEM/NASADEM_HGT.001) | Sekitar 30 m; elevasi dasar statis | Tile s08e110 ditemukan dalam metadata. ZIP ilmiah belum diunduh; lereng merupakan hasil perhitungan dari elevasi. |
| Tren simpanan air wilayah luas | [GRACE/GRACE-FO CRI RL06.3Mv04](https://podaac.jpl.nasa.gov/dataset/TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.3_V4) | Bulanan; grid keluaran 0,5°, informasi mascon independen sekitar 3° | Metadata seri sampai Agustus 2026 ditemukan. Hanya cocok sebagai konteks regional, terlalu kasar untuk satu sawah. |
| pH, tekstur, karbon organik, total N, CEC | [ISRIC SoilGrids](https://docs.isric.org/globaldata/soilgrids/) | Native 250 m, enam lapisan kedalaman | **Potongan raster pH berhasil diunduh melalui WCS**. Sifat lain tersedia menurut katalog, belum diunduh dalam audit ini. |
| Syarat tumbuh tanaman | [FAO ECOCROP](https://www.fao.org/geospatial/data-and-tools/data-portals/ecocrop/) | Referensi tingkat spesies, bukan piksel | Profil padi, jagung, kedelai berhasil dibaca dan angka rujukan disimpan. Perlu penyesuaian varietas lokal. |
| Kalender/pola tanam Indonesia | [Kementan SIAP TANAM](https://brmp.pertanian.go.id/index.php/layanan/layanan-elektronik/siap-tanam) | Konteks nasional hingga kecamatan | Sumber resmi ditemukan; API publik untuk integrasi otomatis belum terkonfirmasi. |
| Rotasi berjalan dan prioritas petani | Input petani/penyuluh | Lahan individual | Belum tersedia. Harus dikumpulkan dari pengguna. |

## Bukti unduhan nyata

### NASA POWER

- Koordinat: lintang −7,8; bujur 110,37. Periode: 1 Januari 2021–31 Desember 2025, Local Solar Time.
- Respons HTTP 200, **362.850 byte**, sekitar **363 KB** tanpa kompresi.
- **1.826 hari × 12 parameter = 21.912 nilai**. Tidak ditemukan nilai kosong atau sentinel −999 pada sampel ini. Ini menunjukkan kelengkapan respons contoh, bukan jaminan akurasi pengukuran atau kelengkapan setiap lokasi lain.
- Parameter: T2M, T2M_MAX, T2M_MIN, PRECTOTCORR, RH2M, WS2M, ALLSKY_SFC_SW_DWN, GWETTOP, GWETROOT, EVPTRNS, PS, T2MDEW.
- GWETTOP/GWETROOT adalah indikator kebasahan tanah dari model; jangan disamakan dengan pengukuran air tanah petak. Respons EVPTRNS berunit MJ/m²/hari, bukan langsung mm/hari.
- File dalam paket: `power-yogyakarta-2021-2025.json`; ringkasan per parameter: `power-coverage.csv`.

[Permintaan yang diuji](https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M,ALLSKY_SFC_SW_DWN,GWETTOP,GWETROOT,EVPTRNS,PS,T2MDEW&community=AG&longitude=110.37&latitude=-7.8&start=20210101&end=20251231&format=JSON&time-standard=LST). [Penjelasan resolusi dan model NASA](https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/).

### MODIS

Dua respons REST masing-masing sekitar 4,2 KB berhasil diunduh untuk satu piksel di koordinat yang sama: dua komposit Januari 2025 dan dua komposit Juli–Agustus 2025. NDVI/EVI memiliki faktor skala 0,0001.

Tiga komposit memiliki `pixel_reliability=3` (cloudy), satu bernilai `1` (marginal). **Sampel ini membuktikan akses, belum memenuhi seleksi kualitas untuk membuat rekomendasi.** Respons subset tidak mencantumkan versi koleksi, sehingga versi subset tidak diklaim identik dengan koleksi 061 yang ditemukan di CMR.

File: `modis-actual-sample.json` dan `modis-actual-dryseason.json`. [Metadata band dan skala resmi](https://modis.ornl.gov/rst/api/v1/MOD13Q1/bands).

### SoilGrids

WCS menghasilkan GeoTIFF **648 byte**, grid 9 × 8 untuk area sekitar Klaten: bujur 110,54–110,56 dan lintang −7,73–−7,71. Ini contoh mean pH kedalaman 0–5 cm. Sumber native 250 m; keluaran contoh direproyeksi ke koordinat geografis.

Ada 68 sel nonzero dengan integer 56–58, setara prediksi pH 5,6–5,8. Empat sel bernilai 0 belum tervalidasi dan dikecualikan dari interpretasi. TIFF tidak menyatakan nodata, sedangkan cuplikan VRT sumber menyatakan −32768; **jangan menyebut nol sebagai nodata terkonfirmasi atau pH tanah 0**. Peta ini hasil prediksi, bukan pemeriksaan laboratorium. SoilGrids berlisensi CC BY 4.0; atribusi: ISRIC SoilGrids.

File: `ph-rural-subset.tif`. [Petunjuk WCS](https://docs.isric.org/globaldata/soilgrids/wcs.html), [unit dan ketidakpastian](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html).

### Referensi tanaman

Angka rujukan spesies disimpan di `crop-reference.csv` dari profil [padi](https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id=1574), [jagung](https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id=2175), dan [kedelai](https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id=1150). Curah hujan referensi adalah hujan tahunan, bukan kebutuhan air satu musim. Rentang umur tanaman dapat sangat luas. ECOCROP merupakan referensi historis yang pengembangannya dihentikan sekitar 2015, sekarang tersedia melalui GAEZ.

## Kendala akses dan kualitas

- SoilGrids mengumumkan REST API dihentikan sementara; percobaan REST mendapat nilai null/timeout. WCS berhasil dalam audit ini, sehingga aplikasi tidak boleh hanya bergantung pada REST tersebut.
- [NASA menjelaskan transisi IMERG V08](https://gpm.nasa.gov/data/news/imerg-v08-transition-schedule). Jangan menganggap Final V07 menyediakan data hingga hari ini atau mencampur Final dan Late tanpa penjelasan perbedaan pemrosesan.
- NSIDC memberikan advisory geolokasi SMAP L4 untuk 14 Mei–28 Juli 2026. Periode itu perlu memperhatikan status pemrosesan ulang.
- Resolusi berbeda perlu diselaraskan. Memperbesar piksel 9 km menjadi 30 m tidak menciptakan informasi lahan baru. Citra optik/termal membutuhkan filter awan dan quality flags.
- Metadata katalog membuktikan keberadaan berkas, belum membuktikan semua piksel valid, unduhan berhasil, atau integrasi aplikasi siap. Paket menyimpan metadata secara terpisah dari sampel numerik.
- [AppEEARS](https://github.com/nasa/AppEEARS-Data-Resources) mendukung ekstraksi titik/area dan memerlukan Earthdata Login. Tidak ada akun yang dibuat atau diubah dalam audit ini.

## Data yang tetap perlu diisi petani

Batas dan luas lahan; tanaman/varietas serta tanggal tanam–panen sebelumnya; sumber dan batas irigasi; drainase; hasil uji tanah bila tersedia; riwayat hama dan pengelolaan; keterbatasan alat, tenaga dan biaya; akses pasar; prioritas hemat air, pendapatan, atau perbaikan tanah. Data harga agregat belum sama dengan harga jual petani.

Membandingkan tiga strategi rotasi adalah **hasil analisis aplikasi**, bukan kolom siap unduh dari NASA. Penjelasan fiksasi nitrogen, perubahan kesehatan tanah, gangguan siklus hama, kebutuhan air dan pendapatan memerlukan aturan/model dengan sumber agronomi dan validasi lokal. [FAO AquaCrop](https://www.fao.org/aquacrop/overview/input-requirements/) juga memerlukan parameter tanaman, profil tanah, iklim, dan pengelolaan.

## Rekomendasi susunan data untuk versi awal

Mulai dari **NASA POWER + MODIS subset (atau HLS setelah akses siap) + SoilGrids WCS + referensi tanaman FAO/Kementan + input petani**. Tambahkan NASADEM untuk lereng. SMAP/GPM/ECOSTRESS memperkuat analisis air setelah ekstraksi nilai dan QA diuji; GRACE menjadi konteks wilayah luas.

Susunan ini cukup sebagai dasar prototipe yang sejalan dengan challenge, tetapi belum membuktikan rekomendasi rotasi siap digunakan pada lahan nyata. Lima tahun contoh berguna untuk menguji alur data dan pola musiman; analisis tren iklim jangka panjang memerlukan baseline lebih panjang. Aplikasi perlu menampilkan sumber, tanggal data, skala, kualitas, serta alasan dan ketidakpastian setiap perbandingan.
