# Prompt revisi Stitch — material, lighting, dan color grading

Tempel prompt ini pada desain Stitch yang sudah ada. Ini revisi visual terarah, bukan permintaan menghasilkan ulang seluruh halaman. Arahan material, pencahayaan dan warna di bawah diprioritaskan terhadap prompt sebelumnya.

---

Pertahankan komposisi landing page FieldShift, urutan bagian, navigasi, copy Indonesia, font Libre Franklin, fungsi eksplorasi dan responsivitas yang sudah terbentuk. **Revisi kualitas diorama 3D, shading, dan color grading-nya.** Jangan mengganti layout yang sudah baik atau menambah ornamen untuk menutupi masalah render.

Target visual: **diorama agrikultur dengan material yang dapat dibedakan, pencahayaan daylight yang konsisten, dan grading netral**. Bentuk tanaman, tekstur tanah, dan bayangan harus menjelaskan objek. Hindari tampilan mainan plastik, clay render pastel, isometric clip art, atau gambar yang seluruh permukaannya dipoles sama.

## 1. Kunci pencahayaan, bukan menambah efek

- Gunakan satu cahaya daylight utama dari **kiri atas agak depan**; arah bayangan ke **kanan belakang** konsisten untuk tanaman, penampang tanah dan alas. Jangan membuat tiap objek memiliki arah cahaya sendiri.
- Bidang atas yang menerima cahaya lebih terang dari sisi tanah yang membelakangi cahaya. Perbedaan terang-gelap harus masih terbaca saat gambar dilihat dalam grayscale.
- Cahaya pengisi hanya menjaga detail sisi teduh; jangan mengangkat semuanya hingga volume terlihat rata. Shadow tidak hitam pekat dan tidak berwarna hijau brand.
- Highlight lembut, detail tetap terbaca. Tidak ada permukaan putih terbakar, bloom, rim light berlebihan, lens flare, sinar dekoratif atau efek HDR.
- Pertahankan kamera tiga perempat dan ukuran objek agar perbaikan sebelum–sesudah bisa dibandingkan. Objek utama tajam pada keseluruhan kedalamannya; hindari blur tilt-shift yang membuat lahan terlihat seperti miniatur mainan.

## 2. Buat objek benar-benar menapak

- Tanaman tertanam di tanah. Ada bayangan kontak kecil pada pangkal batang dan pertemuan daun, sesuai posisi cahaya.
- Bayangan blok tanah paling rapat di area kontak dengan ground plane, kemudian melunak menjauh. Jangan membuat oval shadow terpisah yang memberi kesan objek melayang.
- Ambient occlusion cukup di celah/pertemuan bentuk. Hilangkan halo hitam tebal di seluruh tepi dan outline gelap palsu.
- Natural shading berada pada objek 3D. Jangan menambah drop-shadow besar pada semua panel UI atau radial gradient di belakang objek sebagai pengganti pencahayaan.

## 3. Bedakan material secara nyata

**Tanah:** matte dan berpori, dengan gumpalan kecil serta variasi ukuran butiran yang masuk akal. Penampang memiliki variasi lapisan yang halus dan tidak seragam sempurna. Cokelat tanah tetap memiliki warna pada sisi teduh. Hindari lapisan seperti kue, bevel menggelembung, permukaan licin, atau retakan besar yang dibuat sekadar hiasan.

**Daun dan batang:** bidang daun tipis, orientasi dan tinggi bervariasi sedikit, siluet tanaman tetap terbaca. Daun memiliki highlight tipis dan tidak merata; sedikit tembus cahaya hanya pada bagian yang menghadap cahaya. Bukan daun transparan, karet, lilin, atau plastik mengilap. Jangan membuat semua tanaman identik seperti stempel atau menambahkan noise acak pada setiap daun.

**Permukaan air jika memang sudah ada pada ilustrasi padi:** refleksi lebih terarah daripada tanah, warna dari lingkungan, tanpa warna biru neon atau efek kaca tebal. Jangan menambahkan air sebagai default untuk semua metode padi atau menyiratkan kondisi irigasi yang diketahui.

**Detail:** utamakan siluet, perbedaan material, dan bayangan sebelum menambah detail mikro. Tidak perlu grain/filter di seluruh halaman. Pada ukuran mobile, tanah dan tanaman harus tetap terbaca tanpa berubah menjadi tekstur bising.

## 4. Grade render secara netral, biarkan UI tetap bersih

Palet UI yang dipakai:

| Peran | Warna |
|---|---|
| Kanvas netral | `#F5F5F2` |
| Panel | `#FFFFFF` |
| Teks utama | `#202820` |
| Teks sekunder | `#536055` |
| Aksen/tombol utama | `#274C38` dengan teks putih |

Gunakan warna tersebut sebagai token UI, bukan filter warna pada objek. Aksen hijau dipakai pada tindakan utama dan informasi yang relevan; jangan mewarnai semua heading, panel, ikon, dan bayangan menjadi hijau. Warna status tetap dapat dibedakan dan selalu memiliki label teks.

Untuk material diorama, gunakan referensi warna dasar **hijau daun/zaitun, cokelat tanah, dan sedikit kuning jerami pada bagian yang relevan**. Warna tanaman tidak harus sama dengan warna tombol. Referensi material seperti olive `#647347`, deep leaf `#3F5636`, earth `#756154`, dan straw `#B39A60` adalah panduan warna dasar, bukan warna datar yang ditempel ke semua sisi; cahaya tetap membentuk volumenya.

White balance daylight netral. Hilangkan cast hijau atau kuning menyeluruh; putih UI harus tetap putih. Beri rentang terang-gelap yang cukup, highlight yang turun secara lembut, dan detail pada shadow. Jangan sekadar menurunkan saturasi sampai semua warna kusam/abu-abu.

Hindari pastel mint yang mendominasi, hijau neon, tanah oranye, teal–orange, sepia, black crush, washed-out haze, vignette, oversharpening, dan LUT sinematik berat. **Color grading hanya diterapkan pada render**, bukan filter CSS di seluruh halaman yang ikut mengubah teks, peta, warna status atau tombol. Jangan memakai layer tint untuk menyatukan aset yang pencahayaannya berbeda; selaraskan sumber cahaya dan materialnya.

## 5. Pertahankan disiplin desain sebelumnya

Tetap gunakan satu keluarga Libre Franklin, hierarki teks yang sudah baik, dan judul pendek. Tidak ada kata dekoratif raksasa, outline text, label kapital renggang, badge “AI-powered”, eyebrow tambahan, ikon melayang, atau tipografi baru untuk memberi kesan premium.

Tetap ada satu diorama utama. Jangan menambah partikel, grain overlay, glow, kartu kaca, animasi kamera panjang, maupun ilustrasi kecil tambahan. Kualitas harus datang dari bentuk, material, pencahayaan dan komposisi.

Perubahan fase tanaman mempertahankan posisi kamera, cahaya dan grade. Jangan memberi alternatif tertentu cahaya lebih cerah/hijau lebih sehat sehingga seolah-olah menjadi pemenang. Pada mobile atau reduced motion, gunakan render statis dengan kualitas cahaya dan grade yang sama. Semua kontrol, teks, dan fallback tetap terbaca.

Pertahankan caption **“Ilustrasi skenario”**. Peningkatan realisme visual tidak mengubahnya menjadi pengukuran lahan atau prediksi. Sumber data, kalender asumsi, status analisis sebagian, dan batas kemampuan produk tetap seperti desain sebelumnya.

## 6. Periksa hasil dengan bukti visual

Tampilkan sebelum–sesudah pada komposisi dan kamera yang sama, versi desktop 1440 px, mobile 390 px, serta close-up diorama. Perbaikan harus tampak pada hasil, bukan hanya pada deskripsi perubahan.

Periksa satu per satu:

1. Dalam grayscale, tanaman, bidang atas tanah, penampang, dan latar masih terpisah.
2. Arah cahaya serta bayangan konsisten; tanaman berakar dan blok tanah tidak melayang.
3. Tanah terbaca matte; daun punya respons cahaya sendiri, tanpa tampilan plastik yang sama di seluruh objek.
4. Putih UI netral, hijau tanaman tidak neon, cokelat tanah tidak menjadi oranye; teks tidak ikut terkena color grade.
5. Detail tetap terbaca saat diorama diperkecil ke ukuran mobile; tidak ada halo, crop terpotong, atau blur berlebihan.
6. Teks dan kontrol tetap memenuhi kontras AA; tidak ada elemen baru tanpa fungsi.

Jika kontrol material/renderer tidak tersedia di Stitch, hasilkan visual statis yang mendekati arahan tersebut dan tandai bagian yang perlu aset 3D khusus saat implementasi. Jangan mengklaim pencahayaan fisik atau interaksi WebGL sudah diimplementasikan hanya karena mockup menampilkan objek 3D.

---

Catatan untuk handoff: prompt ini berdasarkan panduan warna/imagery dari skill `design-taste-frontend`, pencarian gaya 3D dan aksesibilitas `ui-ux-pro-max`, serta review independen material/pencahayaan. Nilai palet merupakan keputusan art direction FieldShift, bukan hasil pengukuran gambar atau preset renderer terverifikasi. Belum ada screenshot hasil Stitch yang diinspeksi pada revisi ini; checklist di atas merupakan sasaran review, bukan klaim sudah lulus.
