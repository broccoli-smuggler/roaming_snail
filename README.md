# Snail

Remote-controlled go-kart. ROS2 Jazzy, Gazebo Harmonic, ros2_control.

- 4 drive motors (hoverboard hub motors, VESC IDs 1–4 on CAN, all get the same eRPM — passive diff handles the rest)
- 1 steering motor (VESC ID 5, position controlled)
- Rear-steered tricycle kinematics

## Quick start (sim)

```bash
# Build image once (or after Dockerfile changes)
docker buildx build -t snail:latest .

# Launch sim — builds workspace automatically on first run
./docker/run.sh ros2 launch snail_bringup sim.launch.py
```

An xterm window opens for keyboard teleop. Click it to give focus, then use the standard `teleop_twist_keyboard` keys.

To get a shell inside the running container:

```bash
docker exec -it snail bash
```

## Workspace layout

| Package | Purpose |
|---|---|
| `snail_description` | URDF (xacro), ros2_control tags, Gazebo plugin |
| `snail_bringup` | Launch files, all tunable config in `config/snail.yaml` |
| `snail_vesc` | CAN protocol library + ROS2 node (sim: logs frames, real: sends over SocketCAN) |
| `snail_gz` | Gazebo world |

## Configuration

All hardware parameters are in `src/snail_bringup/config/snail.yaml`:

```yaml
vesc:
  can_interface: can0
  drive_ids: [1, 2, 3, 4]
  steer_id: 5
  pole_pairs: 7           # electrical pole pairs of the drive motors
  wheelbase: 1.60         # metres
  wheel_radius: 0.19      # metres
  maximum_steering_degrees: 60.0
  steering_gear_ratio: 1.0  # motor shaft degrees per steering degree — measure at bringup
```

Teleop mode (`keyboard` or `joy`) is also set in `snail.yaml`.

## Hardware

- Raspberry Pi 5 (Ubuntu 24.04 / ROS2 Jazzy)
- Waveshare 2-CH CAN HAT (MCP2515) @ 500 kbps
- 5× VESC controllers
- 4× hoverboard hub motors (drive), 1× hub motor (steer)
- 48 V system, physical inline E-Stop relay

To bring up the virtual CAN interface on the host before running in hardware mode:

```bash
./docker/setup_vcan.sh   # vcan0 for testing without physical hardware
```
