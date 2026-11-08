# FieldShift - konteks proyek

Lokasi kerja yang dipilih: D:\Codex\FieldShift
Tanggal: 8 November 2026 (Asia/Jakarta)

## Status roadmap terbaru: tahap 3 backend MVP selesai

Pengguna menginstruksikan **"baik lanjut ke tahap be."** Tahap 3 diimplementasikan di `backend/fieldshift/` dengan Python 3.11/FastAPI. API stateless membaca paket lokal, memverifikasi manifest prepared 390 entri + supplemental 526 entri, dan tidak menyimpan input lahan. Enam layer konteks, tiga slot strategi netral dan seluruh 12 pemeriksaan tersedia. Panduan menjalankan/API: `backend/README.md`; dependency diuji terkunci di `backend/requirements-lock.txt`. Jalankan dari root: `.venv/Scripts/python.exe -m uvicorn backend.fieldshift.app:app --host 127.0.0.1 --port 8000`.

Verifikasi terbaru: `outputs/backend-verification.json`, direproduksi dengan `.venv/Scripts/python.exe scripts/verify_backend.py`: 55 tes metode + 79 tes backend dan 5 pemeriksaan HTTP sungguhan lulus. Server uji telah dihentikan. Request/hasil demo historis 2025 di `outputs/backend-demo-request.json`/`backend-demo-response.json`, kontrak HTTP di `outputs/backend-openapi.json`. Data prepared/supplemental tidak diubah.

Backend menggunakan native SoilGrids pada koordinat aktual (primary pH mean5,8/Q05 4,2/Q95 7,9); tidak memakai indeks WCS lama. Terra/Aqua tetap terpisah. Dokumen parsial memakai vocabulary119field, unknown tetap null/missing; asal durasi/konversi, kalender terkunci, panen dilaporkan, lokasi dan duplikasi input diperiksa. Kalender dari baseline tidak disalin ke tanaman berbeda tanpa `slot_inputs` eksplisit. Prioritas hanya highlight; semua ranking/yield/irigasi/profit/manfaat tetap null, local_agronomic_validation=false. Poligon belum didukung dan non-null ditolak; analisis memakai titik. Referensi context yang dikirim tidak menggantikan data repository. Tidak ada scraper otomatis atau deployment.

**Tahap berikutnya: tahap 4 antarmuka**, belum dimulai. Bagian di bawah mempertahankan riwayat tahap data/metode; pernyataan lama bahwa backend belum ada merujuk keadaan sebelum pembaruan ini. Jangan meminta ulang area contoh/online/izin backend atau mengubah contoh menjadi observasi petani.

Sebelum implementasi frontend, pengguna meminta `design.md` dan deskripsi proyek untuk dimasukkan ke Stitch. Brief ada di root `design.md`; prompt awal dan deskripsi singkat di `docs/stitch-project-description.md`. Arahan terbaru pengguna menggabungkan produk dan aplikasi menjadi landing page responsif dengan 3D, tanpa AI slop/typografi dekoratif. Prompt revisi utama di `docs/stitch-revision-landing-3d.md` mengesampingkan komposisi/sidebar/font awal: hero split dengan diorama rotasi ilustratif, satu font Libre Franklin, area kondisi/form/perbandingan lebar penuh dalam satu halaman, fallback mobile/reduced motion. Batas data, sumber/status dan asumsi backend tetap berlaku. Ini bahan prompt untuk Stitch; desain Stitch belum diperiksa langsung, belum ada kode frontend atau pengujian visual. Data/API tidak diubah.

Revisi desain berikutnya: pengguna menyukai struktur landing page, tetapi shading/color grading masih dinilai AI slop dan meminta penggunaan skill. Prompt terbaru ada di `docs/stitch-revision-material-color.md`: pertahankan layout dan Libre Franklin; perketat daylight satu arah, bayangan kontak, material matte tanah/daun berbeda, grade netral pada render saja, UI netral dengan palet baru. Arahan menggunakan design-taste-frontend/ui-ux-pro-max dan review material independen. Belum ada screenshot Stitch yang tersedia/diinspeksi; hasil visual belum diklaim lulus. Ini tetap pekerjaan prompt, tanpa mengubah frontend atau backend.

Pengguna menginstruksikan "oke kita lanjut sesuai roadmapnya. dimulai satu satu." Ini mengizinkan kelanjutan pekerjaan sesuai roadmap; jangan meminta ulang izin yang sudah diberikan untuk langkah yang termasuk cakupan tersebut. Pengguna juga mengonfirmasi **online untuk versi pertama**. Publikasi belum diminta.

Tahap 1 menghasilkan `docs/mvp.md` dan `docs/roadmap.md`: web responsif online, keputusan kerja bahasa Indonesia, area contoh Yogyakarta–Klaten, padi/jagung/kedelai, alur peta-kondisi → profil/skenario → perbandingan tiga strategi. Angka di luar cakupan tetap unavailable, tidak ada prioritas/skor/profit rekaan, dan data petani/asumsi sesi terpisah dari raw.

Pengguna kemudian menginstruksikan **"lanjut tahap 2."** Tahap 2 menghasilkan `docs/rotation-method.md`, `specs/rotation-method-v1.json` (versi 0.1.0, 12 aturan), fixture berlabel di `specs/fixtures/rotation-demo.json` dan modul referensi di `scripts/method/`. Contoh historis 2025 membandingkan padi–padi, padi–jagung dan padi–kedelai: seluruh kalender/produksi/urutan adalah asumsi sintetis eksplisit, lingkungan tetap data nyata, berkas input petani asli tetap kosong. Hasil ada di `outputs/rotation-method-demo.md`/`.json`; status semua strategi `partial`, validasi agronomi lokal false, semua skor/ranking/hasil/irigasi/kredit N/profit tetap null.

Kebijakan penting: horizon setengah terbuka; asal durasi hari ke-0, hari panen masih mengokupansi petak, release pada hari berikutnya; tidak menambah nursery dua kali; rentang durasi dipertahankan; tanaman terkunci sebelum horizon perlu pemeriksaan irisan okupansi. Total P/ETo/P−ETo seluruh horizon sama untuk semua strategi, termasuk jeda; perbedaan jendela tanaman bukan penghematan air. Total parsial tetap null per metrik. Analog 1991–2020 memakai pemetaan bulan/tanggal dan durasi sama: 365 hari memiliki 22 tahun cocok, 366 hari 8; selisih antarjendela wajib memakai kohort berpasangan yang sama. Tanam langsung tidak menetapkan rezim air padi. SoilGrids menggunakan sel yang memuat koordinat dan kedalaman eksplisit, bukan nearest-point fallback.

Pengujian dan review independen memeriksa contoh numerik, kasus gagal/parsial, sumber dan seluruh 390 hash berkas prepared. Reproduksi: `py -3.11 scripts/method/verify_rotation_method.py`; hasil terbaru di `outputs/rotation-method-verification.json`. Modul latihan adalah referensi fixture dan belum evaluator agronomi umum/backend. Aplikasi belum diimplementasikan. Tahap berikutnya adalah **tahap 3 mesin data/backend**, sesuai `docs/mvp.md` dan metode versi 0.1.0; belum mulai antarmuka atau publikasi.

## Audit tambahan yang diminta sebelum backend

Pengguna meminta: **"sebelum masuk ke be, pastikan data data yg diperlukan tidak ada yg kosong/kurang. jikalau ada silahkan lengkapi terlebih dahulu untuk keperluan mendatang."** Saat ditanya tentang observasi petani, pengguna menjawab: **"belum ada datanya. gunakan sumber yang tersedia saja lalu ambil datanya."** Sumber publik boleh dilengkapi; jangan meminta ulang data petani atau mengarang data petak.

Rujukan kesiapan terbaru adalah `outputs/audit-kelengkapan-data-fieldshift.md` dan `data/supplemental/readiness-audit.json`. Snapshot awal `data/prepared/` beserta manifest 390 entri tetap identik; tambahan tidak menimpa nilai awal. Paket lengkap baru `outputs/fieldshift-data-publik-v2-2026-11-08.zip` mempunyai checksum/CRC di `outputs/data-package-verification.json` dan `.zip.sha256`. Audit offline: `py -3.11 scripts/data/audit_data_completeness.py`.

- `data/supplemental/environment/`: 304 komposit tambahan (38 Terra 2026 + 266 Aqua 2021–2026), 69 strict-good/53 marginal/182 excluded; sensor, produk, QA dan footprint tetap terpisah. Diagnostik ketersediaan 2021–2025: primary 31→34/60 bulan, pembanding 32→35/60 bulan; gap 26/25 bulan tetap ada tanpa interpolasi. POWER 14 hari terakhir diminta ulang dan tidak ada revisi/tambahan: hujan 5 Nov, radiasi/ETo 2 Nov 2026 tetap batas valid. 38 sumber/hash diverifikasi.
- `data/supplemental/soil-terrain/`: seluruh 180 raster native 250 m, 12 sifat × 5 kedalaman × 3 statistik, diperoleh dengan ekstraksi terbatas. Seluruh 11.900 positif lama cocok. Dari 1.056 nol, 340 merupakan nol kuantil cfvo Q05 valid dan 716 nodata sumber; 4 sentinel negatif juga nodata, 0 unresolved. Setiap anchor primary/pembanding memiliki 180/180 nilai (termasuk 5 nol prediksi valid). Gunakan grid/mask/CRS native dan provenance baru, jangan patch diam-diam ke WCS lama. Retensi sumber pre-release dilabeli; nodata area lain tetap null.
- `data/supplemental/agronomy/`: kontrak bertipe/satuan 119 field (91 awal + 28 tambahan), JSON Schema Draft 2020-12, semua 12 input aturan dipetakan, 19 pemeriksaan batas positif/negatif lulus. Kontrak ini memperjelas dictionary awal generik; lintang negatif valid dan 3 legacy priority weights tetap unused. Seluruh 119 nilai aktual tetap null. Katalog resmi Anjasmoro PDF page 87/printed 64, Lampiran 27: 82–93 hari setelah tanam; alternatif PVT 82,5–92,5/LAKIN HST dipertahankan, bukan default petani. 5 snapshot baru + 11 reused = 16 source hash verified. Validator jsonschema 4.26.0 lokal ada di `work/validation-deps`, tidak dimasukkan ke ZIP dan bukan dependency backend.
- `data/supplemental/crop-water/`: FAO56 Tabel 12/22 untuk Kc/tinggi referensi/akar maksimum/deplesi. Kc awal jagung/kedelai berasal dari baris kelompok; p padi pada Tabel 22 adalah 0,20 dari saturation, bukan p upland. Belum mengaktifkan ETc/irigasi/persen hemat lokal.
- `data/supplemental/regional-context/`: 18 prakiraan cuaca 3 jam BMKG, kelurahan Klaten 33.10.25.1003 sebagai anchor administratif eksplisit, bukan piksel petak. Issue/valid times dan UTC/WIB/unit diverifikasi. Snapshot berlaku terakhir 10 Nov 2026 pukul 21 WIB; refetch sebelum operasional. `tp` raw tidak diolah (unit/akumulasi belum terverifikasi), visibility null. Bukan forecast musim dan tidak digabung NASA history.

Kesiapan publik inti untuk contoh MVP terpenuhi, **bukan semua data untuk seluruh fitur masa depan atau lahan nyata sudah lengkap**. Actual boundary/history/cultivar/water/lab/pests/economics tetap memerlukan observasi; validasi lokal belum ada. Forecast musim dan misi opsional NASA masih deferred, tidak wajib MVP. Gunakan `use_policy` pada audit baru saat membangun backend. Jangan melakukan silent nearest fallback, imputasi QA atau mengubah model menjadi observasi.

Temuan dukungan pH: primary actual coordinate pada grid native mempunyai mean 5,8/Q05 4,2/Q95 7,9. Pusat sel WCS lama pada row 4/col 6 mempunyai mean 5,8/Q05 4,2/Q95 7,8. Seluruh 11.900 nilai positif cocok saat dibandingkan pada koordinat pusat lama, bukan menyamakan koordinat anchor dengan pusat lama. Fixture tahap 2 tetap memakai snapshot prepared lama; implementasi baru harus memilih native dengan mask/CRS yang benar, tanpa menyalin indeks antar-grid atau mengganti sumber diam-diam.

Pengguna menanyakan waktu dan skala dataset NASA: jelaskan cakupan luas/global berbasis grid/piksel, ekstraksi titik/area bukan data bawaan per kota, serta frekuensi/jeda berbeda antarproduk. Online tidak berarti observasi real-time. POWER harian dan MODIS komposit 16 hari adalah contoh; dataset kita berupa subset dan riwayat, bukan seluruh dunia atau data live setiap petak.

## Pembaruan terakhir: fondasi data publik telah dilengkapi

Pengguna meminta: "lengkapi data yg diperlukan dulu. baru kita mulai eksekusi." Pengguna kemudian mengonfirmasi **Yogyakarta–Klaten sebagai area contoh**. Tahap penyiapan data publik inti sudah selesai; aplikasi belum dibuat. Tanaman referensi tetap padi, jagung, kedelai. Jangan menyamakan persiapan data dengan rekomendasi lahan yang sudah tervalidasi.

Hasil terbaru yang menjadi rujukan utama:

- `outputs/kesiapan-data-fieldshift.md`: laporan kesiapan dan gap yang tersisa.
- `outputs/fieldshift-data-publik-2026-11-08.zip`: paket portabel data mentah/terolah, sumber, QA dan skrip (tanpa dependency vendor).
- `data/prepared/README.md`, `analysis-profile.json`, `readiness.json`, `locations.geojson`, `file-manifest.json`, `validation-report.json`: katalog, cakupan, geometri contoh, hash dan hasil pemeriksaan.
- `data/prepared/climate/`: NASA POWER 1991–2025 dan 2026 parsial, 13.095 tanggal × 12 parameter. Baseline 1991–2020 lengkap 10.958 hari/360 bulan. Meteorologi terakhir valid 5 November 2026; radiasi/ETo 2 November. Akhir permintaan 7 November bukan tanggal valid semua parameter. ETo referensi FAO56 telah dicek dengan contoh numerik FAO; P−ETo bukan kebutuhan irigasi. EVPTRNS tetap fluks energi MJ/m²/hari. Satu titik POWER menjadi konteks regional puluhan km, bukan cuaca tiap petak.
- `data/prepared/vegetation/`: 230 komposit MODIS 2021–2025, dua piksel rural Klaten; primary 42 good/21 marginal/52 excluded dan good pada 31/60 bulan, pembanding 42/22/51 dan good pada 32/60 bulan. Bulan kosong tidak diinterpolasi; tidak boleh dipakai otomatis menyimpulkan tanggal tanam/panen atau masa lahan kosong. Versi koleksi tidak disebut oleh respons subset ORNL.
- `data/prepared/soil-terrain/`: 180 raster SoilGrids (12 sifat, 5 kedalaman sampai 1 m, mean/q05/q95), 11.900 sel interpretabel, 1.056 nol ambigu tetap dikecualikan dan empat sentinel negatif. Termasuk retensi air; jangan langsung mengubahnya menjadi kebutuhan irigasi tanpa konteks tanah/pengelolaan. Elevasi/lereng memakai **Copernicus DEM GLO-30 DSM**, bukan NASADEM. WorldCover2021 dan footprint MODIS asli juga tersedia.
- `data/prepared/agronomy/`: 3 profil tanaman, 9 aturan agronomi bersyarat, contoh varietas Indonesia, 12 nilai kategori GAEZ v5 yang benar-benar diekstrak (dua titik × tiga tanaman × dua rezim). Baseline GAEZ HP0120/AGERA5/HIST = 2001–2020, grid 5 arc-minute. Kategori memakai legend resmi; bukan skor 0–100 atau rekomendasi petak. Template 91 input petani dan tiga slot strategi seluruh nilai farm/hasilnya tetap kosong.
- `scripts/data/`: skrip persiapan, QA independen dan pengemasan; belum ada kode aplikasi. Periksa README per modul untuk dependensi/reproduksi. Folder lokal `scripts/data/soil-terrain/_vendor` tidak dimasukkan ZIP.

Temuan lokasi penting: titik lama Yogyakarta (-7.8,110.37) adalah built-up pada WorldCover2021; titik Klaten lama (-7.72,110.55) tree cover/campuran. Keduanya bukan sawah terverifikasi. Titik POWER tetap dipakai sebagai anchor regional. Vegetasi memakai dua piksel baru yang lokasi akhirnya dibekukan:

- Primary: lat -7.721875031299882, lon 110.55354472008753; sekitar 84,469% cropland, tanpa built-up dalam footprint MODIS aktual.
- Pembanding (`klaten_cropland_candidate`): lat -7.7240416666666665, lon 110.546875; sekitar 69,206% cropland dalam footprint aktual.

Presisi koordinat berasal dari perhitungan grid, bukan pengukuran GPS lahan. Keduanya tetap mixed pixel, tutupan lahan historis 2021 dan jenis tanaman tidak diketahui.

Pemeriksaan gabungan lulus: JSON finite, jumlah/grid data, tanggal unik, baseline, agregat bulanan, skala dan packed QA MODIS, null input petani; modul juga memverifikasi sumber/hash. Belum ada ground truth/validasi agronomi lokal. Data yang tetap diperlukan untuk analisis lahan nyata: batas/luas, rotasi dan tanggal, varietas, irigasi/drainase, pengelolaan, prioritas; harga/biaya/hasil diperlukan sebelum perbandingan ekonomi. Forecast musim belum diambil. HLS/SMAP/GPM/ECOSTRESS/NASADEM/GRACE masih metadata-only dari audit awal, status ada di `optional-sources.json`; semua misi tidak wajib dipakai sekaligus.

Bagian berikut mempertahankan riwayat riset dan perpindahan folder sebelum pengayaan data ini.

## Permintaan pengguna dan status

Pengguna ingin aplikasi/peta interaktif untuk challenge NASA Space Apps 2026, Field Shift: Adapting Farms with NASA Data.
Sumber challenge: https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/

Riwayat otorisasi: pada fase awal pengguna meminta konfirmasi sebelum pembuatan aplikasi, dan perpindahan ke D: bukan persetujuan implementasi. Instruksi terbaru untuk melanjutkan roadmap satu per satu kini menjadi acuan (lihat status roadmap di atas). Publikasi belum diminta.

Pengguna kemudian meminta memakai drive D: atau Codex CLI. Hasil riset disalin dari folder chat di Documents/Codex ke folder ini; 66 file telah diverifikasi SHA-256. Sumber C: masih tersedia sebagai cadangan. Jangan menghapusnya tanpa instruksi pengguna.

## Hasil riset

- outputs/audit-data-field-shift.md: laporan audit kebutuhan challenge dan sumber data.
- outputs/contoh-data-field-shift-2026-11-08.zip: contoh data numerik, metadata, dan sumber.
- work/data-audit/power-yogyakarta-2021-2025.json: 12 variabel NASA POWER, 1826 hari, 362850 byte, tanpa nilai kosong/-999 pada contoh.
- work/vegetation-terrain/: sampel MODIS dan metadata HLS/NASADEM. Beberapa sampel MODIS cloudy/marginal, belum layak menjadi dasar rekomendasi.
- work/soil-crop/: contoh SoilGrids pH dan referensi FAO untuk padi/jagung/kedelai. Empat sel pH bernilai nol belum tervalidasi, jangan diartikan sebagai pH 0 atau nodata terkonfirmasi.
- work/water-thermal/: metadata SMAP/GPM/ECOSTRESS/GRACE dan audit akses/kualitas.
- work/platform-audit/: katalog AppEEARS.
- work/agriculture-db/: metadata GAEZ, bila tersedia.

Usulan fondasi data: FAO GAEZ v5 untuk agronomi + observasi NASA melalui Earth Engine/AppEEARS/POWER + input petani. Ini masih usulan, bukan keputusan implementasi final. GAEZ baseline/model bukan kondisi live tiap petak. GEE memerlukan proyek, registrasi, dan aturan kuota. Jangan menjanjikan semua API/integrasi sudah diuji.

Kebutuhan input petani: batas/luas lahan, rotasi saat ini, tanggal tanam/panen, varietas, irigasi, riwayat hama/pengelolaan, akses pasar, biaya, dan prioritas. Perbandingan rotasi perlu logika agronomi dan validasi lokal; bukan label siap pakai dari NASA.

Perkiraan desain untuk riwayat lima tahun: 1-5 MB data ringkas per lahan; 100-500 MB untuk 100 lahan; tambahan raster bulanan beberapa layer pada wilayah 10x10 km sekitar 50-200 MB. Ini estimasi, belum ukuran aplikasi yang sudah dibangun. Gambar peta dasar dan kode belum termasuk.

## Langkah berikutnya

Lanjutkan tahap 3 berdasarkan `docs/mvp.md`, `docs/rotation-method.md` dan `docs/roadmap.md` bila pekerjaan dilanjutkan. Wilayah contoh dan penggunaan online telah dikonfirmasi; tanaman mengikuti referensi yang sudah disiapkan. MVP memakai data publik yang tersedia tanpa memerlukan akun data tambahan. Jangan meminta ulang keputusan yang telah diberikan, mengunduh arsip global, atau menjalankan proyek lain secara otomatis.
