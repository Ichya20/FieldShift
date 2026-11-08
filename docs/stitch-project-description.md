# FieldShift — deskripsi proyek untuk Stitch

> **Untuk revisi desain terbaru gunakan [prompt landing page + 3D](stitch-revision-landing-3d.md).** Prompt awal di bawah mempertahankan konteks produk; arah tampilannya telah diganti oleh permintaan terbaru pengguna.

> Setelah struktur landing page terbentuk, gunakan [revisi material, lighting & color grading](stitch-revision-material-color.md) untuk memperbaiki tampilan render tanpa mengganti layout.

Salin bagian “Prompt utama” ke Stitch dan sertakan `design.md` sebagai panduan desain. Deskripsi singkat tersedia di akhir jika hanya membutuhkan ringkasan proyek.

## Prompt utama

Rancang antarmuka web responsif untuk **FieldShift**, alat bantu eksplorasi rotasi tanaman yang dikembangkan untuk challenge NASA Space Apps **“Field Shift: Adapting Farms with NASA Data”**. Semua teks antarmuka harus berbahasa Indonesia. Gunakan panduan visual dan batas fitur pada `design.md` yang disertakan.

FieldShift membantu petani dan penyuluh menjawab: **“Apa yang perlu saya pertimbangkan jika mengubah rotasi tanaman di lokasi ini?”** Aplikasi menghubungkan konteks iklim NASA POWER, riwayat vegetasi MODIS, prediksi tanah SoilGrids, medan Copernicus, tutupan lahan ESA WorldCover, referensi tanaman dan kategori GAEZ dengan informasi pengguna. Sumber pendukung tetap memakai atribusinya masing-masing. NASA tidak memberikan rekomendasi rotasi siap pakai; FieldShift menyusun perbandingan berdasarkan metode yang menjelaskan bukti, asumsi dan kebutuhan informasi.

Versi pertama adalah web online tanpa akun, untuk area contoh **Yogyakarta–Klaten** dan tanaman **padi, jagung, kedelai**. Backend MVP sudah tersedia; frontend belum diimplementasikan. Data berupa subset historis dan snapshot, bukan pemantauan real-time. Dua lokasi contoh Klaten adalah titik/piksel campuran yang belum terverifikasi sebagai lahan petani. Jangan membuat profil petani, luas lahan atau riwayat tanam seolah-olah telah diketahui.

Desain tiga layar inti, masing-masing versi desktop 1440 px dan mobile 390 px:

1. **Kondisi lokasi.** Pengguna memilih contoh atau titik sendiri, periode, dan mode waktu. Tampilkan peta, ketersediaan data per layer, ringkasan iklim/tanah, serta riwayat vegetasi dengan gap kualitas. Jelaskan sumber, periode dan dukungan regional/piksel di dekat data. Lokasi di luar cakupan tidak memperoleh angka lokasi lain secara otomatis.
2. **Susun skenario.** Formulir bertahap untuk periode, urutan rotasi, metode tanam, tanggal/durasi dan sumbernya, air/drainase, serta prioritas. Bedakan isian pengguna dan asumsi skenario. Sediakan “Belum tahu”; jangan tampilkan seluruh kontrak 119 field sekaligus. Informasi yang belum ada tetap kosong. Tanaman terkunci mempertahankan kalender di semua alternatif. Sediakan aksi eksplisit untuk mengisi asumsi demo 2025.
3. **Perbandingan strategi.** Tiga strategi setara: rotasi berjalan, alternatif 1 dan alternatif 2. Tampilkan kalender pada periode sama, bukti, kendala, asumsi, informasi yang perlu dilengkapi, serta tindakan melihat sumber. Pada mobile gunakan perbandingan per aspek dengan tiga baris strategi, bukan tiga kolom sempit.

Tampilan harus terasa seperti **atlas pertanian yang jelas dan ramah**, dengan peta serta jalur kalender sebagai identitas. Gunakan latar putih kehijauan tipis, panel putih, teks gelap, aksen hijau hutan, tipografi Atkinson Hyperlegible yang mudah dibaca, garis pemisah halus dan ruang yang teratur. Hindari dekorasi berlebihan, gradient, glassmorphism, neon, kartu KPI generik, sidebar gelap, emoji sebagai ikon, dan landing page pemasaran. Satu tindakan utama terlihat jelas pada setiap layar.

Gunakan contoh historis 2025 berikut bila membutuhkan angka: hujan regional **2.964,05 mm**, ETo referensi **1.372,10 mm**, selisih P−ETo **+1.591,95 mm**, suhu rerata **26,16 °C**; tiap metrik mencakup 365 hari valid. Prediksi pH tanah primary **5,8**, rentang Q05–Q95 **4,2–7,9**, kedalaman **0–5 cm**. P−ETo bukan kebutuhan irigasi. Jangan mengarang seri bulanan untuk mengisi grafik.

Demo membandingkan **padi–padi**, **padi–jagung**, dan **padi–kedelai** menggunakan kalender sintetis berlabel **“Skenario asumsi”**. Status semua strategi **“Analisis sebagian”**. Keberhasilan menghitung kalender tidak berarti rotasi telah dinyatakan layak. Urutan kandidat bukan ranking; prioritas hanya menyorot informasi yang relevan.

Tampilkan status **Bukti tersedia**, **Perlu informasi**, **Perlu tinjauan**, **Ada konflik input**, **Di luar cakupan**, dan **Tidak berlaku** dengan teks serta penanda visual. Jika pembatasan tanaman membuat dua alternatif belum tersedia, slot yang kosong tetap dijelaskan; jangan membuat kandidat rekaan. Rancang juga loading, formulir kosong/parsial, kegagalan API/peta dan grafik dengan gap QA. Grafik MODIS utama hanya memakai observasi strict-good, dengan Terra/Aqua terpisah; nilai marginal/excluded tidak diplot sebagai bukti utama. Detail sumber dibuka melalui drawer desktop atau sheet mobile, dengan periode, satuan, resolusi/dukungan ruang, kualitas, metode turunan dan keterbatasan.

Jangan membuat skor kesesuaian, pemenang strategi, prediksi hasil, profit, persen hemat air, kebutuhan irigasi petak, kredit nitrogen atau klaim peningkatan kesehatan tanah. Jangan menambahkan login, simpan permanen, ekspor, notifikasi, poligon lahan, offline, atau prakiraan musim. Fitur-fitur itu belum tersedia pada MVP. Alat ini membantu pertimbangan petani dan penyuluh; validasi agronomi lokal belum dilakukan.

Hasilkan enam frame inti, variasi keadaan penting, dan komponen konsisten sesuai `design.md`. Prioritaskan keterbacaan, navigasi sederhana, target sentuh minimal 44 px, kontras AA, serta penjelasan ilmiah yang mudah dipahami.

## Deskripsi singkat

FieldShift adalah aplikasi web berbahasa Indonesia yang membantu petani dan penyuluh mengeksplorasi rotasi padi, jagung, dan kedelai pada area contoh Yogyakarta–Klaten. Aplikasi menggabungkan konteks lingkungan NASA POWER/MODIS, referensi tanah dan agronomi, serta isian pengguna untuk membandingkan rotasi berjalan dengan dua alternatif. Setiap strategi menampilkan kalender, bukti, asumsi, kendala dan informasi yang masih kurang. Desain berpusat pada peta, formulir bertahap dan perbandingan yang mudah dibaca di HP maupun laptop. Data historis, prediksi model dan asumsi dibedakan dengan jelas; hasil belum berupa rekomendasi lapangan yang tervalidasi.
