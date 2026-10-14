# Proxmox VE Testbed Setup Guide

> Comprehensive guide for deploying the Risk-Aware ZTNA Testbed on Proxmox VE.

## Network Topology & VLAN Segmentation

```
                        [ WAN / Internet (192.168.1.0/24) ]
                                        │
                                 [ vmbr0 Bridge ]
                                        │
                         ┌──────────────┴──────────────┐
                         │   gw-firewall (VM 101)      │
                         │   (nftables / Router)       │
                         └──────────────┬──────────────┘
                                        │
      ┌─────────────────────────────────┼─────────────────────────────────┐
      │ (Control Plane)                 │ (DMZ Apps)                      │ (Sensitive Core)
      ▼                                 ▼                                 ▼
 [ vmbr1: 10.10.10.0/24 ]          [ vmbr2: 10.10.20.0/24 ]          [ vmbr3: 10.10.30.0/24 ]
 ├─ ztna-controller (101)          ├─ pep-proxy (105)                └─ ent-vm-critical (108)
 ├─ risk-engine (102)              ├─ ent-vm-low (106)                   (DB / Core Credentials)
 ├─ mfa-server (103)               └─ ent-vm-medium (107)
 └─ mon-logging (109)
```

## Virtual Machine Inventory

| VM ID | Name | Subnet / IP | RAM | Cores | Network Segment | Role / Resource Sensitivity |
|---|---|---|---|---|---|---|
| **101** | `gw-firewall` | 192.168.1.254/24 | 2 GB | 2 | `vmbr0` (WAN/Mgmt) | Router, Firewall, Quarantine Enforcer |
| **102** | `ztna-controller` | 10.10.10.10/24 | 2 GB | 2 | `vmbr1` (Control) | Policy Decision Point (PDP) |
| **103** | `risk-engine` | 10.10.10.11/24 | 2 GB | 2 | `vmbr1` (Control) | Risk Scoring Engine |
| **104** | `mfa-server` | 10.10.10.12/24 | 2 GB | 2 | `vmbr1` (Control) | Adaptive MFA Server |
| **105** | `pep-proxy` | 10.10.20.10/24 | 2 GB | 2 | `vmbr2` (DMZ) | Policy Enforcement Point Gateway |
| **106** | `ent-vm-low` | 10.10.20.101/24 | 1 GB | 1 | `vmbr2` (DMZ) | Low Sensitivity App (Intranet News) |
| **107** | `ent-vm-medium` | 10.10.20.102/24 | 2 GB | 2 | `vmbr2` (DMZ) | Normal Sensitivity App (Wiki/Docs) |
| **108** | `ent-vm-critical` | 10.10.30.103/24 | 4 GB | 2 | `vmbr3` (Core) | Critical Sensitivity Resource (Database) |
| **109** | `mon-logging` | 10.10.10.20/24 | 4 GB | 2 | `vmbr1` (Control) | Prometheus & Grafana Server |

## Deployment Steps

### 1. Configure Linux Bridges on Proxmox Host

On your Proxmox VE Node shell (`/etc/network/interfaces`), add the following bridge definitions:

```etc
auto vmbr1
iface vmbr1 inet static
        address 10.10.10.1/24
        bridge-ports none
        bridge-stp off
        bridge-fd 0
# ZTNA Control Plane

auto vmbr2
iface vmbr2 inet static
        address 10.10.20.1/24
        bridge-ports none
        bridge-stp off
        bridge-fd 0
# Enterprise DMZ

auto vmbr3
iface vmbr3 inet static
        address 10.10.30.1/24
        bridge-ports none
        bridge-stp off
        bridge-fd 0
# Enterprise Core DB
```

Apply network changes with: `ifreload -a`

### 2. Run Automated Provisioning Script

Transfer `infra/proxmox/01-setup-proxmox-vms.sh` to the Proxmox host and execute:

```bash
chmod +x 01-setup-proxmox-vms.sh
./01-setup-proxmox-vms.sh
```

### 3. Deploy nftables Firewall Rules

On the gateway VM (`gw-firewall` - 101) or Proxmox host:

```bash
cp infra/firewall/nftables-ztna.conf /etc/nftables.conf
nft -f /etc/nftables.conf
systemctl enable --now nftables
```

### 4. Deploy ZTNA Microservices on VMs

Clone the repo onto each respective VM and start via systemd service or Docker:

```bash
# On ztna-controller (VM 102)
uvicorn src.ztna_controller.app:app --host 0.0.0.0 --port 8003

# On risk-engine (VM 103)
uvicorn src.risk_engine.app:app --host 0.0.0.0 --port 8001

# On mfa-server (VM 104)
uvicorn src.mfa_server.app:app --host 0.0.0.0 --port 8002

# On pep-proxy (VM 105)
uvicorn src.pep.app:app --host 0.0.0.0 --port 8000
```
