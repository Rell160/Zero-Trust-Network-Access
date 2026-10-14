#!/usr/bin/env bash
# ==============================================================================
# Proxmox VE Automated Testbed Provisioning Script
# ==============================================================================
# Research Study: "Risk-Aware Zero Trust Network Access with Adaptive Multi-Factor
# Authentication for Virtual Enterprise Networks: An Experimental Study Using a
# Proxmox-Based Testbed"
# ==============================================================================
# Usage:
#   chmod +x 01-setup-proxmox-vms.sh
#   ./01-setup-proxmox-vms.sh
# ==============================================================================

set -euo pipefail

# --- Configuration & Resource Allocation ---
STORAGE="local-lvm"
UBUNTU_CLOUD_IMAGE_URL="https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img"
IMAGE_NAME="jammy-server-cloudimg-amd64.img"
SNIPPETS_STORAGE="local"
SSH_PUB_KEY_PATH="${HOME}/.ssh/id_rsa.pub"

# Subnet Mapping:
#   vmbr0: Management / WAN Uplink (192.168.1.0/24)
#   vmbr1: ZTNA Control Plane (10.10.10.0/24)
#   vmbr2: Enterprise DMZ / Apps (10.10.20.0/24)
#   vmbr3: Enterprise Sensitive DB / Core (10.10.30.0/24)

# VM Specifications Matrix:
# VM_ID | NAME | RAM (MB) | CORES | IP / CIDR | VLAN / BRIDGE
declare -A VMS=(
    [101]="gw-firewall:2048:2:192.168.1.254/24:vmbr0"
    [102]="ztna-controller:2048:2:10.10.10.10/24:vmbr1"
    [103]="risk-engine:2048:2:10.10.10.11/24:vmbr1"
    [104]="mfa-server:2048:2:10.10.10.12/24:vmbr1"
    [105]="pep-proxy:2048:2:10.10.20.10/24:vmbr2"
    [106]="ent-vm-low:1024:1:10.10.20.101/24:vmbr2"
    [107]="ent-vm-medium:2048:2:10.10.20.102/24:vmbr2"
    [108]="ent-vm-critical:4096:2:10.10.30.103/24:vmbr3"
    [109]="mon-logging:4096:2:10.10.10.20/24:vmbr1"
)

echo "=== [1/4] Downloading Ubuntu Cloud-Init Image if missing ==="
if [ ! -f "/tmp/${IMAGE_NAME}" ]; then
    wget -q --show-progress -O "/tmp/${IMAGE_NAME}" "${UBUNTU_CLOUD_IMAGE_URL}"
fi

echo "=== [2/4] Ensuring Linux Bridges for Network Segmentation ==="
# Note: In Proxmox, /etc/network/interfaces configures bridges vmbr0, vmbr1, vmbr2, vmbr3.
# This script assumes vmbr1, vmbr2, vmbr3 are created or will create SDN bridges if supported.

echo "=== [3/4] Creating VM Template 9000 ==="
if ! qm status 9000 &>/dev/null; then
    qm create 9000 --name "ubuntu-cloud-template" --memory 2048 --cores 2 --net0 virtio,bridge=vmbr0
    qm importdisk 9000 "/tmp/${IMAGE_NAME}" "${STORAGE}"
    qm set 9000 --scsihw virtio-scsi-pci --scsi0 "${STORAGE}:vm-9000-disk-0"
    qm set 9000 --boot c --bootdisk scsi0
    qm set 9000 --ide2 "${STORAGE}:cloudinit"
    qm set 9000 --serial0 socket --vga serial0
    qm template 9000
    echo "Template 9000 created successfully."
else
    echo "Template 9000 already exists."
fi

echo "=== [4/4] Provisioning Testbed VMs from Template ==="
for VM_ID in "${!VMS[@]}"; do
    IFS=':' read -r VM_NAME MEM CORES IP BR <<< "${VMS[$VM_ID]}"

    if qm status "${VM_ID}" &>/dev/null; then
        echo "VM ${VM_ID} (${VM_NAME}) already exists, skipping creation."
        continue
    fi

    echo "Cloning VM ${VM_ID}: ${VM_NAME} (RAM: ${MEM}MB, Cores: ${CORES}, Bridge: ${BR}, IP: ${IP})..."
    qm clone 9000 "${VM_ID}" --name "${VM_NAME}" --full
    qm set "${VM_ID}" --memory "${MEM}" --cores "${CORES}"
    qm set "${VM_ID}" --net0 "virtio,bridge=${BR}"
    qm set "${VM_ID}" --ipconfig0 "ip=${IP},gw=10.10.10.1"

    if [ -f "${SSH_PUB_KEY_PATH}" ]; then
        qm set "${VM_ID}" --sshkey "${SSH_PUB_KEY_PATH}"
    fi

    qm resize "${VM_ID}" scsi0 +10G
    echo "VM ${VM_ID} provisioned."
done

echo "=== Proxmox Testbed VM Provisioning Completed Successfully ==="
