#!/usr/bin/env bash
set -e

source /opt/ros/jazzy/setup.bash

cd /snail_ws
# Build failures print the error but don't kill the container — you still get a shell to diagnose.
colcon build --symlink-install || echo "[entrypoint] BUILD FAILED — dropping to shell"

[ -f /snail_ws/install/setup.bash ] && source /snail_ws/install/setup.bash

exec "$@"
