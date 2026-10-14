# 03 Walkthrough Kode Sistem ZTNA (Milestone 1-6)

> **Ringkasan:** Dokumen ini merupakan panduan tur teknis yang menjelaskan baris-baris kode dari seluruh modul yang sudah selesai dibangun dari Milestone 1 sampai Milestone 6. Kita akan membedah tujuan dari setiap file Python di folder `src/`, `experiments/`, dan `infra/`, mengidentifikasi input dan output, membahas fungsi kuncinya, dan memberikan contoh skenario pemrosesan data riil. Panduan ini sangat bermanfaat untuk memahami logika kode internal secara menyeluruh.

---

## 1. Modul Konfigurasi dan Model Data Bersama (Common)

Karena arsitektur kita menggunakan pendekatan microservices, semua komponen perlu sepakat tentang bentuk data yang dipertukarkan. Kesepakatan ini diatur dalam folder `src/common/`.

### File: `src/common/models.py`
- **Tujuan:** Mendefinisikan struktur data terpusat menggunakan library Pydantic. Pydantic memastikan tipe data valid sebelum diproses.
- **Fungsi Kunci:**
  - `RiskLevel`: Enum klasifikasi empat tingkat risiko (Low, Medium, High, Critical).
  - `PolicyDecision`: Enum keputusan kebijakan (ALLOW, RESTRICT, DENY).
  - `MFAMethod`: Enum metode autentikasi (NONE, PASSWORD, TOTP, WEBAUTHN).
  - `AccessContext`: Blueprint dari data konteks pengguna yang datang dari PEP. Berisi informasi seperti `geo_location`, `device` compliance, `behavioral_score`, dan `failed_login_count`.
  - `RiskScore`: Blueprint data balasan dari Risk Engine ke Controller. Berisi skor akhir, level risiko, dan penjelasan rincian poin tiap fitur (explainability).

### File: `src/common/config.py`
- **Tujuan:** Mengelola semua pengaturan batas ambang dan bobot perhitungan dari file YAML ke dalam objek Python.
- **Fungsi Kunci:**
  - `RiskThresholds`: Menetapkan batas poin risiko (Low 29, Medium 59, High 84, Critical 100).
  - `RiskWeights`: Mendefinisikan persentase pengaruh 7 fitur risiko, yang otomatis disesuaikan menjadi total 1.0 melalui fungsi `normalized()`.

### File: `src/common/logging.py`
- **Tujuan:** Membuat format pencatatan log berbentuk JSON secara otomatis agar mudah di-parse oleh alat pemantauan terpusat.

---

## 2. Modul Penilaian Risiko (Risk Engine)

Folder `src/risk_engine/` adalah pusat otak analitik penilai risiko.

### File: `src/risk_engine/features.py`
- **Tujuan:** Mengekstrak dan menormalkan nilai dari 7 sinyal konteks lingkungan ke dalam skala 0.0 (aman) hingga 1.0 (bahaya).
- **Fungsi Kunci:**
  - `normalize_geo_ip()`: Membandingkan negara pengguna dengan daftar putih dan daftar hitam.
  - `normalize_device_compliance()`: Menghitung penalti penumpukan kepatuhan perangkat (OS patch, Antivirus, Enkripsi, Firewall).
  - `normalize_failed_logins()`: Hukuman bertingkat untuk kegagalan login hingga batas 5 kali yang dianggap brute-force.
  - `normalize_network_reputation()`, `normalize_off_hours()`, `normalize_behavioral_deviation()`, `normalize_resource_sensitivity()`.

### File: `src/risk_engine/engine.py`
- **Tujuan:** Menggabungkan poin normalisasi fitur dengan bobot konfigurasi.
- **Fungsi Kunci:**
  - `calculate_contributions()`: Mengalikan nilai normalisasi fitur dengan bobot ter-normalisasi dan dikali 100 untuk menghasilkan skor persentase.
  - `generate_explanation()`: Menghasilkan kalimat ringkasan 3 penyumbang poin risiko terbesar (Explainable AI).

### File: `src/risk_engine/app.py`
- **Tujuan:** Aplikasi FastAPI bertindak sebagai antarmuka API service penilai risiko pada port 8001.
- **Fungsi Kunci:**
  - Endpoint `POST /evaluate`: Menerima `AccessContext` dan mengembalikan `RiskScore` lengkap dengan pencatatan latensi ke Prometheus.

---

## 3. Modul MFA Server dan Adaptive MFA Policy

Folder `src/mfa_server/` mengelola autentikasi multi-faktor adaptif pada port 8002.

### File: `src/mfa_server/totp.py` & `store.py`
- **Tujuan:** Pendaftaran (enrollment) dan verifikasi kode TOTP 6 digit berbasis RFC 6238 dengan `pyotp`.

### File: `src/mfa_server/webauthn_sim.py`
- **Tujuan:** Simulasi kriptografis WebAuthn/FIDO2 berbasis HMAC-SHA256 assertion challenge-response.

### File: `src/mfa_server/policy.py` & `app.py`
- **Tujuan:** Menentukan faktor MFA yang dibutuhkan berdasarkan level risiko (Low: Password, Medium: Password+TOTP, High: Password+WebAuthn, Critical: Denied).

---

## 4. Modul ZTNA Controller (PDP) dan PEP Proxy

### File: `src/ztna_controller/pdp.py` & `app.py`
- **Tujuan:** Policy Decision Point (PDP) pada port 8003 yang menerapkan prinsip **Fail-Closed (Default-Deny)**. Memetakan skor risiko dari Risk Engine ke keputusan kebijakan ALLOW, RESTRICT, atau DENY.

### File: `src/pep/proxy.py` & `app.py`
- **Tujuan:** Policy Enforcement Point (PEP) pada port 8000 yang bertindak sebagai reverse-proxy gateway. PEP menjalankan alur pipeline: menerima request -> memanggil Risk Engine -> memanggil PDP -> memeriksa status MFA -> meneruskan request atau memblokir dengan HTTP 401/403.

---

## 5. Modul Pemantauan Berkelanjutan (Continuous Monitoring)

### File: `src/monitoring/continuous.py`
- **Tujuan:** Mendaftarkan sesi aktif dan menjalankan fungsi `reevaluate_session_sync()` secara berkala. Jika skor risiko pengguna berubah di pertengahan sesi, sistem menghasilkan `AdaptationEvent` dan mengeksekusi penyesuaian hak akses (misal downgrading atau isolasi karantina).
- **Fungsi Kunci:** Mengukur variabel **Adaptation Time** (waktu jeda antara perubahan konteks risiko hingga penegakan kebijakan baru).

---

## 6. Modul Eksperimen dan Pengujian Otomatis

Folder `experiments/` berisi skrip untuk mengeksekusi pengujian ilmiah.

### File: `experiments/traffic_generator.py`
- **Tujuan:** Menggenerasi 4 skenario trafik sintetis (Legitimate, Off-hours, Non-compliant device, Malicious Attack) dengan fixed random seed agar hasil pengujian dapat direproduksi (reproducible).

### File: `experiments/benchmark_runner.py`
- **Tujuan:** Orkestrator utama yang menjalankan 30 kali pengulangan eksperimen untuk 3 konfigurasi pembanding (Baseline VPN, Static MFA, dan Proposed Risk-Aware ZTNA).

### File: `experiments/analysis.py`
- **Tujuan:** Menghitung nilai rata-rata (Mean), standar deviasi (Std), 95% Confidence Interval, uji normalitas Shapiro-Wilk, uji Mann-Whitney U, serta menghasilkan plot grafik statistik dengan matplotlib.

---

## Keterbatasan (dari Milestone 1-6)

- Panggilan `datetime` pada file `experiments/benchmark_runner.py` di baris 229 mengalami kelalaian impor (`NameError`), sehingga eksekusi master skrip `run_experiment.py` terhenti saat ini. Pertanyaan keliruan ini telah dicatat di `docs/QUESTIONS.md`.

---

## Cek Pemahaman

**Pertanyaan 1:** Bagaimana prinsip Fail-Closed diterapkan di dalam PEP proxy?

> **Jawaban:** Jika subsistem Risk Engine atau PDP mengalami gangguan (down) atau timeout, PEP secara otomatis membatalkan permintaan dan mengembalikan respon HTTP 503 DENY untuk mencegah celah keamanan fail-open.

**Pertanyaan 2:** Apa fungsi dari `experiments/traffic_generator.py` dalam eksperimen ini?

> **Jawaban:** Skrip tersebut bertugas menghasilkan data trafik sintetis dengan skenario terkontrol dan seed acak yang tetap (fixed seed), sehingga seluruh 30 kali pengulangan eksperimen berjalan pada kondisi beban yang sama persis dan dapat direproduksi.

**Pertanyaan 3:** Apa yang diukur oleh variabel Adaptation Time di `src/monitoring/continuous.py`?

> **Jawaban:** Adaptation Time mengukur selisih waktu dalam milidetik antara saat terdeteksinya perubahan nilai risiko konteks pengguna dengan waktu saat kebijakan otorisasi baru berhasil ditegakkan oleh sistem.
