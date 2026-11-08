# Iklim regional Yogyakarta-Klaten

Data NASA POWER harian, titik contoh 110.37,-7.8. `daily.csv` mempertahankan 12 parameter dan unit aslinya. Baseline 1991-2020 dihitung dari data harian. Data 2026 bersifat parsial dan dapat direvisi. Lokasi ini representatif untuk konteks regional, bukan pengukuran pada setiap petak.

`monthly.csv` berisi agregat kalender dan anomali terhadap bulan yang sama pada 1991-2020. Agregat yang tidak memiliki seluruh hari valid dikosongkan. `baseline-1991-2020.csv` berisi mean, median, persentil 10/90 dan jumlah tahun valid per metrik. Tidak ada imputasi.

ETo adalah estimasi referensi rumput FAO56 dengan forcing regional. Ini bukan ET aktual tanaman atau kebutuhan irigasi. P-ETo tidak memperhitungkan limpasan, simpanan air tanah, koefisien tanaman, irigasi atau efisiensinya. Penjagaan Rs/Rso 0.3-1 adalah asumsi operasional tambahan dan ditandai pada QA harian. Lihat method-validation.json untuk pemeriksaan terhadap contoh terbitan FAO, serta manifest.json untuk metode dan sumber.

EVPTRNS tetap MJ/m²/hari. GWETROOT/GWETTOP adalah kebasahan tanah model, bukan kadar air volumetrik yang diukur pada petak. Resolusi meteorologi sekitar puluhan km. Data LST mengikuti waktu matahari, bukan definisi zona waktu WIB.

Reproduksi dari root proyek: `py -3.11 scripts/data/prepare_climate.py`. Raw respons disimpan dan digunakan kembali. Periode 2021-2025 berasal dari sampel audit awal, dengan hash yang tercatat. Tidak ada aplikasi atau rekomendasi rotasi dibuat oleh skrip ini.
