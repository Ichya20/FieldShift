# Audit kelengkapan data FieldShift sebelum backend

8 November 2026 · Yogyakarta–Klaten · padi, jagung, kedelai.

Pengguna mengonfirmasi belum ada data lahan/petani dan meminta memakai sumber publik yang tersedia. Audit ini melengkapi data publik dan definisi input untuk contoh MVP serta persiapan pengembangan berikutnya. Backend belum dibuat. Kesiapan konteks publik berbeda dari kelengkapan observasi sebuah petak.

## Data yang telah dilengkapi

| Bagian | Tambahan dan pemeriksaan | Penggunaan yang didukung |
|---|---|---|
| Iklim NASA POWER | Baseline 1991–2020 dan riwayat 2021–2025 diperiksa per parameter; periode terbaru diminta ulang ke API resmi. | Paparan iklim historis regional. Data terbaru tetap mengikuti batas publikasi sumber, bukan diisi dari prakiraan. |
| Vegetasi NASA | 304 komposit tambahan: 38 Terra 2026 dan 266 Aqua 2021–2026 untuk dua piksel Klaten. Sebanyak 69 strict-good, 53 marginal dan 182 dikecualikan. | Konteks vegetasi tambahan. Sensor tetap terpisah, bulan berawan tidak diinterpolasi dan spesies tidak ditebak. |
| Tanah dan topografi | 180 raster native ISRIC diperoleh. Dari 1.056 nol yang sebelumnya belum jelas, 340 terbukti nol kuantil prediksi valid dan 716 merupakan nodata sumber; empat sentinel negatif juga nodata. Semua 180 nilai per titik contoh tersedia. | Memisahkan nol prediksi dari nodata tanpa imputasi; tetap berupa prediksi model, bukan hasil uji tanah. Retensi air mempertahankan label sumber pre-release. |
| Agronomi Indonesia | Bukti resmi Kementan/BRMP/PVT tentang durasi varietas dan sistem budidaya padi. Katalog Anjasmoro menyatakan 82–93 hari setelah tanam; descriptor alternatif dipertahankan. | Referensi varietas dengan asal durasi yang jelas; varietas petani tetap belum diketahui. |
| Kontrak input | 91 definisi awal diperjelas dan 28 ditambahkan: 119 field bertipe, satuan, struktur catatan dan keterkaitan ke seluruh 12 aturan. | Persiapan formulir/backend tanpa tipe generik, validasi lintang negatif yang salah, atau bobot prioritas rekaan. |
| Referensi air tanaman | FAO56 Tabel 12/22: Kc, tinggi tanaman referensi, akar maksimum dan fraksi deplesi untuk ketiga tanaman. Nilai kelompok dan catatan khusus padi disimpan. | Bahan penelitian model air berikutnya; belum mengaktifkan kebutuhan irigasi atau penghematan air lokal. |
| Cuaca BMKG | Snapshot resmi kelurahan Klaten: 18 waktu prakiraan per tiga jam, dengan suhu, kelembapan, angin, awan, waktu produksi dan waktu berlaku. | Konteks cuaca administratif jangka pendek yang harus diperbarui sebelum digunakan. Bukan prakiraan musim dan bukan observasi pada piksel contoh. |

Data awal di `data/prepared/` dipertahankan utuh. Semua tambahan, sumber asli, waktu akses, hash, metode serta QA berada di [data/supplemental](../data/supplemental/README.md). Kontrak bertipe terbaru ada di [farm-input-contract.json](../data/supplemental/agronomy/farm-input-contract.json); nilai aktual pada template tetap kosong karena memang belum ada observasi petani.

**Perbedaan dukungan tanah yang perlu diperhatikan:** pH mean primary tetap 5,8, tetapi Q95 pada sel native yang memuat koordinat anchor adalah 7,9. Pusat sel WCS lama pada contoh tahap 2 mempunyai Q95 7,8. Koordinat pusat dan gridnya berbeda, sehingga indeks row/column tidak boleh disalin antar-grid. Hasil tahap 2 tetap dapat direproduksi dengan snapshot sumber lamanya; backend berikutnya harus memilih layer native beserta dukungan dan provenance yang benar.

## Nilai kosong yang tetap mempunyai alasan

- POWER terbaru: meteorologi/hujan terakhir valid 5 November 2026; radiasi dan ETo 2 November. Permintaan ulang tidak menyediakan tanggal setelah batas tersebut. Baseline dan riwayat perbandingan tetap lengkap.
- MODIS: awan, kualitas pengamatan dan piksel campuran tetap membatasi seri. Pada 2021–2025, setidaknya satu sensor mempunyai observasi baik pada 34/60 bulan di primary dan 35/60 bulan di pembanding; 26/25 bulan tetap tanpa observasi baik. Ini diagnostik ketersediaan, bukan penggabungan indeks antar-sensor. Rinciannya ada di [ringkasan lingkungan](../data/supplemental/environment/summary.json).
- SoilGrids: nodata sumber tidak dijadikan angka tanah. Pada dua titik contoh, 12 sifat × 5 kedalaman × 3 statistik sudah tersedia, termasuk lima nol kuantil cfvo yang terverifikasi per titik. Di bagian lain subset masih terdapat lubang mask sumber. Status tiap properti/kedalaman ada di [ringkasan tanah](../data/supplemental/soil-terrain/summary.json).
- BMKG: visibility yang tidak dilaporkan tetap kosong. Field `tp` disimpan pada sumber asli tetapi tidak diolah menjadi jumlah hujan karena unit dan interval akumulasinya belum dijelaskan dalam dokumentasi API yang tersimpan. Snapshot mempunyai waktu berlaku terakhir 10 November 2026 pukul 21.00 WIB; periksa ulang sebelum penggunaan operasional.
- Informasi petak nyata: batas/luas, rotasi dan tanggal aktual, varietas yang dipilih, sistem air/drainase, uji tanah, hama, pengelolaan, biaya serta hasil belum tersedia. Sumber wilayah atau nilai model tidak dipindahkan menjadi laporan petani.
- Validasi agronomi lokal, keuntungan, hasil prediksi, kredit nitrogen dan penghematan air belum tersedia. Prakiraan musim operasional dan misi NASA tambahan di luar MVP tetap tercatat sebagai kebutuhan pengembangan terpisah.

Daftar kebutuhan dan status setiap bagian tersimpan di [readiness-audit.json](../data/supplemental/readiness-audit.json), dengan rincian input di [gap-register.json](../data/supplemental/agronomy/gap-register.json). Tidak ada klaim bahwa seluruh kemungkinan data atau informasi lahan nyata sudah lengkap.

## Pemeriksaan dan paket penggunaan berikutnya

Pemeriksaan mencakup kelengkapan baseline/riwayat per parameter, kecocokan raster asli, QA dan skala indeks, waktu UTC/WIB, sumber referensi, tipe/satuan input, serta checksum snapshot awal dan tambahan. Skema Draft 2020-12 dan 19 kasus batas telah lulus; metode tahap 2 mempunyai 55 pengujian yang lulus. Review independen juga memeriksa interpretasi FAO56 dan BMKG.

- [Laporan validasi data tambahan](../data/supplemental/validation-report.json).
- [Manifest SHA-256 data tambahan](../data/supplemental/file-manifest.json).
- [Paket lengkap versi 2](fieldshift-data-publik-v2-2026-11-08.zip), berisi snapshot awal, tambahan, spesifikasi, metode dan skrip; dependency vendor tidak disertakan.
- [Verifikasi ZIP/CRC/SHA-256](data-package-verification.json) dan [checksum paket](fieldshift-data-publik-v2-2026-11-08.zip.sha256), disimpan sebagai sidecar agar tidak terjadi hash arsip yang merujuk dirinya sendiri.

Reproduksi audit tanpa unduhan: `py -3.11 scripts/data/audit_data_completeness.py`. Pengambilan/pengolahan sumber ada di README masing-masing modul; refresh dilakukan saat diperlukan, tanpa proses latar otomatis. Data publik untuk alur contoh MVP tersedia dengan batas kualitas yang dinyatakan; rekomendasi lahan nyata masih memerlukan data dan validasi lapangan.
