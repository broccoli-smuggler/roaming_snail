# Snail

Remote-controlled kart. ROS2 Jazzy, Gazebo Harmonic, ros2_control.

- 1 drive wheel (4 VESC motor controllers on CAN, broadcast)
- 1 steered wheel (1 VESC, position controlled, limit-switch homing)
- Bicycle kinematics, rear-steered

## Quick start (sim)

```bash
# Build inside devcontainer
colcon build --symlink-install
source install/setup.bash

# Bring up Gazebo + controllers
ros2 launch snail_bringup snail.launch.py sim:=true

# In another terminal: drive
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## Workspace layout

| Package | Purpose |
|---|---|
| `snail_description` | URDF (xacro) + ros2_control tags |
| `snail_bringup` | Top-level launch + config (YAML-driven) |
| `snail_vesc` | Hardware interface plugin (SocketCAN → VESCs) |
| `snail_teleop` | Input devices |
| `snail_gz` | Gazebo worlds + spawn launch |

Uses stock messages only: `geometry_msgs/Twist`, `sensor_msgs/JointState`, `std_msgs/Float32`.

## Hardware

- Raspberry Pi 5 (Ubuntu 24.04)
- Waveshare 2-CH CAN HAT (MCP2515)
- 5x VESC controllers on CAN bus @ 500kbps
- 4x hoverboard hub motors (drive), 1x hub motor (steer)
- 48V system, physical inline E-Stop relay

See `docs/` for design notes.
