# Audit data air dan termal untuk Field Shift

Dicek 8 November 2026. Riset metadata dan dokumentasi saja; tidak mengunduh berkas ilmiah penuh dan belum menguji nilai/quality mask piksel lahan.

Area uji CMR: bbox 110.2,-7.95,110.5,-7.65, sekitar Yogyakarta. Metadata yang beririsan dengan bbox tidak menjamin setiap piksel lahan memiliki retrieval valid.

| Kebutuhan | Produk terverifikasi | Ruang/waktu | Hasil discovery aktual |
|---|---|---|---|
| Kelembapan permukaan tanah | SPL3SMP_E v006 | Grid 9 km, komposit harian, sejak 31 Maret 2015; resolusi efektif radiometer tetap puluhan km | Granule 6 November 2026, `SMAP_L3_SM_P_E_20261106_R19240_001.h5`; ukuran metadata global 641.77 MB |
| Kelembapan zona akar | SPL4SMGP v008 | Grid model 9 km, rata-rata 3 jam, sejak 31 Maret 2015; asimilasi radiometer ke model, bukan pengukuran akar langsung | Granule 5 November 2026 21:00–6 November 00:00 UTC; ukuran global 142.92 MB |
| Curah hujan historis | GPM_3IMERGDF v07 Final | 0.1 derajat (~11 km di ekuator), harian; CMR mencatat 1998-01-01–2025-09-30 | Granule 30 September 2025, 30.97 MB global |
| Curah hujan terbaru | GPM_3IMERGDL v07 Late | 0.1 derajat, harian (tersedia juga setengah jam); Early/Late lanjut saat transisi algoritme | Granule 6 November 2026, V07C, 25.79 MB global |
| Suhu permukaan | ECO_L2T_LSTE v003 | 70 m, observasi sesaat saat lintasan ISS, sejak 2018; tidak menjamin harian/cerah | Tile 49MDM beririsan bbox pada 2 November 2026; metadata set layer 40.16 MB |
| Evapotranspirasi | ECO_L3T_JET v003 | 70 m, instantaneous/daytime estimates; model ET dari penginderaan termal dan forcing tambahan | Tile 49MDM pada 12 Oktober 2026; metadata set layer 83.23 MB |
| Indeks stres evaporatif | ECO_L4T_ESI v003 | 70 m, instantaneous model product | Tile 49MDM pada 12 Oktober 2026; metadata set layer 13.5 MB |
| Tren simpanan air regional | TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.3_V4 | Bulanan sejak 2002; output grid 0.5 derajat, informasi mascon independen ~3 derajat | Satu file seluruh seri April 2002–Agustus 2026; metadata 44.01 MB |

## Keterbatasan yang harus dibawa ke aplikasi

- SMAP: grid 9 km tidak memberi observasi independen tiap petak kecil. L3 kondisi permukaan; L4 rootzone adalah hasil model + asimilasi. Quality flags, air terbuka dan vegetasi perlu diperiksa.
- NSIDC memperingatkan masalah geolokasi SMAP 14 Mei–28 Juli 2026; produk L4 periode itu sedang direproses. Jangan menganggap semua data 2026 sudah bersih.
- GPM: NASA menyatakan Final V07 berhenti September 2025 selama transisi V08. CMR saat dicek masih menunjukkan v07 untuk short name Final. Early/Late mutakhir beroperasi hybrid sehingga dapat memiliki diskontinuitas. Jangan mencampur deret itu tanpa penjelasan.
- ECOSTRESS: metadata lintasan bukan jaminan data bebas awan. Panduan v3 menyatakan retrieval tidak valid bernilai NaN dan menyediakan cloud/water mask. Suhu permukaan bukan suhu udara. ET dan ESI turunan model, bukan sensor ukur air setiap petak.
- GRACE: anomali total simpanan air pada wilayah besar. Tidak dapat dipakai sebagai pengukuran kedalaman sumur/air irigasi satu sawah; grid 0.5 derajat tidak mengubah skala informasi dasar 3 derajat.
- Semua seri merupakan observasi historis/estimasi historis, bukan prakiraan musim atau rekomendasi rotasi yang sudah tervalidasi.

## Akses

CMR metadata publik berhasil diakses tanpa login. File metadata JSON disimpan bersama laporan ini. Distribusi ilmiah cloud umumnya memakai Earthdata Login; NSIDC dan PO.DAAC mendokumentasikannya. Untuk ECOSTRESS, uji HEAD satu URL layer berhasil HTTP 200 lewat pengalihan proxy lingkungan ini, tetapi tidak mengunduh raster atau menguji sesi login produksi. Jangan menyimpulkan dari HEAD ini bahwa seluruh aplikasi publik bebas autentikasi.

NSIDC mendokumentasikan spatial/parameter/shapefile subsetting untuk SPL3SMP_E dan SPL4SMGP lewat Earthdata Search. ECOSTRESS tersedia per layer COG agar bisa membaca subset/range yang diperlukan. GRACE menyediakan subset/OPeNDAP. Layanan subset belum dijalankan karena memerlukan alur/akun yang sesuai.

## Sumber primer

- SMAP L3: https://nsidc.org/data/spl3smp_e/versions/6
- SMAP L4 (termasuk advisory geolokasi): https://nsidc.org/data/spl4smgp/versions/8
- SMAP subsetting: https://nsidc.org/data/user-resources/help-center/what-data-subsetting-reformatting-and-reprojection-services-are-available-smap-data
- GPM IMERG: https://gpm.nasa.gov/data/imerg
- Transisi IMERG: https://gpm.nasa.gov/data/news/imerg-v08-transition-schedule
- ECOSTRESS LST v3: https://doi.org/10.5067/ECOSTRESS/ECO_L2T_LSTE.003
- ECOSTRESS JET v3: https://doi.org/10.5067/ECOSTRESS/ECO_L3T_JET.003
- Panduan v3 tim JPL: https://github.com/ECOSTRESS-Collection-3/ECOv003-L3T-L4T-JET/blob/main/documentation/ECOv003_L3_L4_JET_User_Guide.md
- GRACE CRI: https://podaac.jpl.nasa.gov/dataset/TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.3_V4
- Contoh probe CMR SMAP: https://cmr.earthdata.nasa.gov/search/granules.json?collection_concept_id=C2938664763-NSIDC_CPRD&bounding_box=110.2,-7.95,110.5,-7.65&temporal=2025-01-01T00%3A00%3A00Z,2026-11-08T00%3A00%3A00Z&page_size=1&sort_key=-start_date

