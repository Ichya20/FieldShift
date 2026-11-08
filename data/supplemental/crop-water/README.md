# Referensi air tanaman untuk pengembangan berikutnya

FAO56 Tabel 12 dan 22 menyediakan referensi generik koefisien tanaman, kedalaman akar maksimum dan fraksi deplesi untuk padi, jagung biji dan kedelai. Setiap nilai ditautkan ke baris sumber. Nilai awal jagung/kedelai berasal dari baris kelompok tanaman; bukan hasil kalibrasi lokal. Footnote padi memakai 0,20 dari kondisi jenuh dan tidak disamakan dengan deplesi tanaman upland. Rentang dipertahankan.

Paket ini belum mengaktifkan perhitungan ET tanaman atau irigasi dalam MVP. Tanggal fase, kondisi awal air tanah, hujan efektif, pengelolaan padi, alokasi air dan validasi lokal tetap diperlukan. Sumber primer: [FAO56 Bab 6](https://www.fao.org/4/x0490e/x0490e0b.htm) dan [Bab 8](https://www.fao.org/4/x0490e/x0490e0e.htm).

Unduh/katalog: `pwsh -File scripts/data/supplemental_regional/fetch_crop_water.ps1`. Validasi/olah: `py -3.11 scripts/data/supplemental_regional/prepare_crop_water.py`.
