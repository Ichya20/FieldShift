# Roadmap FieldShift

Diperbarui 8 November 2026 (Asia/Jakarta). Pengerjaan mengikuti urutan tahap; tiap tahap menghasilkan bahan konkret untuk tahap sesudahnya.

| Tahap | Status | Hasil utama | Syarat selesai |
|---|---|---|---|
| 0. Fondasi data | Selesai untuk area contoh | Dataset publik mentah/terolah, sumber, QA dan skrip | Pemeriksaan data lulus; cakupan dan gap dicatat. Input petani/validasi lahan tetap kebutuhan terpisah. |
| 1. Tetapkan MVP | Selesai | [Spesifikasi MVP](mvp.md): cakupan, alur, input/output, layar dan kriteria penerimaan | Sesuai data yang tersedia dan arah challenge; pilihan online dikonfirmasi pengguna. |
| 2. Metode analisis rotasi | Selesai sebagai metode referensi | [Metode dan batas hasil](rotation-method.md), kontrak 12 pemeriksaan dan [latihan tiga strategi](../outputs/rotation-method-demo.md) | Generator, kalender, agregasi dan kasus batas diperiksa. Asumsi kalender dibedakan dari lingkungan nyata; validasi agronomi lokal tetap belum dilakukan. |
| 2a. Audit dan pengayaan data sebelum backend | Selesai untuk konteks publik contoh MVP | [Audit terbaru](../outputs/audit-kelengkapan-data-fieldshift.md), sumber numerik tambahan, klarifikasi nol tanah dan kontrak 119 input | Seluruh kebutuhan publik inti tersedia dengan QA/mask/latensi eksplisit. Data aktual lahan belum ada; sumber publik tidak diubah menjadi observasi petani. |
| 3. Mesin data/backend | Selesai untuk MVP lokal | [API FastAPI](../backend/README.md), konteks enam layer, generator/kalender dan 12 pemeriksaan | 134 tes metode/backend dan 5 pemeriksaan HTTP lulus; 916 hash sumber terverifikasi. Input parsial, konflik, cakupan dan null diperiksa. |
| 4. Antarmuka | Brief desain siap; implementasi belum dimulai | [design.md](../design.md) dan [deskripsi Stitch](stitch-project-description.md); sasaran peta/kondisi, profil/skenario dan perbandingan tiga strategi | Alur utama bekerja di HP/laptop, dapat diakses dan memperlihatkan kualitas/asal data. |
| 5. Uji dan validasi | Belum dimulai | Verifikasi fungsi, angka, geografi, penjelasan, dan tinjauan agronomi lokal | Temuan yang mengubah kesimpulan diperbaiki. Bagian yang belum ditinjau lokal tetap berstatus belum tervalidasi. |
| 6. Demo challenge | Belum dimulai | Contoh penggunaan lengkap, narasi kontribusi NASA dan materi demo | Demonstrasi dapat diulang; contoh/asumsi, sumber, keterbatasan dan status model disampaikan jelas. |

Versi pertama adalah web online. MVP menggunakan padi, jagung dan kedelai pada area contoh Yogyakarta–Klaten, dengan cakupan numerik per layer sesuai spesifikasi.

Tahap 3 telah diimplementasikan berdasarkan instruksi pengguna "baik lanjut ke tahap be." Backend membaca data lokal tanpa menyimpan input petani. [Request demo](../outputs/backend-demo-request.json), [hasil](../outputs/backend-demo-response.json), [OpenAPI](../outputs/backend-openapi.json) dan [verifikasi](../outputs/backend-verification.json) dapat ditinjau ulang. Hasil tetap parsial, tanpa ranking/manfaat numerik rekaan dan tanpa validasi agronomi lokal. Server uji HTTP sudah dihentikan. Tahap berikutnya adalah **tahap 4 antarmuka**, yang belum dimulai; hosting belum dilakukan.

Tahap 2 menghasilkan metode referensi versi 0.1.0 dan demonstrasi historis 2025 memakai kalender sintetis berlabel. Hasil ketiga strategi tetap parsial dan tidak menghasilkan ranking/manfaat numerik yang belum didukung. [Laporan verifikasi](../outputs/rotation-method-verification.json) memuat pengujian, resolusi sumber dan pemeriksaan hash data. Modul latihan belum merupakan backend atau UI.

Setelah tahap 2, pengguna meminta kelengkapan data sebelum backend dan mengonfirmasi belum ada data lahan nyata. Pengayaan publik tersimpan terpisah di `data/supplemental/`: 304 komposit Terra/Aqua, pemeriksaan POWER terbaru, 180 raster native tanah, referensi agronomi resmi, kontrak bertipe 119 field, referensi FAO56 untuk model air berikutnya dan snapshot cuaca BMKG yang terbatas masa berlaku. [Indeks kesiapan terbaru](../data/supplemental/readiness-audit.json) menjadi rujukan tambahan terhadap snapshot prepared awal. Kesiapan ini mencakup contoh MVP, bukan klaim seluruh gap observasi lahan atau validasi lokal sudah selesai.

Publikasi/hosting tidak dilakukan pada tahap spesifikasi. Detail deployment ditentukan setelah prototipe dan demonstrasinya tersedia untuk ditinjau.
