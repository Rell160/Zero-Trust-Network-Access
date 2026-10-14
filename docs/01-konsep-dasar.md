# 01 Konsep Dasar: Zero Trust, ZTNA, Risk-Aware Access, Adaptive MFA, dan Proxmox

> **Ringkasan:** Dokumen ini menjelaskan fondasi teori dari proyek penelitian ini. Kita akan mulai dari filosofi keamanan jaringan tradisional yang punya banyak kelemahan, lalu bergeser ke paradigma Zero Trust yang lebih modern. Setelah itu kita pahami apa itu ZTNA, bagaimana sistem bisa "membaca risiko" secara dinamis, bagaimana autentikasi bisa menyesuaikan diri dengan konteks, dan kenapa Proxmox VE dipilih sebagai platform uji coba. Semua dijelaskan dari nol, dengan analogi yang mudah dibayangkan.

---

## 1. Masalah dengan Keamanan Jaringan Lama

Bayangkan sebuah kantor dengan satu penjaga di pintu depan. Siapapun yang sudah berhasil masuk lewat pintu itu, bisa bebas keliling kantor tanpa diperiksa lagi. Inilah model keamanan jaringan yang disebut **perimeter-based security** atau keamanan berbasis perimeter.

Dalam jaringan komputer tradisional, logikanya sama:
- Ada **firewall** di batas luar jaringan (perimeter).
- Siapa pun yang sudah berada di dalam jaringan internal dianggap "aman" dan dipercaya sepenuhnya.
- Ancaman dianggap hanya datang dari luar.

**Kenapa ini berbahaya?** Ada beberapa alasan:

1. **Ancaman dari dalam.** Karyawan sendiri bisa jadi ancaman, baik disengaja maupun karena akunnya diretas. Sekali masuk, mereka bisa akses semua yang ada di dalam.
2. **Perangkat yang dikompromikan.** Laptop yang sudah kena malware tapi "ada di dalam jaringan" tetap dipercaya.
3. **Era cloud dan remote work.** Sekarang data dan aplikasi tidak hanya ada di kantor. Karyawan kerja dari rumah, kafe, atau co-working space. Konsep "perimeter" sudah tidak relevan.

Model lama ini diibaratkan: **satu kali lolos penjaga depan, bebas ke mana saja.** Model baru yang kita bahas di sini punya penjaga di setiap pintu ruangan, bahkan di setiap laci meja.

---

## 2. Apa Itu Zero Trust?

**Zero Trust** adalah filosofi keamanan yang prinsip utamanya sangat sederhana:

> **"Never Trust, Always Verify"** — Jangan pernah percaya siapa pun secara otomatis, selalu verifikasi.

Artinya, tidak ada satu pun pengguna, perangkat, atau aplikasi yang langsung dipercaya hanya karena mereka ada di dalam jaringan internal. Setiap permintaan akses harus diverifikasi terlebih dahulu, tidak peduli dari mana asalnya.

Konsep ini pertama kali dipopulerkan oleh John Kindervag dari Forrester Research sekitar tahun 2010. Saat ini, Zero Trust sudah menjadi standar keamanan yang direkomendasikan oleh lembaga-lembaga besar seperti **NIST (National Institute of Standards and Technology)** di Amerika Serikat melalui dokumen **NIST SP 800-207: Zero Trust Architecture**.

### Tiga Prinsip Utama Zero Trust

| Prinsip | Penjelasan Singkat |
|---|---|
| Verifikasi secara eksplisit | Autentikasi dan otorisasi harus dilakukan di setiap akses, menggunakan semua informasi yang tersedia (identitas, lokasi, perangkat, waktu, dll.) |
| Gunakan akses dengan hak paling minimal | Berikan akses hanya ke sumber daya yang benar-benar dibutuhkan, tidak lebih |
| Asumsikan selalu ada pelanggaran | Rancang sistem seolah-olah penyerang sudah ada di dalam jaringan. Batasi radius kerusakan dan monitor terus |

**Analogi:** Zero Trust itu seperti rumah sakit. Meskipun kamu sudah masuk lewat pintu utama dan terdaftar sebagai pengunjung, kamu tetap tidak bisa masuk ke ruang ICU, ruang operasi, atau apotek begitu saja. Setiap area punya aturan akses sendiri, dan kamu diverifikasi ulang setiap masuk ke area yang berbeda.

---

## 3. Apa Itu ZTNA (Zero Trust Network Access)?

**ZTNA** (dibaca: "zet-na" atau dieja per huruf) adalah **implementasi teknis** dari filosofi Zero Trust, khusus untuk konteks akses jaringan.

ZTNA adalah layanan atau mekanisme yang mengatur siapa boleh mengakses aplikasi atau sumber daya jaringan tertentu, berdasarkan verifikasi identitas dan konteks yang ketat, bukan hanya posisi mereka di jaringan.

### Perbandingan ZTNA vs VPN Tradisional

| Aspek | VPN Tradisional | ZTNA |
|---|---|---|
| Model kepercayaan | Percaya semua yang ada di dalam tunnel | Verifikasi setiap permintaan akses |
| Cakupan akses | Setelah konek VPN, akses ke seluruh jaringan | Hanya akses ke aplikasi/resource spesifik yang diizinkan |
| Visibilitas | Terbatas, lalu lintas terenkripsi susah dimonitor | Monitoring granular per sesi dan per pengguna |
| Adaptasi konteks | Statis, akses sama untuk semua kondisi | Dinamis, keputusan berubah sesuai konteks dan risiko |

**Analogi:** VPN itu seperti kunci master yang bisa membuka semua pintu di gedung. ZTNA itu seperti kartu akses digital yang hanya membuka pintu tertentu, diperiksa ulang tiap kali kamu mencoba masuk, dan bisa dinonaktifkan secara instan jika ada sesuatu yang mencurigakan.

### Komponen Utama dalam Arsitektur ZTNA

Dalam standar NIST SP 800-207, ada dua komponen logis kunci:

- **PEP (Policy Enforcement Point)**: Titik yang benar-benar "menutup" atau "membuka" akses. Bayangkan ini sebagai petugas keamanan yang berdiri di depan pintu ruangan.
- **PDP (Policy Decision Point)**: Otak yang memutuskan apakah akses boleh diberikan atau tidak, berdasarkan aturan kebijakan. Ini seperti manajer keamanan yang memberitahu petugas di depan pintu: "Boleh masuk" atau "Tolak".

Di proyek ini, PDP terbagi menjadi dua sub-komponen yang akan kita bahas lebih detail di dokumen arsitektur:
- **Policy Engine (PE)**: Mengevaluasi kebijakan.
- **Policy Administrator (PA)**: Memberikan atau mencabut akses ke sumber daya.

---

## 4. Risk-Aware Access: Membaca Risiko Secara Dinamis

Sistem Zero Trust biasa sudah lebih baik dari perimeter tradisional. Tapi sistem kita melangkah lebih jauh dengan **Risk-Aware Access**, yaitu kemampuan sistem untuk menghitung **skor risiko** secara dinamis setiap kali ada permintaan akses.

### Kenapa Perlu Skor Risiko?

Tidak semua skenario akses sama berbahayanya. Contoh:
- Manajer HRD login dari laptop kantor, jam 9 pagi, dari kantor pusat di Jakarta. **Risiko rendah.**
- Akun yang sama login dari laptop asing, jam 3 pagi, dari negara yang tidak pernah dikunjungi sebelumnya, dan laptop tidak punya antivirus aktif. **Risiko sangat tinggi.**

Tanpa penilaian risiko dinamis, kedua skenario ini bisa diperlakukan sama (asal password benar, silakan masuk). Dengan Risk-Aware Access, sistem akan memberikan respons yang berbeda sesuai tingkat bahayanya.

### Faktor-Faktor yang Memengaruhi Skor Risiko

Skor risiko dihitung dari berbagai sinyal kontekstual, antara lain:

| Kategori | Faktor | Contoh |
|---|---|---|
| Identitas | Riwayat login, reputasi akun | Akun yang baru saja gagal login berkali-kali |
| Perangkat | Status keamanan perangkat | Tidak ada antivirus, OS tidak diupdate |
| Lokasi | Negara asal, reputasi IP | Login dari negara berisiko tinggi, IP dari daftar hitam |
| Waktu | Jam akses, kesesuaian pola | Login jam 3 pagi dari pengguna yang biasa login jam 9 pagi |
| Perilaku | Kecepatan aksi, volume data | Transfer data besar secara tiba-tiba |

Setiap faktor ini diberi **bobot** dan dijumlahkan untuk menghasilkan skor risiko akhir (biasanya dalam skala 0 sampai 100 atau 0.0 sampai 1.0). Detail perhitungan ini akan dijelaskan di `04-skenario-risiko.md` berdasarkan kode yang sebenarnya.

---

## 5. Adaptive MFA: Autentikasi yang Menyesuaikan Diri

**MFA (Multi-Factor Authentication)** atau autentikasi multi-faktor adalah metode keamanan di mana pengguna harus membuktikan identitasnya dengan lebih dari satu cara. Secara tradisional, ada tiga kategori faktor autentikasi:

- **Something you know**: Sesuatu yang kamu tahu, misalnya password atau PIN.
- **Something you have**: Sesuatu yang kamu miliki, misalnya smartphone (untuk menerima OTP) atau token hardware.
- **Something you are**: Sesuatu yang kamu sendiri, misalnya sidik jari atau wajah (biometrik).

MFA biasa meminta dua faktor ini secara seragam untuk semua orang di semua kondisi. **Adaptive MFA** lebih cerdas dari itu.

### Apa Bedanya Adaptive MFA?

Adaptive MFA menyesuaikan **jenis dan jumlah faktor autentikasi** yang diminta berdasarkan konteks dan skor risiko sesi tersebut.

- Skor risiko rendah: mungkin cukup dengan password saja, atau password plus TOTP (kode OTP berbasis waktu).
- Skor risiko sedang: wajib TOTP atau email OTP.
- Skor risiko tinggi: diminta autentikasi biometrik atau konfirmasi manual dari admin.
- Skor risiko kritis: akses ditolak langsung, sesi diblokir.

**Analogi:** Bayangkan masuk ke gedung bank. Kalau kamu adalah nasabah yang dikenal, datang saat jam kerja, maka petugas hanya minta menunjukkan kartu identitas. Tapi kalau kamu datang tengah malam, petugas keamanan akan minta kartu identitas, PIN khusus, dan mungkin verifikasi wajah. Tapi kalau situasinya mencurigakan, kamu tidak akan diizinkan masuk sama sekali dan alarm berbunyi.

### TOTP (Time-based One-Time Password)

Salah satu faktor yang umum dipakai dalam proyek ini adalah **TOTP**, yang standarnya didefinisikan dalam **RFC 6238**. TOTP adalah kode numerik (biasanya 6 digit) yang berubah setiap 30 detik dan dibangkitkan menggunakan algoritma berbasis waktu dan kunci rahasia bersama. Aplikasi seperti Google Authenticator atau Authy menggunakan mekanisme TOTP ini.

---

## 6. Proxmox VE Sebagai Platform Testbed

**Proxmox VE (Virtual Environment)** adalah platform virtualisasi open-source berbasis Linux yang memungkinkan kita menjalankan banyak mesin virtual (VM) dan container (LXC) dalam satu server fisik.

### Kenapa Proxmox Dipilih?

Untuk penelitian ini, kita perlu mensimulasikan sebuah jaringan enterprise secara lengkap, tapi tentu tidak mungkin membeli puluhan server fisik hanya untuk eksperimen. Proxmox VE memecahkan masalah ini dengan:

1. **Virtualisasi penuh (KVM)**: Kita bisa membuat VM yang benar-benar berjalan seperti komputer nyata dengan OS sendiri.
2. **Jaringan virtual (Software-Defined Networking)**: Kita bisa membuat topologi jaringan yang kompleks (multiple subnet, VLAN, routing) tanpa hardware tambahan.
3. **Open-source dan gratis**: Tidak perlu lisensi mahal, dokumentasinya lengkap.
4. **Kontrol penuh**: Kita bisa mengatur semuanya dari konfigurasi jaringan sampai snapshot VM untuk reproduksi eksperimen.
5. **Relevan secara industri**: Proxmox banyak digunakan di lingkungan produksi nyata, sehingga hasil penelitian ini relevan secara praktis.

**Analogi:** Proxmox itu seperti LEGO teknologi. Kamu bisa membangun kota virtual lengkap dengan jalan, gedung, dan aturan lalu lintasnya, semuanya dari satu kotak LEGO (satu server fisik), lalu membongkar dan membangunnya lagi dengan konfigurasi yang berbeda.

### Gambaran Topologi Testbed

Di atas Proxmox, kita membangun jaringan virtual yang terdiri dari beberapa VM yang merepresentasikan komponen-komponen nyata dari sistem Zero Trust:
- VM untuk pengguna yang ingin mengakses sumber daya.
- VM untuk Gateway dan ZTNA Controller.
- VM untuk Risk Engine (mesin hitung skor risiko).
- VM untuk MFA Server.
- VM untuk Enterprise Resource (sumber daya yang dilindungi).
- VM untuk Monitoring.

Detail topologi dan konfigurasi jaringannya akan dijelaskan di `02-arsitektur.md`.

---

## Keterbatasan (dari Milestone Saat Ini)

Karena kode belum tersedia di repositori pada saat dokumen ini ditulis, beberapa hal berikut **belum dapat dikonfirmasi dari implementasi nyata** dan akan diperbarui setelah CLI 1 mengisi `docs/HANDOFF.md` dan kode di `src/`:

- Detail teknis perhitungan skor risiko (bobot per faktor, normalisasi, rumus akhir) belum diimplementasikan.
- Mekanisme integrasi antara komponen (protokol API, format data) belum diimplementasikan.
- Konfigurasi jaringan Proxmox yang spesifik belum diimplementasikan.
- Adapasi MFA otomatis berdasarkan skor risiko belum diimplementasikan.

---

## Cek Pemahaman

**Pertanyaan 1:** Apa perbedaan utama antara model keamanan perimeter tradisional dan Zero Trust?

> **Jawaban:** Model perimeter mempercayai semua entitas yang sudah masuk ke dalam jaringan internal. Zero Trust tidak mempercayai siapapun secara otomatis, setiap permintaan akses harus diverifikasi ulang terlepas dari posisi mereka di jaringan.

**Pertanyaan 2:** Dalam ZTNA, apa perbedaan peran PEP dan PDP?

> **Jawaban:** PEP (Policy Enforcement Point) adalah komponen yang secara fisik membuka atau menutup akses ke sumber daya. PDP (Policy Decision Point) adalah komponen yang memutuskan apakah akses harus diberikan atau ditolak berdasarkan evaluasi kebijakan. PEP mengeksekusi keputusan PDP.

**Pertanyaan 3:** Kenapa Adaptive MFA lebih unggul dari MFA konvensional?

> **Jawaban:** MFA konvensional menerapkan faktor autentikasi yang sama untuk semua kondisi, sehingga bisa jadi terlalu ketat untuk skenario berisiko rendah (menurunkan kenyamanan pengguna) atau terlalu longgar untuk skenario berisiko tinggi. Adaptive MFA menyesuaikan jenis dan jumlah faktor autentikasi secara dinamis sesuai konteks dan skor risiko, mencapai keseimbangan antara keamanan dan kenyamanan.
