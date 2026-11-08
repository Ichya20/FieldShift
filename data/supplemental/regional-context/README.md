# Konteks cuaca regional BMKG

Snapshot resmi prakiraan cuaca kelurahan Klaten, Klaten Tengah. Lokasinya dipilih secara eksplisit sebagai konteks administratif dan tidak menggantikan data piksel contoh atau kondisi lahan. Suhu, kelembapan, angin dan awan tersedia per tiga jam dengan waktu produksi dan waktu berlaku. Snapshot harus diperbarui sebelum penggunaan operasional; prakiraan cuaca ini bukan prakiraan musim tanam.

Sumber asli disimpan di `sources/`, beserta URL, waktu unduh dan SHA-256 di `source-evidence.json`. `tp` dan visibility tidak dipakai dalam angka olahan: semantik jumlah hujan belum terverifikasi dan visibility null dari sumber. Tidak ada pengisian nilai kosong atau penggabungan dengan riwayat NASA.

Unduh: `pwsh -File scripts/data/supplemental_regional/fetch_sources.ps1` (tambahkan `-Refresh` untuk data baru). Validasi/olah: `py -3.11 scripts/data/supplemental_regional/prepare_context.py`.
