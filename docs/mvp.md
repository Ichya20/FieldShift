# FieldShift — spesifikasi MVP

Versi 1.0 · 8 November 2026 · Tahap 1 roadmap.

## Tujuan produk

FieldShift membantu petani dan penyuluh mengeksplorasi rotasi tanaman dengan menghubungkan kondisi lingkungan historis, karakteristik tanaman, informasi lahan dan prioritas petani. Keluaran utamanya adalah perbandingan rotasi yang sedang digunakan dengan dua skenario alternatif, beserta alasan, kendala dan informasi yang masih dibutuhkan.

Pertanyaan utama yang ingin dijawab: **“Apa yang perlu saya pertimbangkan bila mengubah rotasi tanaman pada lokasi ini?”**

Data NASA harus digunakan dalam analisis dan penjelasan hasil. POWER menyediakan konteks iklim dan indikator air; MODIS menyediakan riwayat vegetasi beserta kualitasnya. Data tanah, agronomi, topografi dan tutupan lahan memperkaya konteks dengan atribusi sumber masing-masing.

## Keputusan cakupan

| Aspek | Keputusan | Dasar |
|---|---|---|
| Platform | Web responsif, online, dapat dibuka dari HP/laptop | Dikonfirmasi pengguna pada tahap ini |
| Bahasa awal | Bahasa Indonesia, istilah teknis dijelaskan singkat | Keputusan kerja berdasarkan pengguna dan area contoh |
| Pengguna | Petani dengan atau tanpa pendampingan penyuluh | Arah challenge dan kompleksitas informasi agronomi |
| Wilayah demonstrasi | Yogyakarta–Klaten | Dikonfirmasi pengguna pada tahap pengumpulan data |
| Tanaman versi pertama | Padi, jagung, kedelai | Referensi dan data yang sudah disiapkan |
| Unit perbandingan | Satu lokasi, satu cakrawala perencanaan, tiga strategi | Agar bukti dan kendala dapat dibandingkan secara setara |
| Bentuk hasil | Perbandingan bukti, kalender jika input cukup, kendala dan kebutuhan informasi | Metode peringkat dan rekomendasi lahan belum terkalibrasi |
| Akun dan penyimpanan | Tanpa akun untuk MVP; isian digunakan selama sesi, penyimpanan permanen belum menjadi fitur | Keputusan kerja untuk memusatkan implementasi pada alur analisis |

Pilihan online sudah dipastikan. Bahasa, bentuk sesi dan detail interaksi di atas merupakan keputusan kerja yang dapat disesuaikan selama implementasi, tanpa mengubah tujuan MVP.

## Cakupan geografis sebenarnya

Nama wilayah demonstrasi tidak berarti semua petak Yogyakarta–Klaten sudah memiliki data terolah.

| Layer | Cakupan yang tersedia | Penggunaan dalam MVP |
|---|---|---|
| NASA POWER | Satu titik representatif regional; meteorologi puluhan km; 1991–2025 dan 2026 parsial | Konteks iklim historis. Dukungan spasial sumber tetap terlihat. |
| MODIS | Dua piksel rural Klaten; 115 komposit per piksel pada 2021–2025 | Riwayat vegetasi pada piksel terpilih. Tidak otomatis diperluas ke lokasi pengguna. |
| SoilGrids dan terrain | Subset bujur 110,54–110,56; lintang −7,73–−7,71, sekitar 2 × 2 km | Konteks tanah/permukaan pada sel yang tersedia dan lolos pemeriksaan. |
| GAEZ | Dua titik audit, padi/jagung/kedelai dan dua rezim; model 2001–2020 | Konteks kategori pada sel yang benar-benar diekstrak. |
| WorldCover | Subset dan footprint historis 2021 | Menjelaskan alasan pemilihan sampel dan campuran tutupan lahan. |

Piksel vegetasi utama berada pada sekitar −7,721875; 110,553545, dengan 84,469% cropland menurut WorldCover 2021 pada footprint MODIS. Pembanding sekitar −7,724042; 110,546875, dengan 69,206% cropland. Koordinat berasal dari grid; keduanya bukan lahan petani yang terverifikasi.

Lokasi baru diperiksa per layer. Jika data belum diekstrak, berada di luar cakupan, atau tidak valid, bagian tersebut menampilkan **“Data belum tersedia untuk lokasi ini”**. Aplikasi dapat menawarkan kembali ke contoh demonstrasi secara eksplisit. Data lokasi terdekat tidak boleh diam-diam menggantikan data lahan pengguna.

Dataset NASA yang digunakan memiliki cakupan luas/global dalam grid atau piksel dan periode pengamatan, bukan satu dataset seragam per kota. Titik, batas lahan atau batas kota menjadi area pemilihan/agregasi oleh aplikasi. Satu piksel dapat mencakup beberapa petak dan tidak membuktikan kondisi masing-masing petak.

Web online berarti aplikasi diakses dengan koneksi internet. Versi ini memakai riwayat data yang sudah disiapkan, dengan tanggal observasi dan batas periode yang terlihat; tidak menjanjikan streaming kondisi lahan. POWER harian dan MODIS komposit 16 hari mempunyai jadwal serta jeda pemrosesan berbeda. Waktu akses/unduh tidak boleh dilabeli sebagai waktu observasi terbaru.

## Dua cara menggunakan MVP

**Lihat contoh lokasi.** Pengunjung langsung dapat memilih contoh Klaten dan membaca kondisi historis, kualitas data serta referensi tanaman. Tidak perlu membuat akun atau mengisi profil petani. Semua informasi tetap berlabel lokasi demonstrasi.

**Bandingkan skenario.** Pengguna menambahkan informasi lahan dan rencana tanam. Perbandingan memakai informasi yang tersedia; bagian yang kekurangan input menyebutkan apa yang perlu dilengkapi. Urutan tanaman yang dicoba adalah skenario pengguna atau usulan eksplorasi, bukan riwayat lahan yang telah dibuktikan.

Riwayat rotasi, pilihan varietas, prioritas dan batas lahan tidak diisi otomatis dari contoh. Bila belum ada data petani, demonstrasi analisis dapat memakai asumsi yang dipilih secara eksplisit di sesi dan ditandai sebagai asumsi; berkas sumber petani tetap kosong.

## Input petani dengan pengisian bertahap

Template data lengkap memiliki 91 field untuk berbagai kebutuhan. Formulir awal hanya meminta kelompok informasi yang relevan dengan penilaian yang akan dilakukan.

| Kelompok | Informasi awal | Perilaku jika belum diketahui |
|---|---|---|
| Lokasi | Titik/pilihan contoh; batas dan luas lahan bila tersedia | Titik hanya mendukung konteks lokasi. Luas/polygon yang belum tersedia tidak disimpulkan dari piksel satelit. |
| Rotasi berjalan | Urutan tanaman dan tanggal semai/tanam/panen terakhir; bedakan tanggal aktual dan rencana | Kolom strategi berjalan tampil belum lengkap; aplikasi tidak mengarang riwayat. |
| Rencana | Periode yang ingin dibandingkan dan tanaman yang diizinkan/dihindari | Evaluasi kalender menunggu periode/tanggal yang cukup; pengguna tetap bisa membaca referensi. |
| Air dan drainase | Tadah hujan/irigasi/campuran/belum tahu; waktu ketersediaan air; kendala drainase | Penilaian kendala air/drainase ditandai perlu informasi. Tidak menghitung kebutuhan irigasi petak. |
| Varietas dan pengelolaan | Varietas, metode tanam dan durasi lokal bila diketahui | Contoh varietas tetap menjadi referensi; durasi tersebut tidak dianggap pilihan petani. |
| Prioritas | Pilihan eksplisit, misalnya konservasi air, tanah atau pengelolaan hama; kendala utama | Tidak ada prioritas atau bobot buatan. Urutan strategi tetap netral. |

Uji tanah, riwayat hama, pengelolaan residu dan ketersediaan sumber daya ditanyakan pada penilaian yang membutuhkannya. Harga, biaya dan hasil panen menjadi prasyarat penilaian ekonomi pada pengembangan berikutnya.

Semua nilai belum diketahui disimpan sebagai `null`. Nilai nol yang diketahui, pilihan “tidak ada”, dan jawaban “belum tahu” memiliki makna berbeda. Tanggal semai dan pindah tanam dibedakan; curah hujan tahunan, ET musiman dan kebutuhan irigasi tidak disamakan.

## Keluaran utama

### Profil kondisi lokasi

Ringkasan musim historis suhu/hujan, ETo referensi dan indikator P−ETo, prediksi tanah serta elevasi/lereng bila tersedia. Riwayat vegetasi menampilkan gap hasil penyaringan kualitas. Pengguna dapat membuka definisi istilah, sumber, periode dan dukungan ruang setiap indikator.

Baseline 1991–2020, riwayat 2021–2025 dan seri 2026 parsial disajikan sebagai periode berbeda. Iklim historis tidak dilabeli prakiraan musim. ETo referensi dan P−ETo tidak dilabeli sebagai kebutuhan irigasi aktual.

### Tiga strategi pada cakrawala yang sama

| Strategi | Asal dan isi |
|---|---|
| Rotasi berjalan (`existing`) | Kelanjutan rotasi yang sedang digunakan pada cakrawala rencana yang sama dengan alternatif. Riwayat petani menjadi dasar, dengan tanggal aktual dan rencana terpisah; jika tidak diketahui, status belum lengkap. |
| Alternatif 1 (`candidate_1`) | Skenario eksplorasi yang dipilih/disusun berdasarkan tanaman referensi dan input yang tersedia. |
| Alternatif 2 (`candidate_2`) | Skenario kedua dengan perbedaan urutan/komposisi yang bermakna dan asumsi eksplisit. |

Metode pembentukan kandidat dan pemeriksaan agronominya dirancang pada tahap 2. Dua kandidat tidak ditetapkan sebagai urutan universal pada tahap MVP ini. Tiga slot yang kosong belum dihitung sebagai tiga strategi yang telah dianalisis.

Setiap strategi menampilkan:

1. Urutan tanaman dan kalender bila tanggal serta durasi memadai.
2. Bukti lingkungan dan referensi tanaman yang relevan.
3. Kendala musim, air/drainase dan pengelolaan yang dapat diperiksa dari input tersedia.
4. Potensi mekanisme manfaat, syarat terjadinya dan risiko yang memerlukan tinjauan lokal.
5. Data yang kurang serta langkah untuk melengkapinya.
6. Sumber dan asumsi untuk setiap kesimpulan.

Prioritas petani menentukan informasi yang ditonjolkan. Prioritas tidak langsung menghasilkan skor gabungan atau peringkat yang belum terkalibrasi. Kolom hasil memakai status yang spesifik seperti “perlu tanggal tanam”, “perlu informasi irigasi”, atau “perlu tinjauan agronomi”.

### Bukti dan kualitas

Angka dari sumber, hasil turunan aplikasi, isian petani dan asumsi skenario memiliki label berbeda. NASA POWER/MODIS disebut sebagai sumber NASA. SoilGrids, FAO/GAEZ/Kementan, Copernicus dan ESA tetap memakai identitas serta atribusi masing-masing.

Piksel utama MODIS memiliki data strict-good pada 31 dari 60 bulan; pembanding pada 32 dari 60 bulan. Grafik utama hanya memakai strict-good, mempertahankan bulan kosong, dan tidak menyimpulkan spesies tanaman, tanggal tanam atau masa lahan kosong dari seri tersebut.

## Alur pengguna

1. Buka FieldShift dan pilih contoh Klaten atau tandai lokasi sendiri.
2. Lihat kondisi historis serta layer yang tersedia untuk lokasi itu.
3. Pilih “Bandingkan rotasi”, lalu isi profil dan periode yang relevan.
4. Susun/tinjau rotasi berjalan dan dua kandidat; tandai asumsi skenario secara eksplisit.
5. Jalankan pemeriksaan bagian yang inputnya cukup. Tinjau hasil berdampingan dan kebutuhan informasi yang tersisa.
6. Ubah satu pilihan, periode atau prioritas untuk mengeksplorasi perubahan pertimbangannya.

Pengguna boleh kembali ke konteks lingkungan saat informasi petani belum lengkap. Penyuluh dapat memakai alur yang sama untuk meninjau asumsi bersama petani.

## Layar yang akan dibangun

| Layar | Tugas utama | Isi inti |
|---|---|---|
| Peta dan kondisi | Memahami lokasi beserta ketersediaan data | Peta, contoh lokasi, ringkasan lingkungan dan kualitas |
| Profil dan skenario | Menyusun bahan perbandingan | Formulir bertahap, rotasi berjalan, periode dan dua kandidat |
| Perbandingan strategi | Menelaah bukti dan kendala | Tiga strategi, kalender yang didukung input, alasan dan data yang kurang |

Detail sumber/metode dapat dibuka dari hasil terkait tanpa memutus alur. Tata letak visual, komponen dan stack belum ditetapkan pada tahap ini; pilihannya mengikuti kebutuhan alur ketika tahap implementasi dimulai.

## Fitur untuk tahap pengembangan berikutnya

Penilaian ekonomi dengan data harga/biaya/hasil yang sesuai; prakiraan musim operasional; ekstraksi lokasi baru yang lebih luas; observasi HLS/air/termal tambahan; simulasi tanaman terkalibrasi; penyimpanan lintas perangkat; dan penggunaan offline.

Penghematan air dalam persen, keuntungan, hasil panen, kredit nitrogen, resep pupuk dan perubahan kesehatan tanah membutuhkan metode serta input yang belum tersedia untuk klaim tersebut. MVP tidak menyediakan angka atau jaminan itu. Semua pilihan misi NASA tidak perlu diintegrasikan sekaligus untuk mencapai alur inti.

## Kriteria penerimaan MVP

| ID | Kondisi yang harus dipenuhi pada implementasi |
|---|---|
| AC-01 | Pengunjung dapat membuka contoh lokasi dan memahami konteks tanpa membuat akun atau mengarang profil petani. |
| AC-02 | Tiga strategi mempunyai identitas, periode dan asal input yang jelas. Slot kosong tetap ditandai belum lengkap. |
| AC-03 | Hasil dapat ditelusuri ke data NASA yang benar-benar dipakai dan referensi pendukungnya; angka turunan memiliki metode/label. |
| AC-04 | Lokasi di luar cakupan diperiksa per layer dan tidak diam-diam menerima angka titik contoh terdekat. |
| AC-05 | Grafik MODIS mempertahankan gap kualitas dan identitas mixed pixel; marginal tidak masuk statistik utama. |
| AC-06 | Input null tidak berubah menjadi nol, prioritas default, riwayat kosong atau kesimpulan positif. |
| AC-07 | Kalender tidak mengarang tanggal panen ketika tanggal awal/durasi tidak cukup; semai dan pindah tanam dibedakan. |
| AC-08 | Perbandingan menampilkan alasan, kendala dan kebutuhan informasi secara konsisten, tanpa peringkat/skor manfaat yang belum tervalidasi. |
| AC-09 | Baseline, riwayat dan data 2026 parsial dibedakan. Tidak ada label prakiraan untuk data historis atau label irigasi aktual untuk P−ETo. |
| AC-10 | Formulir dan perbandingan dapat digunakan di HP serta laptop, dengan label terbaca, akses keyboard dan keadaan memuat/kosong/gagal yang jelas. |
| AC-11 | Gangguan peta atau layanan tidak menghasilkan data atau notifikasi keberhasilan palsu. |
| AC-12 | Isian dan asumsi sesi tetap terpisah dari data mentah dan template sumber. Tidak ada klaim penyimpanan permanen yang belum diimplementasikan. |
| AC-13 | Satu kasus demonstrasi berlabel asumsi harus menjalankan perbandingan penuh: existing sebagai kelanjutan rotasi berjalan, dua kandidat berbeda secara bermakna, periode rencana yang sama, input cukup untuk pemeriksaan terpilih, serta hasil berbasis bukti dan keterbatasan per strategi. Kasus lengkap ini wajib tersedia selain kasus input parsial. |

Kriteria ini adalah sasaran implementasi, bukan hasil pengujian aplikasi yang sudah berjalan.

## Selesainya tahap 1 dan pekerjaan tahap 2

Tahap 1 selesai ketika cakupan produk, batas data, alur, input/output dan kriteria penerimaan telah terdokumentasi serta diperiksa terhadap data yang tersedia. Online telah dikonfirmasi pengguna. Tidak ada keputusan stack, algoritme skor atau publikasi yang dibuat secara tersirat.

Tahap berikutnya: rancang metode pembentukan dua kandidat, aturan pemeriksaan, prasyarat setiap keluaran, asal bukti dan cara menjelaskan hasil. Gunakan contoh skenario berlabel asumsi untuk memeriksa logika; data lahan sebenarnya tetap menunggu input petani.

## Rujukan kerja

Audit sebelum backend menambah sumber publik dan memperjelas kontrak input tanpa mengubah cakupan produk. Gunakan [audit terbaru](../outputs/audit-kelengkapan-data-fieldshift.md), [indeks data tambahan](../data/supplemental/readiness-audit.json) dan [kontrak input bertipe](../data/supplemental/agronomy/farm-input-contract.json) bersama rujukan snapshot awal di bawah. Observasi petani belum tersedia; sumber publik digunakan sebagai konteks contoh yang eksplisit.

- [Deskripsi challenge yang tersimpan](../work/page-text.txt) dan [halaman resmi Field Shift](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/).
- [Profil analisis dan cakupan](../data/prepared/analysis-profile.json), [status kesiapan](../data/prepared/readiness.json), serta [laporan data](../outputs/kesiapan-data-fieldshift.md).
- [Aturan agronomi dan batas bukti](../data/prepared/agronomy/agronomy-rules.json), [kamus input petani](../data/prepared/agronomy/farm-input-data-dictionary.json), dan [template tiga strategi](../data/prepared/agronomy/strategy-comparison-template.json).
- [Ringkasan QA vegetasi](../data/prepared/vegetation/summary.json) dan [ringkasan tanah/topografi/tutupan lahan](../data/prepared/soil-terrain/summary.json).
