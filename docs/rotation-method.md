# FieldShift — metode eksplorasi rotasi

Versi metode 0.1.0 · 8 November 2026 · Tahap 2 roadmap.

Metode ini membandingkan bukti dan kendala untuk satu kelanjutan rotasi berjalan serta hingga dua kandidat. Metode referensi dapat diperiksa secara numerik, tetapi belum dikalibrasi atau divalidasi sebagai rekomendasi lahan oleh ahli/petani lokal.

## 1. Batas hasil dan kontrak

Setiap perbandingan memakai lokasi, horizon dan mode waktu yang sama. Hasil memisahkan data sumber, turunan, laporan petani dan asumsi skenario. Setiap temuan mempunyai `rule_id`, status, cakupan, input terpakai, referensi sumber, asumsi, penjelasan, input yang kurang dan tindakan berikutnya.

Status temuan: `evidence_available`, `needs_input`, `input_conflict`, `review_required`, `outside_coverage`, atau `not_applicable`. Status pelaksanaan adalah `invalid_input`, `partial` atau `complete_for_selected_checks`. Selesainya pemeriksaan tertentu tidak berarti lahan sudah terbukti sesuai.

Skor kesesuaian gabungan, ranking, hasil panen, persen hemat air, kebutuhan irigasi bersih/kotor, kredit nitrogen, keuntungan dan perubahan kesehatan tanah tetap `null`. Prioritas yang dipilih petani menonjolkan temuan relevan, tanpa bobot atau peringkat buatan.

Kontrak terstruktur: [rotation-method-v1.json](../specs/rotation-method-v1.json). Profil/input sumber tetap mengikuti [MVP](mvp.md) dan [kamus data petani](../data/prepared/agronomy/farm-input-data-dictionary.json).

## 2. Pembentukan dua alternatif

Urutan langkah: **validasi input → bentuk urutan → bangun kalender → periksa kendala → jelaskan bukti**. Keberhasilan membentuk urutan tidak berarti strategi layak.

Input minimum generator adalah horizon, 1–3 slot dengan tanggal mulai, daftar tanaman yang diizinkan/dihindari secara eksplisit, kelanjutan rotasi berjalan, panjang prefix yang terkunci dan konfirmasi kelanjutan. Rotasi historis saja tidak menetapkan tanggal/fase rencana berikutnya.

Kebijakan generator:

1. Gunakan ID tanaman tetap `padi`, `jagung`, `kedelai`. Tolak ID tak dikenal, horizon tidak valid, jumlah slot yang tidak cocok dan allowed/excluded yang bertentangan. `null` berbeda dari daftar kosong yang disengaja.
2. Pertahankan prefix yang sudah tetap, misalnya tanaman yang sedang berlangsung. Preferensi mengecualikan tanaman pada masa depan tidak mengubah tanaman terkunci. Kelanjutan baseline tetap terlihat, dengan temuan bila bertentangan dengan preferensi baru.
3. Enumerasi kombinasi pada slot yang boleh berubah. Tanggal mulai slot sama untuk semua strategi agar perbedaan dapat ditelusuri. Jangan membuat perbedaan hanya pada slot setelah horizon.
4. Singkirkan duplikat dan urutan yang identik dengan baseline. Kandidat pertama mengubah paling sedikit slot, lalu mengikuti urutan ID tetap. Kandidat kedua mengutamakan komposisi tanaman berbeda dari kandidat pertama; jika tidak ada, perbedaan urutan waktu yang nyata dapat dipakai.
5. Urutan tersebut adalah pilihan deterministik untuk demonstrasi, bukan ranking manfaat. Evaluasi kalender dan agronomi menyusul; kendala yang ditemukan tetap terlihat dan dapat mendorong pengguna merevisi skenario.
6. Bila hanya ada nol/satu alternatif, kembalikan jumlah sebenarnya dan `insufficient_alternatives`. Jangan menggandakan kandidat untuk mengisi tiga kolom. Jika input belum diketahui, kembalikan kebutuhan input; konteks lingkungan tetap dapat dibaca.

Lebih dari tiga slot memerlukan skenario yang disusun pengguna atau perluasan metode pada tahap lain. Dua kandidat belum ditetapkan sebagai resep rotasi universal.

## 3. Kalender, nursery dan persiapan

Semua tanggal berupa tanggal kalender tanpa jam. Horizon internal menggunakan interval setengah terbuka `[start_date,end_exclusive)`. Tanggal asal durasi adalah **hari ke-0**. Untuk durasi elapsed `d` dari semai atau pindah tanam:

`harvest_date = origin_date + d hari`

`release_date = harvest_date + 1 hari`

Hari panen masih menempati petak. Okupansi petak adalah `[sowing_date,release_date)` untuk tanam langsung dan `[transplanting_date,release_date)` untuk pindah tanam. Dengan konvensi ini durasi 100 hari setelah semai dapat meliputi 101 tanggal okupansi karena tanggal awal dan panen sama-sama tercakup. Jangan mencampurkannya dengan data durasi yang memakai hitungan inklusif tanpa konversi yang dinyatakan.

Durasi memerlukan nilai minimum/maksimum, basis tanggal dan asal informasi. Durasi berbasis semai sudah mencakup nursery; jangan menambahkan nursery lagi. Jika hanya tanggal pindah tanam diketahui, durasi berbasis semai belum bisa diubah menjadi panen tanpa tanggal semai/umur nursery yang jelas. Contoh umur Anjasmoro yang origin-nya belum eksplisit tetap menjadi referensi, bukan kalender otomatis.

Nursery dan petak utama merupakan sumber daya berbeda. Nursery boleh bertumpang tindih dengan tanaman sebelumnya hanya jika lokasinya terpisah secara eksplisit. Lokasi nursery yang belum diketahui menghasilkan kebutuhan informasi. Kecukupan okupansi petak utama tidak otomatis membuktikan nursery aman.

Rentang durasi dipertahankan sebagai panen/release paling awal dan paling lambat. Untuk tanggal mulai berikutnya `S`, release sebelumnya `[Rmin,Rmax]` dan jeda persiapan `[Gmin,Gmax]`:

- `S >= Rmax + Gmax`: tidak ada konflik pada kalender yang diisi, untuk seluruh rentang.
- `S < Rmin + Gmin`: konflik kalender pada seluruh rentang.
- Kondisi di antara keduanya: kemungkinan konflik bergantung realisasi durasi/jeda.
- Jeda atau tanggal yang belum diketahui: `needs_input`, bukan jeda nol.

Tanaman yang sudah berlangsung sebelum awal horizon dipertahankan sebagai prefix terkunci dengan tanggal biologis asli. Verifikasi bahwa okupansinya masih beririsan dengan horizon; tanaman yang telah selesai sebelumnya bukan tanaman yang masih berlangsung. Generator hanya memiliki tanggal awal sehingga pernyataan ongoing masih memerlukan pemeriksaan okupansi dari kalender. Jendela paparan memakai irisan okupansi dengan horizon dan tidak memindahkan tanggal semai ke awal horizon.

Tanaman yang melewati akhir horizon tetap ditandai berlangsung melewati horizon; horizon tidak diperpanjang. Hanya jendela paparan yang dipotong pada batas analisis. Hari tanpa tanaman yang dinyatakan tetap bagian horizon dan tidak otomatis diberi label bera atau tutupan tanah tertentu.

## 4. Iklim NASA dan indikator air

Pemilihan konteks POWER dilakukan secara eksplisit. Pada contoh Klaten, titik POWER Yogyakarta menjadi konteks regional bernama, bukan pengukuran cuaca pada piksel tanaman. Untuk lokasi baru, periksa dukungan masing-masing layer; jangan otomatis mengganti data lahan dengan titik contoh terdekat.

Untuk jendela `W = [mulai,akhir)`:

`P(W) = Σ PRECTOTCORR(t)`

`ETo(W) = Σ ETo_FAO56(t)`

`D(W) = Σ [PRECTOTCORR(t) − ETo_FAO56(t)]`

P dan ETo dalam mm; D mempertahankan tanda. Masing-masing total memerlukan seluruh hari valid untuk metrik itu. D memerlukan pasangan P dan ETo pada hari yang sama; jika tidak lengkap, D menjadi `null`. Keluaran menyertakan hari diharapkan, hari valid per metrik dan jumlah hari dengan guard operasional ETo. Suhu rata-rata menggunakan rerata T2M harian lengkap, dalam °C.

ETo yang dipakai berasal dari metode FAO56 yang sudah diperiksa dengan contoh numerik terbitan FAO. Akurasi lokalnya belum tervalidasi. Guard Rs/Rso 0,3–1 tetap merupakan asumsi operasional tambahan yang ditandai. EVPTRNS asli tetap fluks energi MJ/m²/hari dan tidak menggantikan ETo dalam mm.

**Invariansi penting:** pada lokasi, sumber, mode waktu dan horizon yang identik, total P/ETo/D seluruh horizon harus identik untuk existing dan kedua kandidat. Lingkungan tidak berubah karena nama tanaman diganti. Jendela okupansi tanaman dapat mempunyai paparan berbeda karena tanggal/durasi yang berbeda, tetapi selisih tersebut bukan konsumsi atau penghematan air tanaman. Hari jeda tetap masuk konteks seluruh horizon.

D belum memasukkan hujan efektif, limpasan, simpanan tanah, akar, Kc/fenologi, genangan, perkolasi, rembesan atau efisiensi irigasi. Tidak ada konversi D menjadi kebutuhan irigasi. Rentang ET musiman FAO disajikan per tanaman sebagai referensi kasar; rentang yang bertumpang tindih tidak menentukan strategi mana lebih hemat. Curah hujan tahunan ECOCROP tidak dikurangi dari ET satu musim.

### Mode waktu

| Mode | Makna |
|---|---|
| `historical_replay` | Kalender skenario ditempatkan pada tanggal historis yang memiliki data. Kalender dapat hipotetis; cuaca tetap data historis nyata. |
| `historical_analogue_not_forecast` | Kalender rencana dipetakan ke tahun-tahun historis yang cocok untuk mengeksplorasi variasi musim. Tidak menjadi prakiraan musim mendatang. |
| `recent_partial` | Jendela terbaru dengan cakupan per metrik yang eksplisit. Total yang belum lengkap tetap kosong. |

Untuk analog baseline 1991–2020, petakan bulan/tanggal endpoint dan offset tahun kalender rencana ke setiap anchor year referensi. Semua tanggal harus berada di baseline dan jumlah harinya harus sama dengan jendela target. Tahun dengan 29 Februari yang tidak dapat dipetakan, perbedaan panjang jendela atau lintasan keluar baseline dilewati dengan alasan. Tidak menghapus/menambahkan hari secara diam-diam. Jendela lintas tahun dapat memiliki kurang dari 30 tahun lengkap.

Hitung setiap jendela tahunan terlebih dahulu, lalu mean, median, p10 dan p90 dengan interpolasi linear type7. Distribusi D berasal dari D berpasangan setiap tahun; jangan mengurangkan p10 hujan dengan p10 ETo atau menjumlahkan persentil bulanan. Laporkan jumlah tahun lengkap per metrik dan tahun yang dilewati. Persentil tidak diterbitkan bila kurang dari dua jendela lengkap.

Kebijakan ini membuat analog tahun penuh 365 hari mempunyai 22 tahun referensi dan target 366 hari mempunyai 8, sedangkan jendela Mei–Agustus mempunyai 30. Ini konsekuensi pemetaan durasi yang ketat, bukan berkurangnya data baseline sumber. Kohort dapat berbeda antarjendela. Distribusi terpisah harus menunjukkan daftar/jumlah anchor year; setiap selisih numerik antarjendela wajib dihitung ulang pada irisan tahun berpasangan yang lengkap untuk keduanya. Jangan mengurangkan mean dari kohort berbeda atau menyebut selisih itu efek kausal tanaman.

Rentang durasi tidak disembunyikan menjadi durasi tengah. Ringkasan iklim pada endpoint panen awal/akhir, bila ditampilkan, adalah dua jendela alternatif. Keduanya bukan batas universal seluruh nilai D atau rerata suhu pada semua durasi di antaranya.

## 5. Pemeriksaan agronomi dan sumber lain

| Pemeriksaan | Hasil yang didukung | Batas kesimpulan |
|---|---|---|
| pH | Bandingkan nilai serta ketidakpastian pada kedalaman tertentu dengan rentang optimum spesies historis ECOCROP | Mean di dalam optimum tidak membuktikan kesesuaian lahan. Q05–Q95 yang melintasi batas ditampilkan sebagai ketidakpastian. Di luar optimum tidak berarti tanaman pasti gagal. |
| Suhu | T2M historis pada jendela berisi tanaman, dengan konteks optimum spesies | Optimum bukan ambang Tmax, sterilitas, kematian atau kehilangan hasil varietas. |
| Padi → tanaman upland | Minta sistem/rezim air padi terlebih dahulu, lalu tinjau drainase, kontrol air dan pengelolaan tanah bila transisi dari sawah tergenang relevan | Tanam langsung/pindah tanam tidak menetapkan ekosistem sawah atau gogo. Rezim air/drainase yang belum diketahui menghasilkan kebutuhan input; laporan drainase baik saja bukan validasi lahan. |
| Kedelai/legum | Jelaskan potensi mekanisme fiksasi N beserta kebutuhan nodulasi, inokulasi, residu dan neraca hara | Kredit N dan penghematan pupuk tetap kosong. |
| Pergantian tanaman/hama | Periksa organisme lokal, host range dan riwayat bila tersedia | Nama tanaman yang berbeda tidak membuktikan pemutusan siklus hama. |
| GAEZ | Kategori model 2001–2020 pada sel yang benar-benar diekstrak, dengan rezim pengelolaan terpisah | Bukan skor 0–100, kondisi live, hasil panen atau pengganti pengamatan lahan. Jangan memilih rezim irigasi tanpa input. |
| SoilGrids/retensi air | Nilai prediksi, kedalaman, unit dan ketidakpastian dari sel yang memuat titik | Bukan uji laboratorium; nol ambigu tidak dinilai. Tidak merata-ratakan pH antar-kedalaman atau menganggap kuantil sebagai variasi antarpetak. |
| Terrain | Konteks permukaan/lereng dengan sumber DSM | Tidak menetapkan ambang erosi atau risiko banjir tanpa model serta validasi. |

Riwayat MODIS memakai tanggal pengamatan piksel yang dipilih dan hanya `good_strict`. Ringkasan menyimpan jumlah pengamatan baik/marginal/dikecualikan dan gap. Tidak ada kesimpulan spesies, kalender tanam, masa bera, stres tanaman atau manfaat kausal strategi dari seri yang jarang dan bercampur tutupan lahan.

Audit tambahan sebelum backend memperoleh grid tanah native dan mask sumber; lihat [audit data terbaru](../outputs/audit-kelengkapan-data-fieldshift.md). Fixture tahap 2 tetap mereproduksi snapshot WCS awal. Pada primary, pH mean tetap 5,8, tetapi Q95 pada anchor native 7,9 berbeda dari Q95 pusat sel WCS lama 7,8. Dukungannya berbeda; jangan memindahkan indeks row/column, mengganti nilai tanpa provenance, atau menyebut keduanya pengukuran petak yang sama. Implementasi berikutnya memakai layer native secara eksplisit dengan konvensi yang sama untuk lokasi serta sumber lainnya.

## 6. Contoh demonstrasi yang dapat diulang

[Fixture](../specs/fixtures/rotation-demo.json) memakai horizon historis 1 Januari–31 Desember 2025 pada contoh Klaten, dengan konteks POWER regional. Semua riwayat/kalender/produksi fixture adalah asumsi sintetis berlabel, bukan data petani. Data lingkungan asli tidak diubah dan template petani sumber tetap kosong.

Contoh mengunci tanaman pertama padi dan mencoba slot kedua padi/jagung/kedelai. Dua tanggal semai, tanam langsung, durasi 120/100/90 hari dan jeda persiapan 14 hari dipilih secara eksplisit untuk latihan metode. Rezim air padi tetap belum diketahui; tanam langsung tidak dianggap sawah tergenang. Angka tersebut tidak mengkalibrasi varietas lokal atau menetapkan tanggal anjuran petani.

| Strategi | Urutan pada fixture | Pemeriksaan yang dijalankan |
|---|---|---|
| Existing | Padi → padi | Kalender, konteks iklim sepanjang horizon dan per okupansi, referensi serta data yang kurang |
| Kandidat 1 | Padi → jagung | Pemeriksaan yang sama, ditambah tinjauan transisi padi–upland |
| Kandidat 2 | Padi → kedelai | Pemeriksaan yang sama, ditambah mekanisme legum bersyarat |

Contoh numerik untuk memeriksa metode P/ETo/D:

| Jendela historis | Hari | P (mm) | ETo (mm) | P−ETo (mm) |
|---|---:|---:|---:|---:|
| 1 Mei–1 September 2023, akhir eksklusif | 123 | 306,50 | 480,9418 | −174,4418 |
| 1 Mei–1 September 2025, akhir eksklusif | 123 | 733,79 | 441,2481 | +292,5419 |
| 1–6 November 2026, akhir eksklusif | 5 | 25,09 | tidak tersedia: hanya 2/5 hari valid | tidak tersedia |

Perbedaan antarjendela tersebut menunjukkan variasi paparan historis, bukan kebutuhan irigasi atau perbandingan keberhasilan tanaman. Hasil latihan tersedia di [rotation-method-demo.md](../outputs/rotation-method-demo.md) dan [JSON lengkap](../outputs/rotation-method-demo.json).

## 7. Verifikasi dan batas implementasi

Modul referensi di `scripts/method/` digunakan untuk memeriksa logika tanggal, generator dan agregasi dari data yang tersedia. Modul ini belum merupakan backend, layanan pembaruan data, UI atau model rekomendasi produksi.

Verifikasi mencakup generator nol/satu/dua alternatif, kandidat duplikat, prefix terkunci, tanggal di luar horizon, asal durasi, nursery, jeda null/nol, rentang konflik, pergantian tahun/kabisat, total parsial, invariansi lingkungan, analog baseline, gap MODIS dan sumber yang tetap tidak berubah. Contoh numerik nyata dan kasus kegagalan diperiksa sebelum tahap 2 ditutup.

Jalankan ulang seluruh pemeriksaan dan buat ulang laporan dengan `py -3.11 scripts/method/verify_rotation_method.py` dari folder proyek. Hasil tersimpan dalam [laporan verifikasi](../outputs/rotation-method-verification.json). Pengujian menggunakan Python standard library, tanpa dependency baru. Review independen juga memeriksa angka dari CSV, pemilihan sel, asal sumber, status parsial dan label asumsi. Pemeriksaan ini memvalidasi metode referensi dan integrasi contoh; belum menguji akurasi agronomi lokal.

Selesai tahap 2 berarti metode, kontrak, latihan tiga strategi dan kasus batas dapat ditinjau serta diperiksa ulang. Langkah berikutnya adalah tahap 3: menghubungkan metode dengan mesin data/backend, pemeriksaan cakupan spasial dan respons analisis sesuai MVP. Validasi lahan lokal tetap terbuka.

## Rujukan

- [Referensi tanaman](../data/prepared/agronomy/crop-reference.json), [bukti dan URL sumber](../data/prepared/agronomy/source-evidence.json), [aturan agronomi awal](../data/prepared/agronomy/agronomy-rules.json).
- [Metode dan provenance iklim](../data/prepared/climate/manifest.json), [data harian](../data/prepared/climate/daily.csv), [pemeriksaan FAO56](../data/prepared/climate/method-validation.json).
- [QA vegetasi](../data/prepared/vegetation/summary.json) dan [metadata tanah/terrain](../data/prepared/soil-terrain/manifest.json).
