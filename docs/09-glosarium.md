# 09 Glosarium Istilah Teknis

> **Ringkasan:** Dokumen ini memuat kumpulan istilah teknis yang digunakan sepanjang penelitian ZTNA Risk-Aware dengan Adaptive MFA ini. Istilah-istilah disajikan secara alfabetis lengkap dengan sinonim, padanan kata, dan penjelasan singkat yang mudah dipahami. Glosarium ini dirancang sebagai panduan cepat saat kamu membaca dokumen arsitektur, penjelasan kode, atau menyiapkan bahan presentasi.

---

## Daftar Istilah

### A
- **Adaptive MFA (Multi-Factor Authentication Adaptif)**: Sistem autentikasi multi-faktor yang secara otomatis menyesuaikan tingkat keamanan (jumlah dan jenis faktor) berdasarkan skor risiko dan konteks pengguna.
- **Anomalous Traffic (Lalu Lintas Anomali)**: Pola lalu lintas jaringan yang menyimpang dari perilaku normal, bisa menjadi indikasi adanya serangan atau kebocoran data.
- **API (Application Programming Interface)**: Antarmuka yang memungkinkan dua atau lebih program komputer untuk saling berkomunikasi dan bertukar data.
- **Access Control (Kontrol Akses)**: Mekanisme keamanan yang mengatur siapa yang diizinkan mengakses sumber daya tertentu dan tindakan apa yang boleh mereka lakukan.

### C
- **Context Collection (Pengumpulan Kontekstual)**: Proses mengumpulkan data lingkungan dari permintaan akses, seperti lokasi geografis, reputasi IP, status keamanan perangkat, dan waktu akses.
- **Continuous Monitoring (Pemantauan Berkelanjutan)**: Proses mengawasi aktivitas jaringan dan perilaku sesi pengguna secara terus-menerus, bukan hanya pada saat awal login.

### F
- **FAR (False Acceptance Rate)**: Persentase permintaan akses yang seharusnya ditolak oleh sistem keamanan tetapi justru diterima (lolos).
- **FRR (False Rejection Rate)**: Persentase permintaan akses yang sah tetapi ditolak oleh sistem keamanan.
- **FastAPI**: Framework web berbasis Python yang berkinerja tinggi, digunakan untuk membangun API dengan kecepatan tinggi dan dokumentasi otomatis.

### K
- **KVM (Kernel-based Virtual Machine)**: Teknologi virtualisasi penuh berbasis kernel Linux yang digunakan di Proxmox VE untuk menjalankan mesin virtual secara efisien.

### L
- **LXC (Linux Containers)**: Teknologi virtualisasi tingkat sistem operasi yang ringan, digunakan di Proxmox VE untuk menjalankan container dengan konsumsi resource minimal.

### M
- **MFA (Multi-Factor Authentication)**: Metode autentikasi yang memerlukan dua atau lebih bukti verifikasi (faktor) untuk memberikan akses kepada pengguna.

### N
- **NIST SP 800-207**: Standar arsitektur Zero Trust yang diterbitkan oleh National Institute of Standards and Technology.
- **NIST SP 800-63B**: Panduan identitas digital yang diterbitkan oleh NIST, mencakup standar teknis autentikator seperti TOTP.

### P
- **PDP (Policy Decision Point)**: Komponen logis dalam arsitektur Zero Trust yang bertugas mengevaluasi kebijakan dan membuat keputusan apakah permintaan akses diizinkan atau ditolak.
- **PEP (Policy Enforcement Point)**: Komponen logis yang bertugas mencegat, memeriksa, dan memblokir atau meneruskan lalu lintas jaringan sesuai dengan keputusan PDP.
- **Policy Engine (PE)**: Sub-komponen dari PDP yang menggunakan kebijakan keamanan untuk menentukan keputusan akses.
- **Policy Administrator (PA)**: Sub-komponen dari PDP yang berkomunikasi dengan PEP untuk mengeksekusi atau memperbarui perintah akses.
- **Proxmox VE (Virtual Environment)**: Platform manajemen virtualisasi open-source yang menggabungkan virtualisasi KVM dan LXC, jaringan virtual, dan penyimpanan dalam satu antarmuka.

### R
- **RFC 6238**: Standar teknis internasional yang mendefinisikan algoritma TOTP (Time-based One-Time Password).
- **Risk Engine (Mesin Risiko)**: Komponen software yang menghitung skor risiko berdasarkan bobot dari berbagai faktor kontekstual.
- **Risk Score (Skor Risiko)**: Nilai numerik yang merepresentasikan tingkat bahaya dari suatu permintaan akses.

### S
- **Step-Up Authentication**: Proses meminta faktor autentikasi tambahan dari pengguna ketika risiko meningkat atau saat mengakses data yang lebih sensitif.

### T
- **Testbed**: Lingkungan eksekusi yang dikontrol secara ketat untuk melakukan pengujian dan eksperimen terhadap suatu sistem.
- **TOTP (Time-based One-Time Password)**: Kode sekali pakai yang berlaku dalam durasi waktu singkat (biasanya 30 detik), dibangkitkan dari algoritma matematis menggunakan kunci rahasia dan jam sistem.

### V
- **VM (Virtual Machine / Mesin Virtual)**: Emulasi perangkat lunak dari sistem komputer fisik yang berjalan di atas hypervisor.
- **VPN (Virtual Private Network)**: Teknologi yang membuat koneksi jaringan terenkripsi aman, tetapi secara tradisional memberikan kepercayaan penuh pada perangkat yang terhubung.

### Z
- **Zero Trust**: Filosofi keamanan siber yang mengasumsikan tidak ada elemen yang dapat dipercaya secara otomatis, baik dari luar maupun dari dalam jaringan.
- **ZTNA (Zero Trust Network Access)**: Solusi keamanan berbasis Zero Trust yang memberikan akses aman berbasis aplikasi ke sumber daya internal tanpa membuka akses ke seluruh jaringan.

---

## Keterbatasan (dari Milestone Saat Ini)

Karena implementasi kode dari CLI 1 belum diunggah ke repositori, istilah-istilah berikut mungkin akan bertambah atau disesuaikan dengan komponen spesifik yang nanti dibangun di kode:

- Nama-nama modul internal Python yang dibuat CLI 1 belum dimasukkan.
- Istilah khusus terkait skrip eksperimen belum dimasukkan.

---

## Cek Pemahaman

**Pertanyaan 1:** Apa perbedaan antara FAR dan FRR dalam evaluasi sistem keamanan?

> **Jawaban:** FAR (False Acceptance Rate) mengukur seberapa sering penyerang atau akses tidak sah lolos diterima sistem. FRR (False Rejection Rate) mengukur seberapa sering pengguna sah malah ditolak oleh sistem.

**Pertanyaan 2:** Apa fungsi dari PDP dan PEP dalam arsitektur ZTNA?

> **Jawaban:** PDP adalah otak yang mengambil keputusan apakah akses diperbolehkan atau ditolak. PEP adalah pelaksana yang memblokir atau membiarkan lalu lintas lewat berdasarkan instruksi PDP.

**Pertanyaan 3:** Apa itu Step-Up Authentication?

> **Jawaban:** Step-Up Authentication adalah tindakan meminta verifikasi keamanan tambahan saat sistem mendeteksi peningkatan risiko atau saat pengguna mencoba mengakses data yang sensitif.
