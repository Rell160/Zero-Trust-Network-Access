# 04 Skenario dan Klasifikasi Level Risiko

> **Ringkasan:** Dokumen ini menjelaskan pengelompokan risiko ke dalam empat tingkatan (Low, Medium, High, dan Critical), batas ambang nilai (score thresholds), persyaratan faktor autentikasi adaptif yang harus dipenuhi pengguna, serta tindakan kontrol akses yang diambil pada masing-masing level. Selain itu, dokumen ini dilengkapi dengan perhitungan matematis langkah demi langkah berdasarkan kode logika yang ada pada `features.py` dan `engine.py` untuk memberikan pemahaman menyeluruh tentang bagaimana skor akhir dihasilkan.

---

## 1. Pemetaan Empat Tingkat Risiko dan Kebijakan Akses

Di dalam sistem kita, skor risiko dinyatakan dalam rentang **0.0 sampai 100.0**. Skor tersebut langsung diklasifikasikan ke dalam 4 tingkatan risiko berikut ini:

| Level Risiko | Ambang Skor (Threshold) | Persyaratan Autentikasi (MFA) | Tindakan Akses Jaringan |
|---|---|---|---|
| **Low** | 0 – 29.0 | Password saja (Single Factor) | Akses Penuh (Full Access) ke resource yang diminta |
| **Medium** | 30 – 59.0 | Password + TOTP (Dua Faktor) | Akses Penuh (Full Access) ke resource yang diminta |
| **High** | 60 – 84.0 | Password + WebAuthn / FIDO2 | Akses Dibatasi (Restricted), hanya baca (read-only) atau subnet terbatas |
| **Critical** | 85 – 100.0 | Tidak Diizinkan (Akses Langsung Ditolak) | Akses Ditolak (DENY) dan Perangkat Dikarantina |

---

## 2. Bobot dan Fitur Konteks yang Dipakai

Berdasarkan file `config/config.yaml` dan implementasi kode di `src/common/config.py`, terdapat 7 sinyal konteks lingkungan yang dievaluasi dengan persentase bobot masing-masing sebagai berikut:

| Nama Fitur | Bobot Konfigurasi | Deskripsi Singkat |
|---|---|---|
| `device_compliance` | 0.20 (20%) | Kepatuhan OS patch, Antivirus, Enkripsi, dan Firewall |
| `geo_ip_anomaly` | 0.15 (15%) | Kesesuaian negara asal IP dengan lokasi sah perusahaan |
| `failed_login_attempts` | 0.15 (15%) | Jumlah kegagalan login berturut-turut sebelum ini |
| `network_reputation` | 0.15 (15%) | Jenis dan keandalan jaringan asal pengguna |
| `resource_sensitivity` | 0.15 (15%) | Tingkat kerahasiaan data yang ingin diakses |
| `off_hours_access` | 0.10 (10%) | Kesesuaian waktu akses dengan jam kerja normal |
| `behavioral_deviation` | 0.10 (10%) | Nilai anomali perilaku penggunaan sesi |

Total keseluruhan bobot adalah `0.20 + 0.15 + 0.15 + 0.15 + 0.15 + 0.10 + 0.10 = 1.00` (100%).

---

## 3. Rumus Perhitungan Skor Matematis

Perhitungan skor dilakukan melalui dua tahapan berurutan:

1. **Tahap Normalisasi Fitur:** Setiap nilai sinyal konteks mentah dikonversi menjadi angka riil $F_i \in [0.0, 1.0]$.
2. **Tahap Perkalian Bobot:**
   $$\text{Skor Akhir} = \sum_{i=1}^{7} (W_i \times F_i) \times 100$$
   Di mana $W_i$ adalah bobot ter-normalisasi dari fitur ke-$i$, dan $F_i$ adalah poin hasil normalisasi dari fitur tersebut.

---

## 4. Contoh Perhitungan Langkah demi Langkah (Simulasi Riil Kode)

Mari kita bedah dua skenario contoh perhitungan langsung menggunakan fungsi dari `src/risk_engine/features.py`.

### Skenario A: Karyawan Biasa di Jam Kerja (Risiko Rendah / Low)
**Kondisi Pengguna:**
- Nama: Alice (Staf Admin)
- Perangkat: OS patched, Antivirus aktif, Disk encrypted, Firewall aktif (`device_compliance` = 0.0)
- Negara: Indonesia / "ID" (`geo_ip` = 0.0)
- Riwayat Login: 0 kali gagal (`failed_logins` = 0.0)
- Jaringan: Jaringan Kantor / "corporate" (`network_reputation` = 0.0)
- Resource: Halaman Berita Internal / "low" (`resource_sensitivity` = 0.10)
- Jam Akses: Rabu jam 10.30 pagi (`off_hours` = 0.0)
- Perilaku: Normal (`behavioral_deviation` = 0.0)

**Langkah Perhitungan:**
1. `device_compliance`: $0.20 \times 0.0 \times 100 = 0.0$ poin
2. `geo_ip_anomaly`: $0.15 \times 0.0 \times 100 = 0.0$ poin
3. `failed_login_attempts`: $0.15 \times 0.0 \times 100 = 0.0$ poin
4. `network_reputation`: $0.15 \times 0.0 \times 100 = 0.0$ poin
5. `resource_sensitivity`: $0.15 \times 0.10 \times 100 = 1.5$ poin
6. `off_hours_access`: $0.10 \times 0.0 \times 100 = 0.0$ poin
7. `behavioral_deviation`: $0.10 \times 0.0 \times 100 = 0.0$ poin

**Total Skor Akhir:** $0.0 + 0.0 + 0.0 + 0.0 + 1.5 + 0.0 + 0.0 = \mathbf{1.5}$  
**Hasil Klasifikasi:** **LOW Risk** ($\le 29.0$). Pengguna diizinkan akses penuh hanya dengan memasukkan password standar.

---

### Skenario B: Akses Mencurigakan dari Luar Negeri (Risiko Kritis / Critical)
**Kondisi Pengguna:**
- Nama: Akun Terkompromikan
- Perangkat: Antivirus Mati, OS Tidak Di-patch, Firewall Mati (`device_compliance` = $0.35 + 0.35 + 0.15 = 0.85$)
- Negara: Rusia / "RU" (Termasuk daftar hitam `high_risk_locations`, maka `geo_ip` = 1.0)
- Riwayat Login: Gagal 6 kali berturut-turut (`failed_logins` = 1.0)
- Jaringan: Proxy anonymizer / "proxy" (`network_reputation` = 0.80)
- Resource: Konsol Admin Keuangan / "critical" (`resource_sensitivity` = 1.0)
- Jam Akses: Minggu jam 02.00 dini hari (`off_hours` = 0.90)
- Perilaku: Anomali tinggi (`behavioral_deviation` = 0.80)

**Langkah Perhitungan:**
1. `device_compliance`: $0.20 \times 0.85 \times 100 = 17.0$ poin
2. `geo_ip_anomaly`: $0.15 \times 1.00 \times 100 = 15.0$ poin
3. `failed_login_attempts`: $0.15 \times 1.00 \times 100 = 15.0$ poin
4. `network_reputation`: $0.15 \times 0.80 \times 100 = 12.0$ poin
5. `resource_sensitivity`: $0.15 \times 1.00 \times 100 = 15.0$ poin
6. `off_hours_access`: $0.10 \times 0.90 \times 100 = 9.0$ poin
7. `behavioral_deviation`: $0.10 \times 0.80 \times 100 = 8.0$ poin

**Total Skor Akhir:** $17.0 + 15.0 + 15.0 + 12.0 + 15.0 + 9.0 + 8.0 = \mathbf{91.0}$  
**Hasil Klasifikasi:** **CRITICAL Risk** ($> 84.0$). Permintaan langsung DITOLAK oleh PEP, token sesi dicabut, dan perangkat dimasukkan ke daftar karantina.

---

## Keterbatasan (dari Milestone 0 & 1)

- Tindakan nyata karantina perangkat di tingkat jaringan (misalnya isolasi via VLAN atau pemblokiran IP di iptables/firewall Proxmox) baru disimulasikan sebagai status respon JSON pada tahapan ini, dan akan benar-benar diintegrasikan pada Milestone 3 dan 5.
- Penilaian anomali perilaku (`behavioral_deviation`) saat ini masih mengambil data dummy numerik dan belum terhubung ke model Machine Learning real-time.

---

## Cek Pemahaman

**Pertanyaan 1:** Jika hasil perhitungan skor risiko pengguna berada pada angka 65.0, perlakuan MFA dan tindakan akses apa yang akan diterapkannya?

> **Jawaban:** Skor 65.0 masuk ke dalam kategori risiko **High** (60 - 84.0). Pengguna wajib melewati autentikasi tingkat lanjut berupa Password + WebAuthn/FIDO2, dan hanya diberikan akses terbatas (Restricted Access) seperti hak baca saja.

**Pertanyaan 2:** Mengapa kondisi login dari negara yang ada pada daftar hitam (seperti "RU" atau "KP") langsung menghasilkan nilai normalisasi 1.0 pada fitur `geo_ip_anomaly`?

> **Jawaban:** Karena di dalam logika `normalize_geo_ip()`, negara yang terdaftar sebagai lokasi berisiko tinggi dikategorikan sebagai ancaman langsung, sehingga sistem menetapkan nilai risiko maksimal 1.0 untuk memberikan kontribusi poin secara penuh pada fitur tersebut.

**Pertanyaan 3:** Apa perbedaan dampak gagal login 2 kali dengan gagal login 5 kali dalam perhitungan skor?

> **Jawaban:** Berdasarkan fungsi `normalize_failed_logins()`, gagal login 2 kali hanya menghasilkan poin penalti 0.35 (kontribusi skor 5.25 poin), sedangkan 5 kali gagal atau lebih dianggap sebagai ciri serangan brute-force dan menghasilkan nilai maksimal 1.0 (kontribusi skor penuh 15.0 poin).
