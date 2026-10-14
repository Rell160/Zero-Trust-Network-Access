# 05 Metodologi Eksperimen dan Definisi Metrik

> **Ringkasan:** Dokumen ini menguraikan metodologi penelitian eksperimental yang dirancang untuk menguji keefektifan sistem ZTNA Risk-Aware dengan Adaptive MFA pada testbed berbasis Proxmox VE. Kita akan membahas skema pengujian dengan membandingkan tiga konfigurasi arsitektur jaringan yang berbeda. Selain itu, dokumen ini mendefinisikan rumus matematis untuk 10 metrik evaluasi kinerja dan keamanan, standar jumlah pengulangan sampel, serta metode pengujian statistik yang digunakan untuk membuktikan signifikansi hasil.

---

## 1. Tiga Konfigurasi Pembanding (Experimental Baselines)

Untuk membuktikan keunggulan arsitektur yang diajukan, eksperimen dibagi ke dalam tiga perlakuan uji:

### Konfigurasi 1: Baseline Tradisional (Perimeter-Based / Legacy VPN)
- **Mekanisme:** Model perimeter klasik di mana verifikasi identitas hanya dilakukan satu kali di pintu masuk (gerbang VPN) menggunakan username dan password standar. Setelah tersambung ke jaringan, seluruh subnet internal dapat diakses tanpa ada pengecekan risiko dinamis maupun MFA lanjutan.
- **Tujuan:** Menjadi pembanding dasar untuk mengukur seberapa besar peningkatan keamanan yang ditawarkan ZTNA dan berapa biaya latensi tambahan yang harus dibayar.

### Konfigurasi 2: Static MFA ZTNA
- **Mekanisme:** Menggunakan model ZTNA dengan verifikasi setiap akses, tetapi kebijakan MFA bersifat kaku (statis). Semua pengguna diwajibkan melewati dua faktor (Password + TOTP) di setiap sesi atau transaksi tanpa memperhitungkan konteks perangkat maupun skor risiko.
- **Tujuan:** Memperlihatkan bahwa keamanan statis menimbulkan beban friksi yang tidak perlu pada skenario aman (low risk) dan berpotensi kurang ketat pada skenario serangan kritis.

### Konfigurasi 3: Proposed System (Risk-Aware ZTNA with Adaptive MFA)
- **Mekanisme:** Sistem yang dibangun pada proyek ini. Akses dievaluasi secara dinamis menggunakan Risk Scoring Engine 7 fitur. Kebutuhan MFA dan tingkat akses disesuaikan secara otomatis sesuai level risiko (Low, Medium, High, Critical) dengan pemantauan berkelanjutan.

---

## 2. Definisi dan Rumus Matematis 10 Metrik Pengujian

Berikut adalah definisi operasional dan formula perhitungan untuk kesepuluh variabel terukur:

### 1. Authentication Latency ($L_{\text{auth}}$)
- **Definisi:** Waktu total yang dibutuhkan sejak pengguna mengirimkan kredensial awal hingga sistem selesai memvalidasi dan mengeluarkan token sesi.
- **Satuan:** Milidetik (ms)
- **Formula:**
  $$L_{\text{auth}} = T_{\text{token\_issued}} - T_{\text{auth\_request}}$$

### 2. ZTNA Policy Decision Latency ($L_{\text{pdp}}$)
- **Definisi:** Durasi waktu yang dihabiskan oleh ZTNA Controller (PDP) untuk mengevaluasi skor risiko, mencocokkan dengan tabel aturan keamanan, dan menghasilkan keputusan kebijakan (ALLOW, RESTRICT, DENY).
- **Satuan:** Milidetik (ms)
- **Formula:**
  $$L_{\text{pdp}} = T_{\text{decision\_ready}} - T_{\text{context\_received}}$$

### 3. MFA Response Time ($L_{\text{mfa}}$)
- **Definisi:** Waktu komputasi yang dihabiskan oleh MFA Server untuk memverifikasi keabsahan kode OTP atau respons kriptografis WebAuthn.
- **Satuan:** Milidetik (ms)
- **Formula:**
  $$L_{\text{mfa}} = T_{\text{mfa\_verified}} - T_{\text{mfa\_submitted}}$$

### 4. False Acceptance Rate (FAR)
- **Definisi:** Persentase insiden di mana permintaan akses yang berbahaya atau tidak sah secara keliru diizinkan (lolos) oleh sistem kontrol akses.
- **Satuan:** Persen (%)
- **Formula:**
  $$\text{FAR} = \frac{\text{Jumlah Akses Ilegal yang Diizinkan}}{\text{Total Percobaan Akses Ilegal}} \times 100\%$$

### 5. False Rejection Rate (FRR)
- **Definisi:** Persentase insiden di mana pengguna sah yang memenuhi syarat kepatuhan justru ditolak atau diblokir oleh sistem.
- **Satuan:** Persen (%)
- **Formula:**
  $$\text{FRR} = \frac{\text{Jumlah Akses Sah yang Ditolak}}{\text{Total Percobaan Akses Sah}} \times 100\%$$

### 6. Unauthorized Access Prevention Rate (UAPR)
- **Definisi:** Tingkat keberhasilan sistem dalam mendeteksi dan menggagalkan seluruh skenario percobaan akses tanpa izin atau serangan yang disimulasikan.
- **Satuan:** Persen (%)
- **Formula:**
  $$\text{UAPR} = \frac{\text{Jumlah Percobaan Ilegal yang Berhasil Diblokir}}{\text{Total Percobaan Ilegal}} \times 100\% = 100\% - \text{FAR}$$

### 7. Network Overhead ($O_{\text{net}}$)
- **Definisi:** Tambahan ukuran data (header, payload pembawa konteks, atau token otorisasi) yang ditambahkan ke paket jaringan jika dibandingkan dengan komunikasi HTTP langsung tanpa perantara ZTNA.
- **Satuan:** Bytes atau Kilobytes (KB)
- **Formula:**
  $$O_{\text{net}} = \text{Ukuran Paket Melalui PEP} - \text{Ukuran Paket Asli Direct Request}$$

### 8. Resource Utilization (CPU & RAM)
- **Definisi:** Rata-rata persentase konsumsi memori kerja (RAM) dan utilisasi pemroses (CPU) pada VM yang menjalankan service ZTNA selama beban kerja berlangsung.
- **Satuan:** Persen CPU (%) dan Megabytes RAM (MB)
- **Formula:** Diambil melalui pembacaan data periodik alat ukur psutil pada sistem operasi.

### 9. Access-Control Accuracy (ACA)
- **Definisi:** Proporsi keseluruhan keputusan kontrol akses (baik izin yang sah maupun penolakan yang tepat) yang dibuat secara benar terhadap total seluruh pengujian yang dijalankan.
- **Satuan:** Persen (%)
- **Formula:**
  $$\text{ACA} = \frac{\text{True Positives} + \text{True Negatives}}{\text{Total Pengujian}} \times 100\%$$

### 10. Adaptation Time ($T_{\text{adapt}}$)
- **Definisi:** Waktu jeda antara saat kondisi konteks pengguna berubah di lapangan (misal antivirus mendadak dimatikan) sampai sistem ZTNA berhasil mencabut atau menurunkan hak akses sesi yang sedang aktif.
- **Satuan:** Milidetik (ms) atau Detik (s)
- **Formula:**
  $$T_{\text{adapt}} = T_{\text{policy\_enforced\_new}} - T_{\text{context\_change\_event}}$$

---

## 3. Desain Sampel dan Pengujian Statistik

### Jumlah Pengulangan Eksperimen
Setiap skenario pengujian pada masing-masing konfigurasi akan dijalankan sebanyak **minimal 30 kali pengulangan independen ($N = 30$)**. Angka 30 dipilih berdasarkan Teorema Limit Pusat (Central Limit Theorem) dalam statistika inferensial, yang memungkinkan distribusi rata-rata sampel diasumsikan mendekati distribusi normal, sehingga pengujian parametrik dapat dipertanggungjawabkan secara akademik.

### Uji Signifikansi Statistik
1. **Uji Normalitas:** Menggunakan uji Shapiro-Wilk untuk melihat apakah data latensi berdistribusi normal.
2. **Uji Komparasi Rata-rata:**
   - Jika data berdistribusi normal: Menggunakan uji **ANOVA satu arah (One-Way ANOVA)** dilanjutkan dengan uji Post-Hoc Tukey HSD untuk membandingkan perbedaan latensi ketiga konfigurasi secara simultan.
   - Jika data tidak berdistribusi normal: Menggunakan uji non-parametrik **Kruskal-Wallis** dan **Mann-Whitney U Test**.
3. **Selang Kepercayaan (Confidence Interval):** Semua hasil metrik latensi akan disajikan dengan Confidence Interval 95% ($p < 0.05$).

---

## Keterbatasan (dari Milestone 0 & 1)

- Modul skrip eksekusi pengujian otomatis di direktori `experiments/` saat ini belum diimplementasikan oleh CLI 1.
- Topologi jaringan fisik di Proxmox VE belum terpasang, sehingga pengujian awal masih dirancang untuk simulasi lokal (Docker Compose).

---

## Cek Pemahaman

**Pertanyaan 1:** Mengapa penelitian ini perlu membandingkan sistem dengan Static MFA dan bukan hanya dengan sistem Perimeter Tradisional saja?

> **Jawaban:** Perbandingan dengan Static MFA diperlukan untuk membuktikan bahwa Adaptive MFA mampu mengurangi beban latensi dan friksi pada skenario normal (risiko rendah), sekaligus memberikan keamanan yang lebih responsif pada skenario berisiko tinggi dibandingkan MFA konvensional yang kaku.

**Pertanyaan 2:** Apa perbedaan mendasar antara metrik ZTNA Policy Decision Latency dan Authentication Latency?

> **Jawaban:** Authentication Latency mengukur durasi total proses pembuktian identitas awal pengguna, sedangkan Policy Decision Latency hanya mengukur waktu komputasi internal PDP dalam mengevaluasi skor risiko dan menentukan aturan akses.

**Pertanyaan 3:** Mengapa jumlah pengulangan eksperimen ditetapkan minimal 30 kali untuk setiap skenario?

> **Jawaban:** Pengulangan minimal 30 kali memenuhi asumsi Teorema Limit Pusat, sehingga distribusi rata-rata sampel dapat dianggap normal dan memungkinkan penggunaan uji statistik inferensial standar dengan selang kepercayaan 95%.
