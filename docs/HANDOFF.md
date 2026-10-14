# HANDOFF.md — Catatan Milestone untuk CLI 2

> File ini ditulis oleh CLI 1 (engineer) untuk CLI 2 (dokumentasi).
> Setiap milestone mencatat: file yang dibuat/diubah, cara menjalankan, keputusan desain, dan hal yang belum selesai.

---

## Milestone 6: Harness Eksperimen & Analisis Kuantitatif

**Tanggal:** 2026-10-01

### File yang Dibuat

| Kategori | File | Status |
|---|---|---|
| Traffic Generator | `experiments/traffic_generator.py` | Dibuat (Generator 4 skenario trafik sintetis dengan fixed seed & ground truth) |
| Runner | `experiments/benchmark_runner.py` | Dibuat (Orkestrator 30x pengulangan untuk 3 konfigurasi: Baseline VPN, Static MFA, Proposed ZTNA) |
| Analisis & Plot | `experiments/analysis.py` | Dibuat (Kalkulasi Mean, Std, 95% CI, uji Shapiro-Wilk, Mann-Whitney U, & plot grafik publikasi matplotlib) |
| Master Script | `run_experiment.py` | Dibuat (Entry point eksekusi eksperimen ujung-ke-ujung) |

### 10 Variabel yang Diukur

1. **Authentication Latency**: Waktu pemrosesan autentikasi (ms).
2. **ZTNA Policy Decision Latency**: Waktu pengambilan keputusan pada PDP (ms) beserta 95% Confidence Interval.
3. **MFA Response Time**: Overhead waktu respon faktor kedua/ketiga (ms).
4. **False Acceptance Rate (FAR)**: $\text{Serangan lolos} / \text{Total serangan} \times 100\%$.
5. **False Rejection Rate (FRR)**: $\text{User sah ditolak} / \text{Total user sah} \times 100\%$.
6. **Unauthorized Access Prevention Rate**: $100\% - \text{FAR}$.
7. **Network / Processing Overhead**: Tambahan latensi proxy PEP.
8. **CPU & RAM Utilization**: Penggunaan resource CPU (%) dan RAM (MB) menggunakan `psutil`.
9. **Access-Control Accuracy**: $\text{Keputusan Benar} / \text{Total Permintaan} \times 100\%$.
10. **Adaptation Time**: Selisih waktu deteksi perubahan risiko terhadap penegakan kebijakan baru (ms).

### Cara Menjalankan Eksperimen

```bash
# Menjalankan seluruh siklus eksperimen (30 pengulangan x 100 request x 3 konfigurasi)
.venv/Scripts/python.exe run_experiment.py
```

---

## Milestone 5: Infrastruktur Proxmox VE & Segmentasi Jaringan

**Tanggal:** 2026-10-01

### File yang Dibuat

| Kategori | File | Status |
|---|---|---|
| Provisioning | `infra/proxmox/01-setup-proxmox-vms.sh` | Dibuat (Skrip bash otomatisasi `qm` & cloud-init Proxmox VE) |
| Firewall | `infra/firewall/nftables-ztna.conf` | Dibuat (Aturan nftables: Default-Deny, isolasi VLAN, & dynamic quarantine set) |
| Panduan | `infra/README.md` | Dibuat (Panduan setup topologi, IP matrix, dan konfigurasi Proxmox bridge) |

### Desain Segmentasi Jaringan (4 Bridges)

1. **`vmbr0` (192.168.1.0/24)**: WAN / Uplink / Management.
2. **`vmbr1` (10.10.10.0/24)**: ZTNA Control Plane (`ztna-controller`, `risk-engine`, `mfa-server`, `mon-logging`).
3. **`vmbr2` (10.10.20.0/24)**: Enterprise DMZ (`pep-proxy`, `ent-vm-low`, `ent-vm-medium`).
4. **`vmbr3` (10.10.30.0/24)**: Enterprise Core DB (`ent-vm-critical` sensitivitas tinggi, hanya bisa diakses via otorisasi PEP).

### Fitur nftables Firewall

- **Default-Deny Forwarding**: Lalu lintas antar-VLAN diblokir secara default.
- **Dynamic Quarantine Set**: IP penyerang (CRITICAL risk) langsung dimasukkan ke kernel set `@quarantined_hosts` dengan tindakan drop instan.
- **Micro-segmentation**: Akses ke DB (Port 5432) hanya diizinkan dari IP DMZ tertentu setelah lolos inspeksi PDP.

---

## Milestone 4: Continuous Monitoring & Risk Re-evaluation

**Tanggal:** 2026-10-01

### File yang Dibuat / Diubah

| Kategori | File | Status |
|---|---|---|
| Monitor Engine | `src/monitoring/continuous.py` | Dibuat (Session registry, risk re-evaluation loop, adaptation event) |
| Tests | `tests/test_continuous_monitoring.py` | Dibuat (4 unit tests siklus sesi & adaptasi) |

### Mekanisme Continuous Monitoring

`ContinuousMonitor` menyediakan:
1. **Session registry**: Mendaftarkan sesi aktif beserta konteks, skor risiko saat ini, dan keputusan kebijakan.
2. **Re-evaluation sinkron**: `reevaluate_session_sync()` menghitung ulang skor risiko dari konteks terbaru dan membandingkannya dengan keputusan sebelumnya.
3. **Adaptation Event**: Jika level risiko atau keputusan berubah, event `AdaptationEvent` dibuat dengan:
   - `trigger_timestamp` = waktu terdeteksi perubahan risiko
   - `enforced_timestamp` = waktu kebijakan baru ditegakkan
   - `adaptation_time_ms` = selisih dalam milidetik (**Variabel Pengukuran ke-10**)
4. **Adaptive Action**:
   - LOW: `DOWNGRADE_TO_LOW_RISK`
   - MEDIUM: `STEP_UP_TOTP`
   - HIGH: `RESTRICT_AND_STEP_UP_WEBAUTHN`
   - CRITICAL: `REVOKE_AND_QUARANTINE` (sesi dimatikan, perangkat diisolasi)

### Keterbatasan (Limitations)

- Background async polling loop diimplementasikan tapi tidak diuji (butuh asyncio test harness terpisah)
- Re-evaluation saat ini sinkron; dalam produksi harus async background task

---

## Milestone 3: ZTNA Controller (PDP) & PEP Proxy

**Tanggal:** 2026-10-01

### File yang Dibuat / Diubah

| Kategori | File | Status |
|---|---|---|
| PDP Engine | `src/ztna_controller/pdp.py` | Dibuat (Logika Default-Deny, evaluasi risiko $\rightarrow$ keputusan Allow/Restrict/Deny) |
| PDP Service | `src/ztna_controller/app.py` | Diubah (Endpoint `/decide` terhubung dengan prometheus `POLICY_DECISION_LATENCY`) |
| PEP Proxy | `src/pep/proxy.py` | Dibuat (Pipeline integrasi: Context $\rightarrow$ Risk $\rightarrow$ PDP $\rightarrow$ MFA $\rightarrow$ Enforcement) |
| PEP Service | `src/pep/app.py` | Diubah (Endpoint `/enforce` & prometheus `PEP_REQUEST_LATENCY`) |
| Tests | `tests/test_ztna_controller.py` | Dibuat (10 test untuk PDP logic & integrasi endpoint /decide) |

### Mekanisme Enforcing PEP (Policy Enforcement Point)

PEP memproses setiap request melalui pipeline berikut:
1. Menghubungi Risk Engine `/evaluate` (latency diukur).
2. Menghubungi PDP `/decide` untuk matriks keputusan (latency diukur).
3. Mengeksekusi penolakan seketika (`HTTP 403`) jika PDP mengembalikan `DENY`.
4. Meminta klien melakukan langkah MFA (`HTTP 401`) jika PDP mengharuskan TOTP/WebAuthn namun klien belum terverifikasi.
5. Meneruskan (`HTTP 200`) klien ke _upstream resource_ dengan izin pembatasan (`read_write` atau `read_only`) jika semua syarat valid.

### Cara Menjalankan & Pengujian

```bash
# 1. Jalankan unit test gabungan (40 total tests passing)
.venv/Scripts/python.exe -m pytest tests/ -v

# 2. Pengujian Endpoint Enforce PEP
curl -X POST http://localhost:8000/enforce \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "user_id": "alice",
      "device": {"device_id": "laptop1"},
      "resource_requested": "/api/data"
    },
    "mfa_verified": false
  }'
```

### Keputusan Desain

1. **Dekopling PDP & PEP**: Pemisahan otorisasi (PDP) dari penegakan teknis (PEP) memungkinkan skalabilitas yang lebih baik. PEP tidak memiliki logika keputusan, hanya bertindak sebagai reverse-proxy gateway dan "polisi lalu lintas".
2. **Fail-Closed (Default-Deny)**: Apabila subsistem (Risk Engine / Controller) *down* atau membalas timeout, PEP otomatis menggugurkan sesi (mengembalikan HTTP 503 dengan status denied) untuk mencegah celah keamanan fail-open.
3. **Perekaman Latency End-to-end**: Setiap proses (Policy Engine maupun proxy pipeline) dilacak durasi prosesnya secara absolut. Sangat esensial untuk tujuan riset (Milestone 6).

---

## Milestone 2: MFA Server dan Adaptive MFA Policy

**Tanggal:** 2026-10-01

### File yang Dibuat / Diubah

| Kategori | File | Status |
|---|---|---|
| State Store | `src/mfa_server/store.py` | Dibuat (In-memory store untuk TOTP secret & WebAuthn challenges) |
| TOTP Logic | `src/mfa_server/totp.py` | Dibuat (TOTP enrollment, URI generation, & 6-digit code verification via `pyotp`) |
| WebAuthn | `src/mfa_server/webauthn_sim.py` | Dibuat (Simulasi WebAuthn/FIDO2 kriptografis dengan HMAC-SHA256 assertion) |
| Adaptive Policy | `src/mfa_server/policy.py` | Dibuat (Pemilihan faktor autentikasi berdasarkan `RiskLevel`) |
| FastAPI Service | `src/mfa_server/app.py` | Diubah (Endpoint `/policy`, `/totp/*`, `/webauthn/*`, & metrik latensi) |
| Tests | `tests/test_mfa_server.py` | Dibuat (Unit & integration test untuk MFA Server & Adaptive Policy) |

---

## Milestone 1: Risk Scoring Engine & Feature Normalization

**Tanggal:** 2026-10-01

### File yang Dibuat / Diubah

| Kategori | File | Status |
|---|---|---|
| Engine Source | `src/risk_engine/features.py` | Dibuat (Fungsi normalisasi 7 fitur konteks) |
| Engine Source | `src/risk_engine/engine.py` | Dibuat (Logika agregasi bobot, klasifikasi level, explainability) |
| Service | `src/risk_engine/app.py` | Diubah (Endpoint `POST /evaluate` & pencatatan Prometheus metrics) |
| Models | `src/common/models.py` | Diubah (Penambahan `behavioral_score` pada `AccessContext`) |
| Tests | `tests/test_risk_engine.py` | Dibuat (21 unit & integration test untuk Risk Engine) |

---

## Milestone 0: Struktur Repo & Environment Dev

**Tanggal:** 2026-10-01

### Progress Milestone

- [x] Milestone 0: Struktur Repo & Environment Dev
- [x] Milestone 1: Risk Engine (scoring, 7 fitur konteks, klasifikasi, explainable output, unit tests)
- [x] Milestone 2: MFA Server & Adaptive MFA Policy (TOTP enrollment & verify, WebAuthn sim, latency measurement)
- [x] Milestone 3: ZTNA Controller (PDP) & PEP (default deny, allow/deny/restrict, segmentation, latency tracking)
- [x] Milestone 4: Continuous Monitoring & Re-evaluation (loop, session re-eval, adaptation time measurement)
- [x] Milestone 5: Infrastruktur Proxmox (skrip VM, VLAN/bridge segmentation, guide)
- [x] Milestone 6: Harness Eksperimen (synthetic traffic, baseline vs static MFA vs proposed, 30x repetitions, statistical tests, plots)

### Jawaban untuk CLI 2

(Belum ada pertanyaan dari CLI 2 saat ini.)
