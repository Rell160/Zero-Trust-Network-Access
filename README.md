# Risk-Aware Zero Trust Network Access with Adaptive MFA

> An experimental study using a Proxmox-based testbed for virtual enterprise networks.

## Architecture Overview

```
User/Device
    │
    ▼
┌───────────────────────────────┐
│ Identity & Device Verification│
└───────────────┬───────────────┘
                ▼
┌───────────────────────────────┐
│       Context Collection      │◄───────────────────────────┐
└───────────────┬───────────────┘                            │
                ▼                                            │
┌───────────────────────────────┐                            │
│      Risk Scoring Engine      │ (Port 8001)                │
└───────────────┬───────────────┘                            │
                ▼                                            │
┌───────────────────────────────┐                            │
│   Risk Level Classification   │                            │
└───────────────┬───────────────┘                            │
                ▼                                            │
┌───────────────────────────────┐                            │
│      Adaptive MFA Policy      │ (Port 8002)                │
└───────────────┬───────────────┘                            │
                ▼                                            │
┌───────────────────────────────┐                            │
│     ZTNA Policy Decision      │ (Port 8003)                │
└───────────────┬───────────────┘                            │
                ▼                                            │
┌───────────────────────────────┐                            │
│ Dynamic Access Control (PEP)  │ (Port 8000)                │
└───────────────┬───────────────┘                            │
                ▼                                            │
┌───────────────────────────────┐                            │
│     Continuous Monitoring     │────────────────────────────┘
└───────────────────────────────┘   (Re-evaluation loop)
```

## Risk Level Policy

| Score Range | Level    | Auth Required         | Access Policy                                    |
|-------------|----------|-----------------------|--------------------------------------------------|
| 0 – 29      | Low      | Password only         | Full access to requested resource               |
| 30 – 59     | Medium   | Password + TOTP       | Full access to requested resource               |
| 60 – 84     | High     | Password + WebAuthn   | Restricted (read-only, limited network segments) |
| 85 – 100    | Critical | Access DENIED         | Device quarantined                               |

## Quick Start (Development Mode)

### Prerequisites

- Python 3.11+
- Windows 11 with PowerShell & Docker Desktop (WSL2 backend)
- Git

### Local Development (without Docker)

```bash
# Clone and enter the repo
git clone <repo-url>
cd Zero_Trust

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Run individual services
uvicorn src.risk_engine.app:app --port 8001 --reload
uvicorn src.mfa_server.app:app --port 8002 --reload
uvicorn src.ztna_controller.app:app --port 8003 --reload
uvicorn src.pep.app:app --port 8000 --reload
```

### Docker Compose (All Services)

```powershell
# Copy environment file (PowerShell)
Copy-Item .env.example .env

# Start all services
docker compose up -d --build

# Check service health
curl http://localhost:8001/health   # Risk Engine
curl http://localhost:8002/health   # MFA Server
curl http://localhost:8003/health   # ZTNA Controller
curl http://localhost:8000/health   # PEP

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Makefile Shortcuts

```bash
make install    # Install Python dependencies
make dev-up     # Start Docker Compose
make dev-down   # Stop Docker Compose
make test       # Run pytest
make lint       # Check with ruff
make format     # Format with ruff
make clean      # Clean cache files
```

## Project Structure

```
├── config/              # YAML configuration & Prometheus config
├── src/
│   ├── common/          # Shared utilities (config, logging, models)
│   ├── risk_engine/     # Risk scoring service (FastAPI)
│   ├── mfa_server/      # MFA service (TOTP + WebAuthn sim)
│   ├── ztna_controller/ # Policy Decision Point (FastAPI)
│   ├── pep/             # Policy Enforcement Point (FastAPI)
│   └── monitoring/      # Prometheus metrics definitions
├── infra/               # Proxmox VE provisioning scripts
├── experiments/         # Experiment harness & analysis scripts
│   └── results/         # Raw CSV results & plots
├── tests/               # Pytest test suite
├── docs/                # Documentation & handoff notes
├── docker-compose.yml   # Dev orchestration
├── Dockerfile           # Container image
├── Makefile             # Dev automation
└── requirements.txt     # Python dependencies
```

## Measured Variables

1. Authentication latency
2. ZTNA policy decision latency
3. MFA response time
4. False Acceptance Rate (FAR)
5. False Rejection Rate (FRR)
6. Unauthorized access prevention rate
7. Network overhead
8. CPU/RAM utilization per VM
9. Access-control accuracy
10. Adaptation time

## License

This project uses only open-source tools.
