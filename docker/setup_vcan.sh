#!/usr/bin/env bash
# Bring up a virtual CAN interface (vcan0) on the host.
#
# vcan is a kernel module — it must be loaded on the host, not inside the
# container. Once `vcan0` exists, the container sees it via `--net=host`.
#
# Idempotent: re-running won't error if vcan is already loaded or vcan0 exists.
#
# Usage:
#     ./docker/setup_vcan.sh         # default: vcan0 @ 500 kbit (virtual)
#     IFACE=vcan1 ./docker/setup_vcan.sh
set -euo pipefail

IFACE="${IFACE:-vcan0}"

if ! lsmod | grep -q '^vcan'; then
    echo "Loading vcan kernel module..."
    sudo modprobe vcan
fi

if ip link show "${IFACE}" >/dev/null 2>&1; then
    echo "Interface ${IFACE} already exists."
else
    echo "Creating ${IFACE}..."
    sudo ip link add dev "${IFACE}" type vcan
fi

if [[ "$(ip -br link show "${IFACE}" | awk '{print $2}')" != "UP" ]]; then
    echo "Bringing ${IFACE} up..."
    sudo ip link set up "${IFACE}"
fi

echo
echo "${IFACE} ready:"
ip -br link show "${IFACE}"
echo
echo "Verify with:  candump ${IFACE}"
echo "Send a test:  cansend ${IFACE} 123#DEADBEEF"
