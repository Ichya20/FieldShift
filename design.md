# FieldShift — Design Brief for Stitch

Versi awal 1.0 · 8 November 2026 · Persiapan desain frontend.

> **Revisi arah terbaru:** pengguna meminta pengenalan produk dan alur aplikasi digabung menjadi landing page responsif dengan 3D serta tipografi sederhana. Gunakan [prompt revisi landing page + 3D](docs/stitch-revision-landing-3d.md) sebagai prioritas komposisi, navigasi, hero dan tipografi. Arahan awal yang melarang landing page serta ketentuan sidebar/font di bawah telah diganti. Detail fungsi, sumber, status dan batas data tetap berlaku.

> **Penyempurnaan visual:** pengguna menyukai struktur landing page, tetapi meminta shading dan color grading yang lebih baik. [Prompt material & warna terbaru](docs/stitch-revision-material-color.md) memprioritaskan pencahayaan daylight konsisten, material tanah/daun berbeda, grading render netral dan kanvas `#F5F5F2`, dengan layout dan fungsi tetap.

## 1. Tujuan desain

Rancang aplikasi web responsif **FieldShift**, alat bantu untuk mengeksplorasi rotasi tanaman menggunakan data lingkungan NASA, referensi tanah/agronomi, dan isian pengguna. Seluruh teks antarmuka berbahasa Indonesia.

Pertanyaan produk: **“Apa yang perlu saya pertimbangkan jika mengubah rotasi tanaman di lokasi ini?”**

Pengguna utamanya petani dan penyuluh di area contoh Yogyakarta–Klaten. Mereka perlu memahami bukti dan keterbatasannya, menyusun skenario, lalu membandingkan rotasi berjalan dengan dua alternatif. Backend MVP sudah tersedia. Desain ini menjadi bahan implementasi frontend berikutnya.

Hasil yang diminta dari Stitch: desain aplikasi yang dapat dikerjakan, mencakup tiga layar inti, versi desktop/mobile, komponen konsisten, serta keadaan data parsial. Mulai langsung dari aplikasi dengan lokasi contoh; jangan tambahkan landing page pemasaran.

## 2. Karakter visual

**Arah: atlas pertanian yang tenang, jelas, dan mudah digunakan.** Identitas FieldShift muncul dari peta Klaten, garis waktu musim, serta tiga jalur rotasi yang dapat dibandingkan pada periode sama.

- Gunakan latar putih kehijauan sangat tipis, panel putih, teks gelap, dan aksen hijau hutan.
- Peta dan kalender menjadi elemen utama; dekorasi tidak mengambil tempat bukti.
- Pakai permukaan datar, garis pemisah halus, jarak teratur, sudut moderat, dan hierarki tipografi kuat.
- Tampilkan ringkasan angka dalam satu kelompok bersekat; hindari setiap angka menjadi kartu dengan ikon berwarna.
- Tiga strategi memiliki ukuran dan bobot visual setara. Angka 1/2 menunjukkan identitas alternatif, bukan peringkat.
- Ikon outline satu keluarga, misalnya Lucide; selalu sertakan teks untuk tindakan penting.
- Wordmark “FieldShift” dengan simbol sederhana tiga jalur tanam sejajar. Simbol tidak menyerupai logo NASA. NASA disebut pada sumber yang relevan, tanpa menyiratkan afiliasi resmi.
- Tidak memakai gradient dekoratif, glassmorphism, neon, bayangan besar, emoji sebagai ikon, ilustrasi petani generik, atau tampilan pusat kendali luar angkasa.

### Warna

| Token | Nilai | Pemakaian |
|---|---|---|
| Background | `#F7F9F6` | Kanvas aplikasi dan navigasi |
| Surface | `#FFFFFF` | Panel, formulir, drawer |
| Text primary | `#1C2C23` | Judul, isi, angka |
| Text secondary | `#54645A` | Bantuan dan metadata |
| Border subtle | `#DCE3DC` | Pemisah dekoratif |
| Border control | `#7C897F` | Batas input yang perlu dikenali |
| Active neutral | `#E7ECE7` | Navigasi aktif dan hover |
| Brand / primary | `#235B3A` | Satu aksi utama per area dan identitas |
| Primary hover | `#19452C` | Hover tombol utama |
| Climate blue | `#256B8E` | Curah hujan atau seri iklim terpilih |
| Harvest ochre | `#936216` | Jagung pada kalender |
| Soy slate | `#526477` | Kedelai pada kalender |
| Information | `#235C83` on `#EAF3FA` | Bukti tersedia dan informasi |
| Review | `#805600` on `#FFF3D6` | Perlu informasi/tinjauan |
| Conflict | `#A12A2A` on `#FDEDED` | Konflik isian dan kegagalan |
| Neutral status | `#54645A` on `#EEF1EE` | Tidak berlaku, luar cakupan |

Tombol hijau memakai teks putih. Status memakai teks gelap pada tint pucat. Warna harus disertai label/ikon; hijau bukan penanda bahwa suatu rotasi aman atau direkomendasikan. Warna tanaman konsisten di semua layar.

### Tipografi dan ukuran

- Font utama: **Atkinson Hyperlegible**, fallback `system-ui, sans-serif`; bobot 400 dan 700.
- Judul halaman: desktop 28/36 px, mobile 24/32 px, bobot 700.
- Judul bagian: 18/26 px, bobot 700.
- Isi, label input dan tombol: 16/24 px. Metadata: 14/20 px; jangan mengecilkan status penting.
- Angka ringkasan: 26–30 px; satuan tetap terlihat. Angka tabel menggunakan tabular numerals dan rata kanan.
- Format Indonesia: `2.964,05 mm`, `26,16 °C`, `5,8`. Koordinat input diberi contoh desimal dan penjelasan format.
- Skala jarak: 4, 8, 12, 16, 24, 32, 48 px. Padding panel 20–24 px desktop, 16 px mobile.
- Radius: panel 12 px, input/tombol 8 px, badge 6 px. Bayangan hanya untuk elemen melayang.
- Tinggi kontrol 44–48 px. Semua target sentuh minimal 44 × 44 px.

## 3. Navigasi dan kerangka aplikasi

Tiga tujuan navigasi: **Kondisi lokasi**, **Susun skenario**, **Perbandingan**. Detail **Sumber & metode** dibuka sebagai drawer, bukan tujuan navigasi utama tambahan.

Desktop 1440 × 1000 px: navigasi kiri sekitar 216 px, kanvas fleksibel dengan padding 28–32 px. Sidebar memakai warna kanvas, bukan bidang hijau gelap. Identitas produk dan “Area contoh Yogyakarta–Klaten” terlihat. Bagian atas halaman memuat nama layar, lokasi/periode aktif, serta satu tindakan utama.

Mobile 390 × 844 px: header ringkas dengan wordmark dan bantuan; navigasi bawah tiga tujuan berlabel. Margin 16 px. Sediakan safe area dan ruang bawah agar navigasi atau tombol sticky tidak menutupi isi/fokus. Tidak ada avatar, login, billing, lonceng notifikasi, atau pencarian global tanpa fungsi.

Status sesi ditulis singkat: **“Isian digunakan selama sesi ini.”** Jangan menampilkan “Tersimpan” karena penyimpanan permanen belum tersedia.

## 4. Layar A — Kondisi lokasi

Pertanyaan layar: **“Data apa yang tersedia untuk lokasi dan periode ini?”**

### Susunan desktop

1. Judul **“Kondisi lokasi”**; subjudul “Konteks lingkungan untuk meninjau pilihan rotasi.”
2. Pemilih **“Contoh Klaten utama”**, **“Contoh Klaten pembanding”**, atau **“Pilih titik sendiri”**. Pemilih periode dan mode waktu berada di dekat lokasi.
3. Peta sekitar 60% lebar, panel informasi lokasi sekitar 40%. Tinggi awal peta sekitar 360–420 px; jangan mendominasi seluruh layar.
4. Di panel: nama contoh, koordinat ringkas, label **“Lokasi contoh · belum terverifikasi sebagai lahan”**, dan ketersediaan layer per sumber.
5. Ringkasan iklim tahunan dalam satu panel bersekat. Di bawahnya, grafik iklim dan bagian tanah/vegetasi dengan judul serta sumber yang mudah dibuka.
6. Aksi utama **“Susun skenario”**; aksi sekunder **“Lihat demo perbandingan”**.

### Peta

- Dua penanda contoh bernama, zoom +/−, tombol kembali ke area contoh, legenda, skala, dan atribusi basemap.
- Bedakan titik pilihan, footprint piksel yang tersedia, dan cakupan subset tanah. Tidak menggambar batas lahan petani dari footprint.
- Layer toggle: “Cakupan data”, “Piksel vegetasi”, “Tanah & medan”. Bentuk cakupan tidak disamakan antarproduk.
- Pilih titik melalui peta atau pasangan koordinat. Tidak ada alat menggambar poligon pada MVP.
- Titik khusus tidak otomatis memperoleh konteks POWER: tampilkan pilihan eksplisit **“Gunakan konteks iklim regional Yogyakarta”** dengan penjelasan dukungan regional.
- Di luar cakupan: **“Data tanah belum tersedia untuk titik ini.”** Pilihan **“Buka contoh Klaten”** memerlukan tindakan pengguna; jangan memindahkan titik atau mengganti angka diam-diam.
- Untuk mockup Stitch, peta skematis boleh dipakai dan diberi label **“Pratinjau peta”**. Jangan membuat citra satelit, raster analitis, atau batas petak rekaan yang terkesan hasil pengukuran.

### Data dan grafik

- Mode waktu: **“Riwayat historis”**, **“Data terbaru parsial”**, **“Analog historis · bukan prakiraan”**. Default contoh: riwayat tahun 2025, bukan kondisi hari ini.
- Iklim: total hujan, ETo referensi, selisih P−ETo, rerata suhu; periode dan hari valid terlihat.
- P−ETo diberi bantuan: **“Selisih hujan dan ETo referensi; bukan kebutuhan irigasi.”** Jangan menafsirkan nilai positif sebagai bukti kecukupan air tanaman.
- Grafik iklim menggunakan panel kecil terpisah untuk hujan dan ETo, dengan sumbu/satuan jelas; tidak memaksakan dua satuan dalam satu sumbu. Data bulanan perlu agregasi frontend atau perluasan endpoint; jangan mengarang titik grafik dari total tahunan.
- Tanah: pH, kedalaman, rentang prediksi Q05–Q95, label **“Prediksi SoilGrids”**. Elevasi/lereng diberi sumber **“Copernicus DEM”**.
- Vegetasi: panel Terra dan Aqua terpisah pada sumbu waktu yang sama. Grafik utama hanya memakai observasi `quality_status=good_strict`; nilai marginal/excluded yang masih ada dalam respons bukan titik yang boleh diplot pada seri utama. Pertahankan gap QA dan jangan menyambungkannya melintasi data kosong. Gunakan titik yang lolos kualitas, jangan garis tren yang menyiratkan observasi tambahan.
- Caption: **“Piksel campuran; jenis tanaman dan tanggal tanam tidak dapat disimpulkan dari grafik ini.”**
- Ringkasan layer selalu memiliki “Lihat sumber”, periode, dukungan spasial, serta status. Nama teknis lengkap bisa berada di drawer.

### Mobile

Pemilih lokasi/periode → peta sekitar 240 px → status cakupan → ringkasan angka 2 kolom → bagian iklim/tanah/vegetasi yang dapat dibuka. Tidak ada peta layar penuh sebagai satu-satunya cara memilih lokasi. Aksi “Susun skenario” tetap mudah ditemukan.

## 5. Layar B — Susun skenario

Pertanyaan layar: **“Informasi apa yang perlu diisi agar rotasi dapat dibandingkan?”**

Gunakan formulir bertahap dengan tiga kelompok: **Lokasi & periode**, **Rotasi & kalender**, **Kondisi & prioritas**. Tampilkan ringkasan pilihan di sisi kanan desktop; pada mobile gunakan ringkasan yang dapat dibuka. Kontrak memiliki 119 field untuk berbagai kebutuhan, tetapi formulir awal hanya menampilkan input yang relevan.

### Lokasi & periode

- Lokasi dari layar A tetap terlihat dan dapat diubah.
- Pilih **“Skenario asumsi”** atau **“Isian pengguna”**. Jika mode asumsi dipilih, wajib ada catatan asumsi yang dapat diedit.
- Label tanggal **“Mulai periode”** dan **“Sampai tanggal (termasuk)”** untuk pengguna. Implementasi mengubah tanggal akhir inklusif menjadi `end_exclusive` pada hari berikutnya. Jangan menampilkan konvensi teknis API sebagai label formulir.
- Riwayat/analog/parsial terlihat, dengan keterangan analog bukan forecast.

### Rotasi & kalender

- Urutan rotasi berjalan berupa 1–3 slot berlabel. Setiap slot memilih padi/jagung/kedelai, metode tanam, tanggal semai, tanggal pindah tanam jika relevan, serta tanggal panen yang diketahui.
- Tombol **“Tambah slot tanaman”** hanya muncul jika jumlah slot kurang dari tiga. Tidak mewajibkan drag-and-drop; kontrol pilih/ubah posisi harus dapat digunakan dengan keyboard.
- Konfirmasi **“Saya menggunakan urutan ini sebagai kelanjutan rotasi pada periode yang dipilih.”** Tidak tercentang otomatis pada formulir kosong.
- Pilih tanaman yang boleh dicoba/dihindari. Jangan mengisi prioritas atau riwayat petani otomatis.
- Durasi memiliki rentang minimum–maksimum, asal hitung semai/pindah tanam, sumber, dan catatan normalisasi bila berubah dari sumber. Referensi umur varietas adalah bantuan yang dipilih pengguna, bukan default petani.
- Input persemaian terpisah hanya untuk metode yang relevan; jeda persiapan ditampilkan sebagai informasi yang perlu diisi.
- Kalender bersama untuk tanaman alternatif memerlukan pilihan eksplisit dan catatan asumsi. Tanpa itu, metode/tanggal dari padi tidak dipindahkan otomatis ke jagung/kedelai.
- Penanda gembok pada prefix terkunci berarti urutan dan kalender tanaman tersebut dipertahankan pada alternatif; bukan tombol mengubah hasil menjadi valid.
- Aksi **“Isi asumsi demo 2025”** menampilkan ringkasan asumsi sebelum diterapkan. Jika isian sudah ada, konfirmasi sebelum menggantinya.

### Kondisi & prioritas

- Kelompok awal: sumber air/irigasi, drainase, ekosistem/rezim air padi jika diketahui.
- Prioritas multi-pilih: **Konteks air**, **Kondisi tanah**, **Pengelolaan hama**, **Kalender tanam**, **Informasi ekonomi**. Tidak ada pilihan/bobot default.
- Bantuan prioritas: **“Pilihan menyorot informasi yang relevan; tidak memberi peringkat strategi.”** Ekonomi diberi keterangan “Belum dihitung pada MVP”.
- Uji tanah, residu, nodulasi dan riwayat hama dibuka saat diperlukan melalui “Lengkapi informasi”. Jangan tampilkan semua field lanjutan sekaligus.
- Semua kelompok menyediakan **“Belum tahu”**. Nilai kosong berbeda dari nol, jawaban “tidak ada”, atau pilihan “tidak”.

Aksi utama **“Bandingkan strategi”**. Input parsial boleh dilanjutkan dengan penjelasan **“Beberapa pemeriksaan akan menunggu informasi tambahan.”** Isian yang tidak valid/bertentangan ditandai dekat field, disertai ringkasan kesalahan dan tautan menuju field. Saat memproses, tampilkan “Memeriksa skenario…” tanpa persentase kemajuan rekaan.

## 6. Layar C — Perbandingan strategi

Pertanyaan layar: **“Apa bukti, kendala, dan informasi yang kurang pada masing-masing rotasi?”**

### Hierarki

1. Judul **“Perbandingan strategi”**, lokasi, periode, mode waktu dan badge **“Skenario asumsi”** jika relevan.
2. Jika ketiga urutan tersedia, pesan ringkas: **“Tiga skenario untuk ditinjau. Sebagian pemeriksaan masih memerlukan informasi.”** Jika kandidat belum lengkap, jumlah mengikuti hasil sebenarnya dan slot yang kosong dijelaskan. Aksi **“Ubah skenario”**.
3. Tiga kolom setara: **“Rotasi berjalan”**, **“Alternatif 1”**, **“Alternatif 2”**. Urutan tetap; tidak ada podium, bintang, “terbaik”, atau kolom pemenang.
4. Kalender tiga jalur dengan sumbu waktu bersama. Label tanaman terbaca, slot terkunci terlihat, jeda dan periode belum ditentukan berbeda secara visual.
5. Matriks pemeriksaan dengan baris konsisten dan status per strategi; detail dapat diperluas. Bukti, asumsi, data kurang, serta langkah berikutnya muncul di dekat kesimpulan.

### Isi per strategi

- Urutan tanaman dan alasan pembentukan kandidat dalam bahasa sederhana.
- Status **“Analisis sebagian”**. Kalender yang berhasil dihitung tidak membuat keseluruhan strategi berstatus tervalidasi.
- Jadwal dengan label **“Kalender berdasarkan asumsi”** atau asal input pengguna. Rentang panen dipertahankan, tidak dirata-ratakan.
- “Perlu dilengkapi” berisi kebutuhan spesifik, misalnya rezim air padi, drainase, atau riwayat organisme pengganggu.
- “Bukti & pertimbangan” menampilkan penjelasan pendek dan tindakan **“Lihat bukti”**.
- Prioritas terpilih ditandai “Sesuai fokus Anda” pada baris terkait; tidak menyembunyikan pemeriksaan lain atau mengubah urutan kandidat.

### Dua belas pemeriksaan

| ID backend | Label antarmuka |
|---|---|
| `coverage` | Cakupan data |
| `calendar` | Kalender & jeda |
| `climate_exposure` | Paparan hujan & ETo |
| `ph_reference` | Referensi pH tanah |
| `temperature_reference` | Referensi suhu |
| `seasonal_et_reference` | Referensi kebutuhan air musiman |
| `paddy_upland_transition` | Transisi padi ke tanaman lahan kering |
| `legume_mechanism` | Mekanisme legum |
| `pest_break` | Tinjauan siklus hama |
| `vegetation_context` | Konteks vegetasi |
| `gaez_context` | Kategori GAEZ historis |
| `economics` | Informasi ekonomi · belum dihitung |

Referensi air musiman adalah rentang umum dari literatur; jangan menggantinya menjadi kebutuhan irigasi lokal atau penghematan. Kategori GAEZ mempertahankan rezim pengelolaan terpisah dan bukan skor kesesuaian.

### Tata letak mobile

Awali dengan ringkasan ketiga urutan, lalu tampilan **“Bandingkan per aspek”**. Setiap aspek menampilkan tiga baris strategi agar bukti tetap dapat dibandingkan tanpa menggeser seluruh halaman. Detail satu strategi dapat dibuka lewat tab/dropdown berlabel. Jangan menyusutkan tiga kolom desktop menjadi teks sempit. Kalender mobile dapat menjadi daftar tanggal per strategi dengan periode yang sama tetap terlihat.

## 7. Sumber, status, dan penjelasan

Drawer **“Bukti & sumber”**: judul indikator, nilai/satuan, nama sumber, jenis data, periode observasi/model, dukungan ruang, hari/observasi valid, metode turunan jika ada, keterbatasan, serta tautan sumber. Desktop drawer kanan sekitar 420 px; mobile menjadi sheet penuh dengan judul dan tombol tutup terlihat.

Bedakan **data publik**, **prediksi model**, **perhitungan aplikasi**, **isian pengguna**, dan **asumsi skenario**. Isian pengguna belum berarti pengukuran terverifikasi. Labelkan NASA POWER/MODIS sebagai sumber NASA; SoilGrids, FAO/GAEZ/Kementan, Copernicus dan ESA memakai atribusinya sendiri.

| Status | Label UI | Perlakuan |
|---|---|---|
| `evidence_available` | Bukti tersedia | Informasi, bukan persetujuan agronomi |
| `needs_input` | Perlu informasi | Sebutkan input dan tindakan melengkapinya |
| `review_required` | Perlu tinjauan | Jelaskan hal yang perlu ditelaah |
| `input_conflict` | Ada konflik input | Tautkan ke catatan yang bertentangan |
| `outside_coverage` | Di luar cakupan | Tidak menampilkan angka pengganti |
| `not_applicable` | Tidak berlaku | Jelaskan relevansinya pada urutan tanaman |
| `partial` | Analisis sebagian | Ringkas pemeriksaan yang masih terbuka |
| `invalid_input` | Periksa isian | Tampilkan bantuan koreksi |
| `insufficient_alternatives` | Alternatif belum lengkap | Tinjau pilihan tanaman atau slot terkunci |

Tidak ada persen “kepercayaan”, skor kesiapan lahan, traffic light aman/berbahaya, atau tanda lulus hanya karena data tersedia. Pernyataan singkat pada hasil: **“Alat bantu eksplorasi. Pertimbangan lapangan perlu ditinjau bersama petani atau penyuluh.”**

## 8. Contoh konten yang boleh dipakai

Sumber angka: respons backend demo historis 2025, lokasi `klaten_cropland_primary`.

| Elemen | Nilai/label mockup |
|---|---|
| Nama lokasi | Contoh Klaten utama |
| Koordinat tampilan | −7,721875; 110,553545 · presisi grid, bukan GPS petak |
| Periode | 1 Januari–31 Desember 2025 |
| Jenis sesi | Skenario asumsi · lingkungan historis |
| Hujan regional | 2.964,05 mm · 365/365 hari |
| ETo referensi | 1.372,10 mm · 365/365 hari |
| P−ETo | +1.591,95 mm · bukan kebutuhan irigasi |
| Suhu rerata | 26,16 °C · konteks regional |
| pH model | 5,8 · kedalaman 0–5 cm · Q05–Q95: 4,2–7,9 |
| Rotasi berjalan | Padi → Padi |
| Alternatif 1 | Padi → Jagung |
| Alternatif 2 | Padi → Kedelai |
| Status ketiganya | Analisis sebagian |

Kalender demo: tanaman pertama mulai 1 Januari, tanaman kedua mulai 1 Juni 2025. Umur asumsi padi 120 hari, jagung 100 hari, kedelai 90 hari sejak semai, hari nol. Panen pertama 1 Mei; panen kedua masing-masing 29 September, 9 September, 30 Agustus. Hari panen masih mengokupansi lahan; petak lepas pada hari berikutnya. Semua tanggal merupakan kalender asumsi demo, bukan observasi petani atau prediksi.

Total iklim satu tahun sama pada ketiga strategi. Tampilkan sekali sebagai konteks bersama; jangan memberi kesan tiap tanaman mengubah total hujan atau bahwa selisih jendela tanam merupakan air yang dihemat.

Angka hanya dibulatkan untuk tampilan. Penjumlahan dari angka tampilan dapat berbeda 0,01 mm; jangan membangun metrik turunan baru dari angka yang sudah dibulatkan. Seri grafik harus berasal dari nilai seri backend/dataset, bukan angka bulanan yang dibuat untuk mengisi mockup.

## 9. Keadaan interaksi yang wajib dirancang

- **Awal tanpa isian:** contoh lokasi dapat dibuka; formulir pengguna kosong. Tiga slot hasil kosong tetap bertuliskan “Belum ada skenario”, bukan analisis berhasil.
- **Memuat:** skeleton datar mengikuti struktur akhir; label tetap terlihat. Tidak menampilkan angka sementara atau shimmer berlebihan.
- **Input parsial:** ringkasan hal yang diketahui dan hal yang menunggu input; tetap dapat mengakses konteks.
- **Alternatif kurang:** pembatasan tanaman atau slot terkunci dapat menghasilkan kurang dari dua kandidat. Pertahankan slot kosong berlabel “Belum ada alternatif untuk konfigurasi ini”, jelaskan batasan yang relevan, dan sediakan “Ubah skenario”. Jangan menyalin rotasi berjalan untuk mengisi slot atau menyatakan tiga strategi telah dianalisis.
- **Gap kualitas:** grafik terputus dan catatan “Tidak ada observasi yang lolos kualitas pada periode ini.” Tidak dianggap nol atau lahan kosong.
- **Konflik kalender:** tandai tanggal/slot terkait; hasil menyebut benturan okupansi, bukan menyatakan tanaman tidak layak.
- **API gagal:** “Data belum dapat dimuat. Coba lagi.” dengan tombol retry; isian sesi tidak hilang. Status error berbeda dari “data tidak tersedia”.
- **Peta gagal:** panel koordinat/pemilih contoh tetap dapat dipakai; teks menjelaskan peta gagal dimuat.
- **Data terbaru parsial:** tampilkan tanggal valid per metrik. Jangan memakai tanggal unduh atau akhir permintaan sebagai tanggal semua nilai.
- **Sumber statis:** label snapshot/periode. Tombol “Coba lagi” hanya mengulang permintaan aplikasi; jangan menjanjikan mengambil observasi NASA terbaru.
- **Hasil sudah berubah:** setelah input diedit, tandai hasil sebelumnya dan sediakan “Hitung ulang”; jangan menampilkan hasil lama sebagai hasil isian baru.

## 10. Aksesibilitas dan responsivitas

Target WCAG 2.2 AA: kontras teks minimal 4,5:1; kontrol dan fokus memiliki pembeda yang jelas. Semua fungsi dapat digunakan dengan keyboard. Label input selalu terlihat; tooltip dapat dibuka dengan sentuh/keyboard, bukan hover saja. Pesan status diumumkan secara wajar, bukan mengganggu setiap perubahan field.

Sediakan alternatif teks/tabel untuk grafik dan input koordinat sebagai alternatif pemilihan peta. Ketidakpastian/rentang/gap tidak disampaikan lewat warna saja. Hentikan animasi nonesensial saat reduced motion aktif; transisi sederhana 120–180 ms. Pertahankan zoom teks dan hindari scroll horizontal pada halaman.

Rancang pada lebar 390 px dan 1440 px; pertimbangkan 320/768/1024 px. Mobile mempertahankan semua informasi penting melalui disclosure, bukan menghilangkannya. Accordion berjudul dan status tetap terlihat saat tertutup.

## 11. Batas fitur MVP

Jangan membuat kontrol aktif atau hasil untuk login, penyimpanan permanen, berbagi publik, ekspor PDF, notifikasi, mode offline, menggambar batas lahan, prakiraan musim, harga pasar live, atau pengambilan data global otomatis.

Tidak menampilkan ranking, skor kesesuaian gabungan, prediksi hasil panen, profit, persen hemat air, kebutuhan irigasi petak, kredit nitrogen, resep pupuk, atau peningkatan kesehatan tanah terukur. Output tersebut belum dihitung. NASA memberi konteks lingkungan; aplikasi tidak menggantikan keputusan petani dan tinjauan agronomi lokal.

Jangan menambahkan dashboard bisnis, “10.000 petani terbantu”, pertumbuhan produktivitas, luas lahan contoh, atau status koneksi sensor live rekaan. Online berarti web membutuhkan koneksi; data contoh berupa snapshot historis dengan latensi berbeda per produk.

## 12. Paket desain yang diminta dari Stitch

1. **Kondisi lokasi — desktop dan mobile**, lokasi contoh, riwayat 2025, peta serta kualitas sumber.
2. **Susun skenario — desktop dan mobile**, formulir bertahap dengan catatan asumsi dan keadaan parsial.
3. **Perbandingan strategi — desktop dan mobile**, tiga strategi setara dan kalender asumsi.
4. Variasi penting: lokasi di luar cakupan, input/kalender konflik, data parsial/gap kualitas, serta kegagalan API/peta.
5. Komponen: navigasi, pemilih lokasi/periode, label asal data, status, input tanggal/rentang, slot tanaman terkunci, kalender, baris matriks pemeriksaan, grafik dengan gap, drawer sumber, dan inline error.

Gunakan satu sistem warna/tipografi/spacing pada semua frame. Seluruh copy harus spesifik FieldShift dan berbahasa Indonesia. Tampilkan kemampuan MVP secara konkret, dengan bukti dan keterbatasannya dekat hasil.

## Rujukan untuk handoff implementasi

Bagian ini konteks pengembang, bukan teks yang ditampilkan ke pengguna produk.

- [Deskripsi siap tempel ke Stitch](docs/stitch-project-description.md).
- [API dan kebijakan input](backend/README.md).
- [Request demo](outputs/backend-demo-request.json) dan [hasil demo](outputs/backend-demo-response.json).
- [OpenAPI](outputs/backend-openapi.json) dan [metode 12 pemeriksaan](specs/rotation-method-v1.json).
- [Roadmap](docs/roadmap.md). Dokumen ini brief desain; belum merupakan implementasi frontend atau hasil pengujian visual.
- Konversi tanggal akhir inklusif harus diperiksa setelah ditambah satu hari: tanggal API 1900–2100, `end_exclusive` sesudah mulai, panjang maksimal 3.660 hari. Batas tiga slot dan field nullable mengikuti kontrak backend.
