# Changelog Dokumen

Semua perubahan dokumen yang ditulis oleh asisten penulis di folder `docs/` dicatat di sini.

## [Sinkronisasi Data Eksperimen Final] - 2026-10-03
### Updated
- `06-interpretasi-hasil.md`: Sinkronisasi angka hasil akhir eksperimen (N=9.000 sampel, 10 Variabel). PDP Latency rata-rata 0.035 ms, Akurasi naik ke 75.20%, Adaptation Time 0.362 ms, Uji statistik Mann-Whitney signifikan ($p < 0.001$).
- `07-draft-artikel.md`: Pembaruan bagian Abstract, Results, dan Discussion untuk menyesuaikan angka metrik terbaru (Akurasi 75.2%, MFA overhead turun 71%, CPU overhead 2.79%, RAM 148.39 MB).
- `experiments/results/`: Menyeragamkan format penamaan file (`raw_benchmark_30rep_3config_*.csv`, `statistical_summary_10vars_3config.md`, dan `comparative_evaluation_plots_30rep.png`) agar lebih deskriptif dan mudah di-tracking.

## [Hasil Eksperimen Tuntas] - 2026-10-01
### Added & Updated
- `01-konsep-dasar.md`: Penjelasan teori Zero Trust, ZTNA, Risk-Aware Access, Adaptive MFA, dan Proxmox VE.
- `02-arsitektur.md`: Gambaran 6 komponen sistem, segmentasi 4 Proxmox bridge (`vmbr0`-`vmbr3`), aturan nftables firewall, diagram Mermaid, dan alur kerja terperinci.
- `03-walkthrough-kode.md`: Tur teknis seluruh file dari Milestone 1 sampai Milestone 6 (`common`, `risk_engine`, `mfa_server`, `ztna_controller`, `pep`, `monitoring`, `infra`, `experiments`).
- `04-skenario-risiko.md`: Pemetaan 4 level risiko, bobot fitur, dan contoh perhitungan matematis lengkap 2 skenario.
- `05-metodologi-eksperimen.md`: Tiga konfigurasi pengujian, definisi dan rumus 10 metrik evaluasi, jumlah pengulangan N=30, dan uji statistik.
- `06-interpretasi-hasil.md`: **[SELESAI]** Diisi dengan analisis data kuantitatif riil dari 9.000 titik sampel eksperimen (PDP Latency 0.038 ms, FAR < 15%, Adaptation Time 0.42 ms, dan uji signifikan Mann-Whitney p < 0.001).
- `07-draft-artikel.md`: **[SELESAI]** Bagian Results dan Abstract telah diperbarui sepenuhnya menggunakan angka kuantitatif riil hasil pengujian.
- `08-panduan-presentasi.md`: 13 pertanyaan prediksi dosen penguji beserta jawaban yang objektif dan jujur.
- `09-glosarium.md`: Daftar istilah teknis yang digunakan di dalam proyek.
- `referensi.md`: Daftar standar dan dokumentasi resmi yang tervalidasi.
- `QUESTIONS.md`: Catatan rujukan teknis.
