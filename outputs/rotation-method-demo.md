# Latihan metode rotasi FieldShift

Versi 0.1.0 · 8 November 2026. **Seluruh informasi petani, urutan dan kalender di contoh ini adalah asumsi sintetis.** Lingkungan menggunakan data nyata yang sudah disiapkan. Ini replay historis 2025, bukan prediksi atau rekomendasi lahan.

## Tiga strategi terisi

Horizon bersama 1 Januari 2025–1 Januari 2026 (akhir eksklusif). Semai pertama 1 Januari dan kedua 1 Juni; tanam langsung, durasi elapsed 120/100/90 hari untuk padi/jagung/kedelai dan jeda 14 hari merupakan asumsi latihan. Hari panen masih menempati petak. Semua strategi lolos pemeriksaan konflik kalender untuk isian tersebut; status agronomi tetap parsial.

Tabel berikut menunjukkan **paparan lingkungan pada okupansi tanaman kedua**, bukan kebutuhan air tanaman:

| Strategi | Urutan | Panen kedua (asumsi) | Hari okupansi | Hujan (mm) | ETo referensi (mm) | P−ETo (mm) |
|---|---|---|---:|---:|---:|---:|
| existing | padi → padi | 2025-09-29 | 121 | 472,1 | 468,5152 | 3,5848 |
| candidate_1 | padi → jagung | 2025-09-09 | 101 | 329,49 | 381,2903 | -51,8003 |
| candidate_2 | padi → kedelai | 2025-08-30 | 91 | 308,21 | 333,2444 | -25,0344 |

Konteks POWER adalah regional, bukan pengukuran cuaca pada piksel Klaten. Selisih pada jendela tanaman di atas berasal dari panjang okupansi yang diasumsikan, bukan bukti tanaman lebih hemat air.

**Sepanjang horizon 365 hari yang sama, ketiganya identik:** hujan 2964,05 mm; ETo 1372,0954 mm; P−ETo 1591,9546 mm. Hari jeda tidak dihapus dari horizon.

## Bukti dan informasi yang kurang

- Sel SoilGrids yang memuat titik primary adalah row 4, col 6; prediksi pH kedalaman 0–5 cm mean 5,8, q05 4,2, q95 7,8. Mean berada dalam referensi ketiga tanaman, tetapi rentang prediksi melewati batas optimum. Ini bukan bukti kesesuaian zona akar atau uji laboratorium.
- Rezim air padi, drainase, kontrol air dan pengelolaan belum diketahui. Tanam langsung tidak menetapkan sawah tergenang atau gogo.
- Potensi mekanisme legum dan pergantian tanaman perlu bukti nodulasi, residu, neraca hara, organisme hama dan host range lokal.
- GAEZ tetap kategori model historis dengan rezim terpisah. MODIS tetap konteks vegetasi piksel campuran dengan QA/gap; bukan identifikasi tanaman.
- Ranking, skor, hasil, keuntungan, kredit N dan penghematan/kebutuhan irigasi tetap kosong.

Analog historis disimpan terpisah, bukan forecast. Horizon 365 hari ini memiliki 22 tahun referensi lengkap karena kebijakan tidak menambah/menghapus 29 Februari. Daftar tahun dan alasan yang dilewati ada di JSON. Perbandingan selisih antarjendela harus memakai kohort berpasangan yang sama.

## Pemeriksaan

Tiga strategi berbeda, horizon sama, konflik kalender, invariansi lingkungan dan resolusi sumber temuan diperiksa. Seluruh 390 berkas data prepared tetap cocok dengan manifest SHA-256; template petani sumber tetap kosong.

Reproduksi: `py -3.11 scripts/method/build_rotation_demo.py`. Hasil lengkap: [rotation-method-demo.json](rotation-method-demo.json). Metode: [rotation-method.md](../docs/rotation-method.md). Fixture: [rotation-demo.json](../specs/fixtures/rotation-demo.json).
