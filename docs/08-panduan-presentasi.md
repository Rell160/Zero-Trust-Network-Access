# 08 Panduan Presentasi dan Pertanyaan Penguji

> **Ringkasan:** Dokumen ini memuat kumpulan pertanyaan kritis yang paling mungkin ditanyakan oleh dosen penguji atau reviewer saat presentasi sidang, beserta jawaban yang jujur dan akurat berdasarkan implementasi kode dan arsitektur yang benar-benar ada. Jawaban disusun agar kamu percaya diri menjawab tanpa mengada-ada atau melebih-lebihkan kemampuan sistem. Bagian kelemahan penelitian juga dibahas secara terbuka karena kejujuran akademik justru menambah kredibilitas.

---

## Kategori 1: Pertanyaan Tentang Konsep dan Arsitektur

### Q1. Apa bedanya sistem Zero Trust yang Anda bangun dibandingkan VPN biasa?
> **Jawaban:** VPN tradisional memberikan kepercayaan penuh begitu perangkat tersambung ke tunnel. Setelah masuk, pengguna bisa mengakses seluruh subnet internal tanpa pemeriksaan lanjutan. Sistem kami menerapkan prinsip "Never Trust, Always Verify" dari NIST SP 800-207. Setiap permintaan akses dievaluasi ulang berdasarkan 7 sinyal konteks (lokasi, perangkat, jaringan, waktu, riwayat login, perilaku, dan sensitivitas resource), dan keputusan akses bersifat dinamis per sesi.

### Q2. Mengapa memilih FastAPI dan bukan framework lain seperti Flask atau Django?
> **Jawaban:** FastAPI dipilih karena tiga alasan teknis. Pertama, FastAPI bersifat async-native sehingga cocok untuk mengukur latensi secara akurat pada operasi I/O non-blocking. Kedua, FastAPI secara otomatis menghasilkan dokumentasi OpenAPI sehingga memudahkan pengujian endpoint. Ketiga, integrasi dengan Pydantic memberikan validasi tipe data yang ketat pada setiap request dan response, yang sangat penting untuk menjaga konsistensi kontrak data antar microservices.

### Q3. Kenapa arsitekturnya menggunakan microservices terpisah dan bukan monolitik?
> **Jawaban:** Pemisahan menjadi 4 service (PEP, Risk Engine, MFA Server, ZTNA Controller) mengikuti rekomendasi arsitektur NIST SP 800-207 yang memisahkan Control Plane (pengambilan keputusan) dan Data Plane (penerusan lalu lintas). Ini memungkinkan setiap komponen diuji secara independen, diskalakan terpisah, dan diganti tanpa memengaruhi komponen lain.

---

## Kategori 2: Pertanyaan Tentang Risk Engine dan Scoring

### Q4. Bagaimana cara Anda menentukan bobot untuk masing-masing fitur risiko?
> **Jawaban:** Bobot awal ditentukan berdasarkan studi literatur dan konsensus keamanan enterprise. Device compliance mendapat bobot terbesar (20%) karena perangkat yang dikompromikan merupakan vektor serangan paling umum. Bobot disimpan secara terpusat di file `config/config.yaml` dan dapat disesuaikan tanpa mengubah kode. Fungsi `normalized()` di `src/common/config.py` memastikan total bobot selalu dinormalisasi menjadi 1.0 meskipun administrator melakukan perubahan manual.

### Q5. Kenapa normalisasi fitur menggunakan step function dan bukan machine learning?
> **Jawaban:** Pendekatan step function (fungsi bertingkat) dipilih karena dua alasan. Pertama, hasilnya deterministik dan dapat dijelaskan (explainable). Administrator bisa melihat dengan jelas mengapa satu sesi mendapat skor tertentu, karena setiap kontribusi poin fitur tercatat. Kedua, pendekatan ini tidak memerlukan dataset pelatihan yang besar, sehingga cocok untuk lingkungan testbed penelitian. Ke depannya, integrasi model ML untuk fitur `behavioral_deviation` bisa menjadi pengembangan lanjutan.

### Q6. Apakah skor risiko bisa berubah selama sesi berlangsung?
> **Jawaban:** Ya, ini dirancang melalui mekanisme Continuous Monitoring dan Re-evaluation. ZTNA Controller dikonfigurasi untuk melakukan evaluasi ulang setiap 30 detik (`continuous_reeval_interval_seconds: 30` di `config.yaml`). Namun perlu dicatat bahwa logika re-evaluasi penuh baru akan selesai diimplementasikan pada Milestone 4.

---

## Kategori 3: Pertanyaan Tentang MFA dan Autentikasi

### Q7. Apakah WebAuthn yang digunakan adalah implementasi penuh?
> **Jawaban (jujur):** Tidak. WebAuthn/FIDO2 dalam proyek ini disimulasikan secara kriptografis di sisi server, bukan menggunakan browser Web Authentication API penuh dengan hardware authenticator fisik. Keputusan ini diambil karena keterbatasan lingkungan testbed virtual (VM tidak memiliki USB passkey atau TPM hardware). Simulasi ini tetap mempertahankan prinsip kriptografis challenge-response yang sama.

### Q8. Bagaimana TOTP diimplementasikan?
> **Jawaban:** TOTP mengikuti standar RFC 6238 menggunakan library `pyotp`. Konfigurasi default menggunakan kode 6 digit dengan interval rotasi 30 detik, sesuai dengan standar NIST SP 800-63B untuk authenticator berbasis waktu. Implementasi lengkap enrollment dan verifikasi TOTP dijadwalkan pada Milestone 2.

---

## Kategori 4: Pertanyaan Tentang Eksperimen dan Testbed

### Q9. Kenapa menggunakan Proxmox dan bukan cloud publik seperti AWS atau GCP?
> **Jawaban:** Proxmox VE dipilih karena memberikan kontrol penuh terhadap lingkungan jaringan virtual tanpa variabel latensi eksternal yang tidak dapat dikontrol (seperti latensi inter-region cloud publik). Selain itu, Proxmox bersifat open-source dan gratis, sehingga eksperimen dapat direproduksi oleh peneliti lain tanpa biaya lisensi. Variabilitas kinerja pada cloud publik (noisy neighbor effect) juga bisa mengotori data pengukuran latensi.

### Q10. Apakah traffic yang digunakan adalah traffic enterprise sungguhan?
> **Jawaban (jujur):** Tidak. Traffic yang digunakan adalah traffic sintetis yang dihasilkan oleh harness eksperimen. Traffic ini dirancang untuk mencakup berbagai profil skenario (dari Low Risk hingga Critical Risk) dengan parameter yang terkontrol. Ini merupakan keterbatasan penelitian yang diakui, namun pendekatan ini umum digunakan pada studi eksperimental testbed.

### Q11. Mengapa pengulangan eksperimen sebanyak 30 kali?
> **Jawaban:** Angka 30 memenuhi syarat Teorema Limit Pusat (Central Limit Theorem), yang memungkinkan distribusi rata-rata sampel diasumsikan mendekati distribusi normal. Ini memungkinkan penggunaan uji statistik parametrik seperti ANOVA dengan tingkat kepercayaan 95%.

---

## Kategori 5: Pertanyaan Tentang Kelemahan dan Keterbatasan

### Q12. Apa kelemahan terbesar dari penelitian ini?
> **Jawaban (jujur dan terbuka):**
> 1. **WebAuthn disimulasikan.** Tidak menggunakan hardware authenticator fisik.
> 2. **Traffic sintetis.** Belum diuji dengan pola lalu lintas enterprise sungguhan yang lebih bervariasi dan tidak terduga.
> 3. **Behavioral deviation masih statis.** Fitur anomali perilaku saat ini hanya menerima nilai numerik input manual, belum terhubung ke model deteksi anomali berbasis ML real-time.
> 4. **Single-node Proxmox.** Testbed berjalan pada satu server fisik, belum diuji pada kluster multi-node yang lebih merepresentasikan skala enterprise sesungguhnya.
> 5. **SQLite untuk development.** Database SQLite tidak cocok untuk skenario high-concurrency write pada produksi nyata.

### Q13. Apa yang bisa dikembangkan dari penelitian ini di masa depan?
> **Jawaban:**
> 1. Integrasi model Deep Learning (misalnya LSTM atau Autoencoder) untuk deteksi anomali perilaku secara real-time.
> 2. Implementasi WebAuthn penuh dengan hardware security key (YubiKey atau platform authenticator).
> 3. Pengujian pada kluster Proxmox multi-node dengan traffic enterprise riil.
> 4. Penambahan mekanisme mTLS (mutual TLS) antar microservices untuk keamanan komunikasi internal.

---

## Keterbatasan (dari Milestone 0 & 1)

- Jawaban di kategori eksperimen dan hasil belum dapat menyertakan angka riil karena skrip eksperimen di Milestone 6 belum dijalankan.
- Beberapa pertanyaan lanjutan terkait perbandingan performa dengan baseline baru bisa dijawab setelah data metrik tersedia.

---

## Cek Pemahaman

**Pertanyaan 1:** Jika dosen penguji bertanya tentang kelemahan WebAuthn, apa sikap terbaik yang harus ditunjukkan?

> **Jawaban:** Akui secara terbuka bahwa WebAuthn disimulasikan karena keterbatasan hardware testbed, lalu jelaskan bahwa prinsip kriptografis challenge-response tetap dipertahankan. Kejujuran akademik justru menambah kredibilitas.

**Pertanyaan 2:** Mengapa traffic sintetis tetap dapat diterima sebagai metode pengujian dalam penelitian ini?

> **Jawaban:** Karena traffic sintetis memberikan kendali penuh terhadap variabel eksperimen (parameter input terkontrol dan dapat diulang), yang merupakan syarat utama dalam desain eksperimen ilmiah. Pendekatan ini umum digunakan pada studi testbed di bidang keamanan jaringan.

**Pertanyaan 3:** Apa alasan teknis utama memilih Proxmox dibandingkan cloud publik untuk testbed?

> **Jawaban:** Proxmox menghilangkan variabel latensi eksternal yang tidak terkontrol (seperti noisy neighbor effect dan latensi inter-region), sehingga data pengukuran lebih bersih dan dapat direproduksi.
