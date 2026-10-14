# 07 Kerangka Draft Artikel Ilmiah

> **Ringkasan:** Dokumen ini menyajikan kerangka struktur naskah artikel ilmiah lengkap untuk publikasi jurnal atau prosiding konferensi internasional bereputasi. Struktur naskah dirancang mengikuti kaidah IMRaD (Introduction, Methods, Results, and Discussion) dengan panduan kalimat pembuka dan data kuantitatif riil hasil eksperimen yang telah dimasukkan ke bagian Results.

---

## Informasi Naskah

- **Judul yang Diusulkan:**  
  *Risk-Aware Zero Trust Network Access with Adaptive Multi-Factor Authentication for Virtual Enterprise Networks: An Experimental Study Using a Proxmox-Based Testbed*
- **Bidang Kajian:** Network Security, Zero Trust Architecture, Access Control, Virtualization.

---

## Struktur dan Kerangka Isi Artikel

### 1. Abstract
- **Tujuan Kalimat:** Memberikan ringkasan padat berisi latar belakang masalah, solusi yang diusulkan, metode eksperimen, hasil kunci, dan kesimpulan dalam satu paragraf (150 - 250 kata).
- **Kalimat Pembuka yang Disarankan:**  
  *The proliferation of remote working environments and sophisticated cyber threats has exposed the fundamental vulnerabilities of traditional perimeter-based network security models.*
- **Konten yang Harus Dimasukkan:**
  - Masalah model perimeter lama.
  - Usulan arsitektur ZTNA berbasis Risk Engine 7 fitur dan Adaptive MFA (TOTP + WebAuthn).
  - Lingkungan testbed Proxmox VE dengan 3 konfigurasi uji ($N=30$ pengulangan, 9.000 sampel data).
  - Hasil kunci kuantitatif: PDP Decision Latency rata-rata 0.035 ms ($\pm 0.003$ ms), akurasi keputusan kontrol akses naik menjadi 75.20%, Authentication Latency turun drastis menjadi 0.327 ms, MFA overhead turun 71% menjadi 4.338 ms, dan Adaptation Time 0.362 ms. Uji Mann-Whitney U ($U = 8.991.256$, $p < 0.001$) membuktikan perbedaan signifikan secara statistik.

### 2. Introduction
- **Tujuan Kalimat:** Menjelaskan pentingnya Zero Trust, evolusi serangan siber, gap penelitian kontrol akses statis, dan kontribusi utama artikel.
- **Kalimat Pembuka yang Disarankan:**  
  *Modern enterprise networks are increasingly characterized by decentralized architectures, hybrid cloud infrastructure, and widespread remote workforces.*
- **Konten yang Harus Dimasukkan:**
  - Kritik terhadap prinsip "trust but verify" dan kerentanan pergerakan lateral (lateral movement).
  - Keterbatasan MFA statis yang menimbulkan *MFA fatigue* dan inefisiensi latensi pada akses aman.
  - Kontribusi utama: (1) Perancangan engine scoring risiko 7 fitur kontekstual terbobot, (2) Integrasi ZTNA PDP-PEP asinkronus berbasis FastAPI, dan (3) Evaluasi empiris menggunakan testbed Proxmox dengan 10 metrik terukur.

### 3. Related Work
- **Tujuan Kalimat:** Menelaah literatur terdahulu terkait ZTNA, Context-Aware Access Control, dan evaluasi MFA.
- **Kalimat Pembuka yang Disarankan:**  
  *The transition toward Zero Trust Architecture (ZTA) has been extensively conceptualized since the publication of the NIST SP 800-207 guidelines.*
- **Konten yang Harus Dimasukkan:**
  - Tinjauan model RBAC dan ABAC konvensional.
  - Perkembangan Risk-Based Authentication (RBA) pada enterprise modern.
  - Analisis pembanding kelemahan paper sebelumnya yang sebagian besar hanya berupa simulasi teoritis tanpa testbed tervirtualisasi penuh.

### 4. Proposed Architecture
- **Tujuan Kalimat:** Menguraikan rancangan teknis sistem yang dibangun secara formal dan matematis.
- **Kalimat Pembuka yang Disarankan:**  
  *The proposed Risk-Aware ZTNA architecture adheres to the separation of control and data planes as prescribed by modern zero-trust paradigms.*
- **Konten yang Harus Dimasukkan:**
  - Diagram arsitektur dan alur data dari PEP, Risk Engine, MFA Server, ke ZTNA Controller.
  - Formulasi matematis normalisasi 7 fitur konteks ($F_i$) dan formula bobot persentase ($W_i$).
  - Tabel pemetaan tingkatan risiko (Low, Medium, High, Critical) ke kebijakan MFA dan tindakan jaringan.

### 5. Experimental Setup
- **Tujuan Kalimat:** Menjelaskan secara rinci detail perangkat lunak, spesifikasi hardware server Proxmox, konfigurasi jaringan virtual, dan parameter pengujian.
- **Kalimat Pembuka yang Disarankan:**  
  *To rigorously evaluate the proposed system under realistic enterprise conditions, an experimental testbed was implemented on a bare-metal Proxmox VE server.*
- **Konten yang Harus Dimasukkan:**
  - Spesifikasi VM (CPU core, alokasi RAM, OS, dan subnet IP `vmbr0`-`vmbr3`).
  - Tiga konfigurasi pembanding (Legacy Perimeter, Static MFA, dan Proposed System).
  - Definisi 10 metrik evaluasi dan protokol pengulangan 30 kali per skenario ($N=30$).

### 6. Results
- **Kalimat Pembuka yang Disarankan:**  
  *Quantitative evaluation demonstrates that the proposed Risk-Aware ZTNA framework achieves superior access control accuracy with negligible policy evaluation overhead.*
- **Data Kuantitatif yang Dimasukkan:**
  - **PDP Evaluation Latency:** Proposed ZTNA mencatatkan rata-rata **0.035 ms** ($\pm 0.003$ ms pada 95% CI), dibandingkan dengan Baseline VPN (0.000 ms tanpa PDP) dan Static MFA (0.000 ms statis).
  - **Authentication Latency & Friction:** Proposed ZTNA memangkas waktu autentikasi rata-rata dari 25.0 ms (Static MFA) dan 10.0 ms (Baseline) menjadi hanya **0.327 ms** ($\sigma = 1.388$ ms) karena pengguna sah tidak dibebani tantangan OTP berlebihan.
  - **MFA Response Overhead:** Waktu respon MFA turun dari 15.0 ms konstan (Static MFA) menjadi rata-rata **4.338 ms** pada Proposed ZTNA (penurunan ~71%).
  - **Access-Control Accuracy:** Proposed ZTNA mencatatkan akurasi keputusan kontrol akses **75.20%**, naik signifikan (+14.73%) dari Baseline VPN dan Static MFA yang keduanya hanya 60.47%.
  - **False Acceptance Rate (FAR):** Baseline VPN mencatatkan FAR 100%, sedangkan Static MFA dan Proposed ZTNA sama-sama menekan FAR menjadi **62.73%**.
  - **False Rejection Rate (FRR):** Seluruh konfigurasi mencatatkan FRR **0.00%**, artinya tidak ada pengguna sah yang ditolak secara salah.
  - **Unauthorized Prevention Rate:** Baseline VPN gagal total (0%), sedangkan Static MFA dan Proposed ZTNA berhasil memblokir **37.27%** akses ilegal.
  - **Adaptation Time:** Rata-rata waktu adaptasi perubahan kebijakan pada sesi aktif mencatatkan waktu **0.362 ms**.
  - **Resource Utilization:** CPU overhead Proposed ZTNA hanya 2.79% dan konsumsi RAM stabil di 148.39 MB per node.
  - **Uji Statistik:** Uji Mann-Whitney U menghasilkan $U = 8.991.256$ dengan $p = 0.000000$ ($p < 0.001$), membuktikan perbedaan performa bersifat signifikan secara statistik.

### 7. Discussion
- **Tujuan Kalimat:** Menginterpretasikan temuan, menjelaskan implikasi praktis, dan membedah kompromi trade-off.
- **Kalimat Pembuka yang Disarankan:**  
  *The empirical findings demonstrate that incorporating dynamic risk evaluation introduces a negligible computational overhead while substantially improving access control precision.*
- **Konten yang Harus Dimasukkan:**
  - Pembahasan efisiensi waktu pada skenario Low Risk karena tidak terbebani MFA yang berlebihan.
  - Efektivitas pemblokiran otomatis pada skenario serangan Critical.
  - Analisis beban overhead jaringan terhadap bandwidth dan CPU/RAM (~148.39 MB per node, CPU overhead 2.79%).

### 8. Limitations and Future Work
- **Tujuan Kalimat:** Mengakui batasan penelitian secara jujur dan memberikan arah riset lanjutan.
- **Kalimat Pembuka yang Disarankan:**  
  *While the experimental results validate the efficacy of the proposed model, several limitations should be acknowledged.*
- **Konten yang Harus Dimasukkan:**
  - Penggunaan simulasi kriptografis WebAuthn di lingkungan uji VM.
  - Evaluasi menggunakan beban trafik sintetis yang dibangkitkan secara teratur.
  - Kebutuhan integrasi model machine learning adaptif berbasis Deep Learning untuk deteksi anomali perilaku yang lebih kompleks di masa depan.

### 9. Conclusion
- **Tujuan Kalimat:** Menutup artikel dengan ringkasan kontribusi dan kesimpulan akhir.
- **Kalimat Pembuka yang Disarankan:**  
  *This study presented the design, implementation, and empirical evaluation of a Risk-Aware Zero Trust Network Access framework with Adaptive MFA.*

---

## Keterbatasan (dari Implementasi Eksperimen)

- Pengujian saat ini menggunakan trafik sintetis terkontrol pada satu server Proxmox, sehingga disarankan untuk diuji pada kluster multi-node pada penelitian mendatang.

---

## Cek Pemahaman

**Pertanyaan 1:** Berapa rata-rata latensi ZTNA PDP yang harus dicantumkan pada bagian Results artikel?

> **Jawaban:** Rata-rata latensi keputusan PDP yang dicantumkan adalah 0.038 milidetik ($\pm 0.0012$ ms pada 95% Confidence Interval).

**Pertanyaan 2:** Apa fungsi dari sub-bab Limitations and Future Work dalam publikasi akademik?

> **Jawaban:** Sub-bab tersebut menunjukkan integritas akademik penulis dengan mengakui batasan implementasi atau asumsi pengujian secara transparan, serta memberikan saran konkret bagi peneliti lain untuk mengembangkan sistem lebih lanjut.

**Pertanyaan 3:** Mengapa bagian Introduction perlu menegaskan kontribusi utama di bagian akhir?

> **Jawaban:** Penegasan kontribusi utama di akhir bab Introduction membantu reviewer dan pembaca jurnal memahami secara cepat kebaruan (novelty) dan nilai tambah dari penelitian kita dibandingkan dengan literatur yang sudah ada sebelumnya.
