# FieldShift — tambahan data sebelum backend

Indeks terbaru adalah [readiness-audit.json](readiness-audit.json). Paket ini menambah sumber numerik, verifikasi dan definisi input tanpa mengubah snapshot `data/prepared`. Kelengkapan publik untuk contoh MVP berbeda dari kelengkapan informasi lahan nyata. Pengguna mengonfirmasi belum ada data petani.

- `environment/`: tambahan Terra/Aqua dan pemeriksaan batas publikasi POWER.
- `soil-terrain/`: verifikasi raster asli dan perbedaan nol prediksi dengan nodata.
- `agronomy/`: descriptor resmi, kontrak input bertipe, satuan, skema dan kebutuhan 12 aturan.
- `regional-context/`: snapshot prakiraan cuaca BMKG yang punya masa berlaku.
- `crop-water/`: FAO56 Tabel 12/22 untuk riset model air berikutnya; bukan kalibrasi lokal.

Sebelum menggunakan data, ikuti `use_policy` pada indeks. Sumber, waktu, QA dan hash tersimpan per modul. Nilai publik tidak dipindahkan ke kolom observasi petani. Tidak ada backend atau proses refresh otomatis.

Audit offline dan kemas ulang: `py -3.11 scripts/data/audit_data_completeness.py`. Skrip mengharuskan semua modul tambahan telah selesai; tidak mengunduh data.
