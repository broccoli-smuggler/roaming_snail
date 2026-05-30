#!/usr/bin/env bash
# Convenience launcher for the Snail dev container (host networking + X11 for Gazebo/RViz).
set -euo pipefail

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Allow local X11 connections so Gazebo/RViz windows show up.
xhost +local:docker >/dev/null 2>&1 || true

exec docker run -it --rm \
  --name snail \
  --net=host \
  --ipc=host \
  --privileged \
  -e DISPLAY="${DISPLAY:-:0}" \
  -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "${WS_DIR}":/snail_ws \
  -w /snail_ws \
  snail:latest \
  "$@"
