# Prompt revisi Stitch — FieldShift landing page + 3D

> **Revisi visual terbaru:** setelah struktur ini diterapkan, gunakan [prompt material, lighting, dan color grading](stitch-revision-material-color.md). Prompt tersebut mempertahankan layout ini, tetapi memprioritaskan arahan warna, shading dan material yang lebih spesifik.

Salin prompt berikut ke proyek Stitch yang sedang dikerjakan. Ini menggantikan arahan komposisi awal; konteks produk dan batas data tetap berlaku.

---

Revisi desain FieldShift menjadi **satu landing page responsif dengan pengalaman eksplorasi produk di dalamnya**. Gabungkan pengenalan produk, kondisi lokasi, penyusunan skenario, dan perbandingan rotasi dalam satu alur halaman. Arahan ini menggantikan instruksi sebelumnya untuk langsung membuka dashboard, memakai sidebar permanen, dan menghindari landing page.

FieldShift membantu petani dan penyuluh mengeksplorasi rotasi padi, jagung, dan kedelai pada area contoh Yogyakarta–Klaten menggunakan NASA POWER/MODIS, referensi tanah/agronomi, dan isian pengguna. Seluruh copy berbahasa Indonesia. Produk harus terasa jelas, matang, dan khas pertanian; setiap elemen visual membantu memahami lokasi, musim, atau perubahan tanaman.

## Struktur halaman

**Navigasi:** wordmark FieldShift, anchor “Kondisi lokasi”, “Susun skenario”, “Perbandingan”, dan tombol “Mulai eksplorasi”. Header sederhana berlatar solid, menu ringkas pada mobile. Tidak ada sidebar dashboard.

**Hero:** sekitar 45% teks dan 55% visual pada desktop, margin luar seimbang. Judul **“Rotasi tanaman, lebih terarah.”**, maksimal dua baris. Satu kalimat pendukung: “Bandingkan pilihan rotasi melalui konteks iklim, tanah, dan vegetasi untuk area contoh Yogyakarta–Klaten.” Satu CTA utama **“Mulai eksplorasi”** menuju kondisi lokasi. Jangan tambahkan slogan atau badge di atas judul.

**Visual 3D:** satu diorama lahan isometrik dengan penampang tanah tipis, bentuk tanaman yang terbaca, material tanah yang meyakinkan, pencahayaan natural, dan bayangan kontak secukupnya. Kamera tiga perempat, objek utuh, visual besar dan terarah.

3D menjelaskan **tanaman yang berganti pada lokasi yang sama antar musim**. Sediakan kontrol dua fase kalender atau pemilih skenario padi–padi, padi–jagung, padi–kedelai. Pilihan mengubah tanaman di diorama dan jalur kalender yang menyertainya. Jangan menggambar rotasi sebagai beberapa petak berbeda seolah-olah itu tumpangsari. Caption: **“Ilustrasi skenario”**. Diorama bukan citra satelit, batas/luas lahan, atau prediksi pertumbuhan. Pergantian tanaman tidak mengubah angka iklim regional.

Shading material dan pencahayaan alami diperbolehkan. Hindari globe mengambang, ikon mengorbit, kartu kaca melayang, partikel, glow, dan objek berputar tanpa henti. Jika output Stitch statis, tampilkan pose utama serta keadaan pergantian fase; jangan menyatakan interaksi WebGL sudah berjalan.

**Kondisi lokasi:** setelah hero, gunakan area kerja lebar penuh dengan peta dan panel bukti. Pemilih contoh Klaten/titik sendiri, periode, cakupan per layer dan sumber terlihat. Bedakan peta lokasi sebenarnya dari diorama hero. Tombol “Susun skenario” meneruskan lokasi pilihan.

**Susun skenario:** formulir bertahap dalam halaman yang sama: “Lokasi & periode”, “Rotasi & kalender”, “Kondisi & prioritas”. Jangan bentangkan 119 field sekaligus. Sediakan “Belum tahu” dan aksi eksplisit “Gunakan contoh 2025”. Riwayat dan prioritas pengguna tidak diisi otomatis. “Bandingkan strategi” menampilkan hasil pada bagian berikutnya.

**Perbandingan:** tiga strategi setara: “Rotasi berjalan”, “Alternatif 1”, “Alternatif 2”. Tampilkan kalender pada periode sama, bukti, kendala, asumsi dan data kurang. Pakai jalur kalender serta matriks pemeriksaan, bukan kartu paket harga. Pada mobile gunakan perbandingan per aspek dengan tiga baris strategi. Kandidat kosong tetap dijelaskan, bukan diisi rotasi rekaan.

**Sumber & metode:** penutup singkat dengan atribusi yang benar; detail bukti dibuka lewat drawer. Footer ringkas berisi identitas dan tautan bagian. Tidak perlu pricing, testimonial, logo partner, statistik pengguna, atau pengulangan hero di bagian bawah.

## Visual dan tipografi tanpa AI slop

- Latar `#F7F9F6`, permukaan putih, teks `#1C2C23`, aksen hijau hutan `#235B3A`. Warna tanah/tanaman datang dari diorama; jangan menghijaukan setiap panel.
- Gunakan **Libre Franklin** sebagai satu keluarga font. Judul sekitar 56–72 px desktop dan 36–40 px mobile; maksimal dua baris pada lebar sebenarnya. H2 32–36 px desktop dan 26–28 px mobile. Isi 16–18 px; metadata minimal 14 px. Label jelas dan angka tabular rapi.
- Satu warna dan satu font pada judul. Tidak ada accent word berwarna, italic/serif dekoratif, outline text, underline dekoratif, kata raksasa di belakang objek, teks vertikal, marquee, atau huruf yang dianimasikan satu per satu.
- Hapus eyebrow, badge “AI-powered”, slogan berlapis, label kapital renggang, nomor dekoratif 01/02/03, dan copy abstrak seperti “revolusi pertanian masa depan”. Gunakan judul yang menjelaskan isi.
- Jangan ulangi grid kartu fitur pada setiap bagian. Hero memakai pasangan teks–3D, lokasi memakai peta, skenario memakai form, hasil memakai kalender. Setiap bagian mempunyai alasan dan isi konkret.
- Gunakan margin konsisten, jarak yang terukur dan perubahan tone permukaan. Tidak ada bidang kosong setinggi layar, crosshair/garis dekoratif, gradient background, glassmorphism, atau bayangan besar pada panel. Form, tabel dan kalender tetap boleh memakai batas yang diperlukan untuk keterbacaan.
- Setiap tombol punya tujuan nyata. Jangan menambahkan login, pencarian, ekspor atau ikon tanpa fungsi hanya untuk mengisi header.

## Responsivitas dan gerak

Rancang desktop 1440 px dan mobile 390 px; tetap layak pada 320 px serta tablet. Mobile: judul → deskripsi → CTA → diorama sekitar 240–300 px → eksplorasi. Hero tidak mendorong semua kontrol jauh ke bawah. Area kerja desktop memakai lebar penuh, tidak terkurung dalam kolom teks hero.

Tidak ada scroll horizontal halaman, scroll hijacking, loading layar penuh untuk 3D, atau animasi panjang sebelum informasi muncul. Pergantian fase tanaman cukup transisi ringan. Kontrol berlabel dapat digunakan dengan sentuh dan keyboard, bukan hover/drag saja. Perangkat lemah dan reduced motion mendapat render 3D statis beserta kalender teks. Semua konten/CTA tetap bisa dipakai tanpa animasi. Target sentuh minimal 44 px dan kontras AA.

## Kejujuran data

Bedakan data historis, prediksi model, isian pengguna dan asumsi skenario. Demo 2025 membandingkan padi–padi, padi–jagung, padi–kedelai; ketiganya **“Analisis sebagian”**, tanpa ranking. Tanggal/umur demo merupakan asumsi, bukan riwayat petani atau prediksi.

Angka contoh yang boleh dipakai: hujan regional 2025 **2.964,05 mm**; prediksi pH primary **5,8**, kedalaman **0–5 cm**, Q05–Q95 **4,2–7,9**. Sertakan sumber/periode. Jangan mengarang grafik bulanan atau menyebut nilai regional sebagai pengukuran petak. MODIS Terra/Aqua dipisahkan, grafik utama hanya strict-good, gap kualitas tetap terlihat. Titik khusus diperiksa per layer dan memerlukan pemilihan konteks POWER regional secara eksplisit.

Tidak ada klaim rotasi terbaik, profit, persen hemat air, prediksi hasil, peningkatan kesehatan tanah terukur, atau monitoring real-time. Tidak ada login, simpan permanen, ekspor, atau poligon lahan. Sumber dan informasi parsial tetap dapat dibuka dekat hasil; hero tidak perlu dipenuhi disclaimer.

## Hasil yang diminta

Tampilkan satu landing page lengkap versi desktop/mobile, close-up hero 3D beserta keadaan fase tanaman, area eksplorasi dan hasil setelah contoh dipilih, serta keadaan kosong/parsial/gagal. Gunakan satu sistem visual untuk header, form, drawer dan hasil.

Sebelum menyelesaikan, hapus elemen yang tidak membantu menjelaskan produk, memilih lokasi, menyusun skenario, membaca hasil, atau memeriksa sumber. Kualitas desain datang dari komposisi, diorama, interaksi yang jelas, dan isi yang spesifik FieldShift.

---

Catatan handoff: ini prompt revisi, bukan bukti frontend/3D telah diimplementasikan. Komposisi split stage diterapkan pada hero; bagian kerja memakai lebar penuh agar peta/form/hasil tetap nyaman. Font tunggal memakai Libre Franklin dari referensi arah, tanpa display serif dan dekorasi tambahan. Tidak ada evaluasi screenshot desain Stitch dalam pekerjaan ini.
