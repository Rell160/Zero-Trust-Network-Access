# Referensi dan Sumber Literatur

> **Ringkasan:** Dokumen ini memuat daftar rujukan akademik dan dokumentasi teknis resmi yang digunakan sebagai dasar teoritis serta teknis dalam penelitian ini. Referensi dibagi menjadi dua status yaitu **[TERVERIFIKASI]** untuk sumber terbuka dan resmi yang pasti valid, dan **[PERLU VERIFIKASI]** untuk rujukan jurnal tambahan yang harus dicek ulang metadata lengkapnya sebelum dimasukkan ke dalam daftar pustaka artikel ilmiah.

---

## Standar Keamanan dan Protokol

- **[TERVERIFIKASI]** Rose, S., Borchert, O., Mitchell, S., & Connelly, S. (2020). *Zero Trust Architecture* (NIST Special Publication 800-207). National Institute of Standards and Technology. Tersedia secara terbuka dan merupakan acuan utama konsep Zero Trust.
- **[TERVERIFIKASI]** Grassi, P. A., Garcia, M. E., & Fenton, J. L. (2017). *Digital Identity Guidelines: Authentication and Lifecycle Management* (NIST Special Publication 800-63B). National Institute of Standards and Technology. Acuan untuk implementasi autentikator dan MFA.
- **[TERVERIFIKASI]** M'Raihi, D., Machani, S., Pei, M., & Rydell, J. (2011). *TOTP: Time-Based One-Time Password Algorithm* (RFC 6238). Internet Engineering Task Force (IETF). Spesifikasi terbuka untuk algoritma OTP yang digunakan sistem kita.

## Dokumentasi Platform Teknis

- **[TERVERIFIKASI]** Proxmox Server Solutions GmbH. *Proxmox Virtual Environment (VE) Documentation*. Dokumentasi resmi open access untuk arsitektur KVM, LXC, dan pengaturan jaringan virtual (SDN).
- **[TERVERIFIKASI]** FastAPI. *FastAPI Documentation*. Dokumentasi resmi open access mengenai framework web berbasis Python, sistem asinkronus (async), dan arsitektur API.

## Literatur Akademik Pendukung (Untuk Pencarian Lebih Lanjut)

Untuk menyusun bagian Related Work (Penelitian Terkait) pada artikel ilmiah nanti, kamu perlu merujuk pada artikel jurnal di IEEE Xplore, arXiv, atau Google Scholar. Judul-judul di bawah ini adalah panduan pencarian, bukan kutipan final.

- **[PERLU VERIFIKASI]** Jurnal terkait "Context-Aware Access Control in Zero Trust Networks". (Saran: Cari di Google Scholar dengan kata kunci "Context-Aware Zero Trust Network Access", pastikan mencari terbitan 3 tahun terakhir yang *open access*).
- **[PERLU VERIFIKASI]** Jurnal terkait evaluasi latensi dan beban kinerja (overhead) akibat penggunaan MFA adaptif pada arsitektur Zero Trust. (Saran: Gunakan kata kunci pencarian "Adaptive MFA performance evaluation Zero Trust" di IEEE Xplore).

---

## Keterbatasan (dari Milestone Saat Ini)

Karena kode program dan rancangan arsitektur spesifik belum tersedia, daftar pustaka perangkat lunak tambahan yang digunakan oleh CLI 1 (misalnya library Python untuk koneksi database, atau alat monitoring latensi) belum dapat diinklusi. Dokumen ini akan diperbarui segera setelah detail dari CLI 1 diterima melalui `docs/HANDOFF.md`.

---

## Cek Pemahaman

**Pertanyaan 1:** Dokumen NIST manakah yang menjadi standar emas untuk arsitektur Zero Trust?

> **Jawaban:** NIST Special Publication 800-207.

**Pertanyaan 2:** Apa pentingnya status [TERVERIFIKASI] pada referensi ini?

> **Jawaban:** Status tersebut menjamin bahwa sumbernya nyata, diterbitkan secara resmi, dapat diakses publik, dan datanya tidak diarang (halusinasi AI), sehingga aman untuk langsung dikutip di paper akademik.

**Pertanyaan 3:** Standar IETF apa yang mendefinisikan cara kerja TOTP?

> **Jawaban:** RFC 6238.
