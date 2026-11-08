"""Build the portable data package after all preparation and validation finish."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/prepared"
OUTPUT = ROOT / "outputs"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main():
    validation = read(DATA / "validation-report.json")
    assert validation["pass"], validation["errors"]
    climate = read(DATA / "climate/summary.json")
    soil = read(DATA / "soil-terrain/summary.json")
    vegetation = read(DATA / "vegetation/summary.json")
    agronomy = read(DATA / "agronomy/manifest.json")
    points = vegetation["points"]
    assert len(points) == 2, "Two rural demonstration pixel series are expected"
    assert all(p["n_composites"] == 115 for p in points), "Incomplete MODIS download"
    assert not vegetation["failed_batches"], vegetation["failed_batches"]
    features = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": climate["coordinate"]},
        "properties": {"id": "power_regional_yogyakarta", "role": "regional climate context", "verified_farm": False,
            "support": "Native meteorological grid tens of km, not a surveyed field", "point_landcover_2021": "built-up; not used as cropland vegetation sample"}},
        {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[110.54,-7.73],[110.56,-7.73],[110.56,-7.71],[110.54,-7.71],[110.54,-7.73]]]},
        "properties": {"id": "klaten_subset", "role": "soil, terrain and land-cover extraction extent", "verified_farm": False}}]
    for point in points:
        features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [point["longitude"], point["latitude"]]},
            "properties": {"id": point["id"], "role": point.get("sample_role", "demonstration vegetation pixel"),
                "verified_farm": False, "crop_species_verified": False, "support": "MODIS pixel nominal 250m; mixed historical land cover"}})
    write(DATA / "locations.geojson", {"type": "FeatureCollection", "features": features})
    readiness = {
        "prepared_date": "2026-11-08", "timezone": "Asia/Jakarta", "area": "Yogyakarta-Klaten example",
        "public_data_preparation_finished": True, "integrity_checks_pass": True,
        "available_modules": ["climate", "vegetation", "soil-terrain", "agronomy"],
        "application_implemented": False, "farm_boundary_verified": False,
        "rotation_recommendation_locally_validated": False, "economic_comparison_ready": False,
        "seasonal_forecast_available": False,
        "missing_data_policy": "Keep missing values/quality exclusions visible, do not interpolate silently or fabricate farm inputs",
        "remaining_requirements": ["Farmer boundary/area, actual rotation and dates, chosen cultivar, irrigation/drainage, priorities",
            "Local agronomic validation and calibration before field-specific advice",
            "Market, cost and yield inputs before economic comparisons",
            "Satellite QA gaps remain in optical history; crop species and planting dates are not established"],
        "module_summary_files": {name: f"{name}/summary.json" for name in ["climate", "vegetation", "soil-terrain", "agronomy"]}}
    write(DATA / "readiness.json", readiness)

    veg_lines = []
    for p in points:
        counts = p["quality_counts"]
        veg_lines.append(f"| {p['id']} | {p['n_composites']} | {counts.get('good_strict', 0)} | {counts.get('marginal_review', 0)} | {counts.get('excluded', 0)} | {p['months_with_primary_data']}/60 |")
    fmt = lambda value: f"{value:,}".replace(",", ".")
    report = f"""# Kesiapan data FieldShift

Disiapkan 8 November 2026 (Asia/Jakarta). Wilayah contoh Yogyakarta–Klaten; tanaman padi, jagung, kedelai.

**Pengumpulan dan penyiapan data publik inti selesai untuk prototipe area contoh.** Data mentah, data numerik terolah, sumber, metode, QA dan skrip reproduksi tersedia. Aplikasi belum dibuat. Rekomendasi spesifik lahan belum tervalidasi karena data lahan/petani belum tersedia.

## Data numerik yang tersedia

| Bagian | Cakupan nyata | Batas penggunaan |
|---|---|---|
| NASA POWER | {fmt(climate['records'])} baris tanggal; 12 parameter; 1991–2025 serta 2026 parsial. Baseline 1991–2020: {fmt(climate['baseline_days'])} hari / 360 bulan, tiap bulan kalender 30 tahun valid. | Konteks regional puluhan km. Nilai meteorologi terbaru valid 5 November 2026; radiasi dan ETo terakhir valid 2 November. Hari kosong setelah itu tetap kosong. |
| Air dari forcing iklim | ETo referensi FAO56 dan indikator P−ETo harian/bulanan. Persamaan dicek dengan contoh numerik FAO dan agregat diperiksa independen. | ETo referensi rumput; P−ETo bukan kebutuhan irigasi atau air tersedia pada akar. EVPTRNS asli tetap MJ/m²/hari. |
| MODIS vegetasi | Dua piksel pedesaan, masing-masing 115 komposit 2021–2025, NDVI/EVI, tanggal observasi dan flag kualitas. | Filter awan/QA wajib. Bulan tanpa komposit good tetap kosong; tidak diinterpolasi. Versi koleksi subset tidak diklaim bila API tidak menyebutkan. |
| SoilGrids | {soil['soil']['successful_rasters']} raster kecil: 12 sifat × 5 kedalaman (0–100 cm) × mean/persentil 5/persentil 95. pH, tekstur, karbon, total N, CEC, bulk density, coarse fragments dan retensi air. | Prediksi 250 m, bukan uji laboratorium. {fmt(soil['soil']['unresolved_zeros'])} sel bernilai nol belum terjelaskan dan dikecualikan; bukan nodata terkonfirmasi atau nol fisik. |
| Elevasi dan lereng | Copernicus DEM GLO-30; subset Klaten, proyeksi UTM49S 30m, lereng dalam derajat. | Sumber ini Copernicus DSM, bukan NASADEM. Kanopi/bangunan dapat memengaruhi permukaan. |
| Tutupan lahan | ESA WorldCover 2021; klasifikasi titik, subset dan footprint MODIS sebenarnya. | Tahun 2021, bukan kondisi live atau bukti tanaman tertentu. |
| Agronomi dan GAEZ | 3 profil tanaman, 9 aturan bersyarat, contoh varietas Indonesia, 12 ekstraksi titik GAEZ (dua titik × tiga tanaman × dua rezim). | GAEZ baseline 2001–2020/AGERA5/HIST, grid 5 arc-minute. Kode kategori mengikuti legend resmi, bukan skor 0–100, hasil panen atau rekomendasi petak. |

## Kualitas dan pemilihan sampel vegetasi

Titik awal Yogyakarta ternyata **built-up** pada WorldCover 2021; titik awal Klaten berupa **tree cover** dan lingkungan campuran. Seri pertanian dipindahkan ke dua footprint MODIS di area rural Klaten. Piksel utama sekitar 84,47% cropland dan tanpa built-up; pembanding sekitar 69,21% cropland. Keduanya tetap mixed pixel dan tidak membuktikan batas lahan atau spesies tanaman.

| Piksel | Komposit tersimpan | Good strict | Marginal | Dikecualikan | Bulan punya data good |
|---|---:|---:|---:|---:|---:|
{chr(10).join(veg_lines)}

Statistik bulanan utama memakai good strict saja. Marginal tersedia terpisah untuk peninjauan. Tanggal tanam/panen, fase tanaman, maupun masa lahan kosong tidak boleh disimpulkan otomatis dari seri yang jarang atau bercampur tutupan lahan.

## Data yang masih harus berasal dari petani atau validasi lokal

Batas/luas lahan, rotasi berjalan dan tanggal semai/tanam/panen, varietas, sumber/kapasitas irigasi dan drainase, riwayat tanah/hama/pengelolaan, sumber daya serta prioritas. Template 91 field dan tiga slot strategi tersedia dengan nilai kosong; varietas referensi bukan varietas yang telah dipilih petani.

Perbandingan pendapatan memerlukan harga jual, pembeli, biaya dan hasil panen yang relevan. Forecast musim operasional belum diambil. Model rotasi, kalibrasi varietas, nilai kredit nitrogen, perubahan kesehatan tanah dan peningkatan profit belum dihitung atau diklaim.

## Sumber tambahan

HLS, SMAP, GPM, ECOSTRESS, NASADEM dan GRACE tersimpan sebagai discovery/metadata pada audit awal, belum sebagai seri piksel ilmiah siap pakai. Status dan kebutuhan akses dicatat dalam `data/prepared/optional-sources.json`. Produk tambahan dapat dipilih sesuai kebutuhan; semua misi tersebut tidak wajib digunakan sekaligus. Tidak ada akun dibuat, integrasi Earth Engine dijalankan, atau arsip global diunduh.

## Struktur dan penggunaan

- `data/prepared/analysis-profile.json`: cakupan, aturan skala/waktu dan kebutuhan analisis.
- `data/prepared/climate/`: raw POWER, daily/monthly, baseline, kamus unit dan metode.
- `data/prepared/vegetation/`: raw MODIS, tabel komposit 16 hari + QA dan bulanan good-only.
- `data/prepared/soil-terrain/`: GeoTIFF, angka sel tanah, elevasi/lereng, WorldCover, footprint dan QA.
- `data/prepared/agronomy/`: referensi, bukti, GAEZ, template input dan strategi.
- `data/prepared/validation-report.json` dan `file-manifest.json`: pemeriksaan konsistensi dan SHA-256.
- `scripts/data/`: skrip data; dependency vendor lokal tidak dimasukkan ke ZIP.

Jalankan `py -3.11 scripts/data/validate_prepared_data.py` untuk pemeriksaan paket tanpa unduhan. Skrip per modul dan README menjelaskan reproduksi/unduhan masing-masing. Nilai numerik kosong tetap kosong. Setiap layer mempertahankan sumber, dukungan ruang, periode dan ketidakpastiannya saat digunakan bersama.

Sumber primer: [NASA POWER](https://power.larc.nasa.gov/docs/services/api/temporal/daily/), [ORNL DAAC MODIS](https://modis.ornl.gov/data/modis_webservice.html), [ISRIC SoilGrids](https://docs.isric.org/globaldata/soilgrids/), [FAO56](https://www.fao.org/4/x0490e/x0490e00.htm), [FAO GAEZ](https://gaez.fao.org/), [ESA WorldCover](https://esa-worldcover.org/). URL ekstraksi, waktu akses dan atribusi spesifik tersedia di manifest setiap modul.
"""
    OUTPUT.mkdir(exist_ok=True)
    (OUTPUT / "kesiapan-data-fieldshift.md").write_text(report, encoding="utf-8")
    (DATA / "README.md").write_text(report, encoding="utf-8")
    files = sorted(p for p in DATA.rglob("*") if p.is_file() and p.name != "file-manifest.json")
    manifest = {"created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "files": [
        {"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size,
         "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
    write(DATA / "file-manifest.json", manifest)
    paths = files + [DATA / "file-manifest.json", OUTPUT / "kesiapan-data-fieldshift.md"]
    paths += [p for p in (ROOT / "scripts/data").rglob("*") if p.is_file()
              and not any(x in p.parts for x in ["_vendor", "__pycache__", "node_modules"])
              and p.suffix != ".pyc"]
    archive = OUTPUT / "fieldshift-data-publik-2026-11-08.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(paths):
            z.write(path, path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None, "ZIP integrity failed"
    print(json.dumps({"archive": str(archive), "archive_bytes": archive.stat().st_size,
        "archive_files": len(paths), "prepared_files_with_sha256": len(files),
        "prepared_uncompressed_bytes": sum(p.stat().st_size for p in files)}, indent=2))


if __name__ == "__main__":
    main()
