# Snail Architecture

## Overview

```
        [Operator Laptop]
              │
            WiFi (ROS2 DDS, same domain ID)
              │
        [Onboard IoT Router]
              │
        [Raspberry Pi 5 — Ubuntu 24.04 + ROS2 Jazzy]
              │
              │  ROS2 nodes (in Docker container)
              │
              │  ┌────────────────────────┐
              │  │  teleop_twist_keyboard │  →  /cmd_vel
              │  └────────────────────────┘
              │                                  │
              │  ┌────────────────────────┐      │
              │  │ bicycle_steering_      │  ←───┘
              │  │ controller (stock)     │
              │  └────────────────────────┘
              │            │
              │            ▼  joint commands via ros2_control
              │  ┌────────────────────────┐
              │  │  snail_vesc            │   ←── hardware_interface plugin
              │  │  (SystemInterface)     │
              │  └────────────────────────┘
              │            │
              ▼      SocketCAN (can0)
        [Waveshare CAN HAT — MCP2515]
              │
        CAN bus @ 500kbps
              │
   ┌──────────┼──────────┬──────────┬──────────┐
   ▼          ▼          ▼          ▼          ▼
 VESC1      VESC2      VESC3      VESC4      VESC5
 (drive)    (drive)    (drive)    (drive)    (steer)
   └──── all four broadcast same cmd ────┘     │
   │                                            │
   ▼                                            ▼
 4× hoverboard hub motors                 1× steer hub motor
 (ganged to single drive axle)            + limit switch (homing)
```

## Sim vs hardware swap

Same controllers, same teleop, same launch files. Only the `hardware_interface` plugin differs:

| Mode | Plugin | Provided by |
|---|---|---|
| Sim | `gz_ros2_control/GazeboSimSystem` | `gz_ros2_control` package |
| Real | `snail_vesc/SnailVescSystem` | this repo |

Selected via `ros2_control` XML in the URDF (xacro arg `use_sim:=true|false`).

## Why this stack

| Choice | Reason |
|---|---|
| ROS2 over custom protocol | Eventual expansion (autonomy, telemetry, multiple inputs), stock teleop, easy WiFi via DDS |
| Gazebo Harmonic | Standard for ROS2 Jazzy; lets us test driving without hardware |
| `bicycle_steering_controller` | Stock controller fits 1-drive + 1-steer geometry; takes Twist directly |
| `python-can` + SocketCAN | Standard Linux CAN stack; SocketCAN is in mainline kernel; `python-can` is well-maintained |
| Multi-arch Docker | Develop on amd64 laptop, deploy to arm64 Pi without architecture surprises |
| Config-driven launch | Single YAML controls which nodes run (mirrors roboat2 pattern) |

## Control semantics

`bicycle_steering_controller` takes one `geometry_msgs/Twist`. Forward / reverse / regen are all encoded in `linear.x`:

| Operator intent | `linear.x` | VESC behavior |
|---|---|---|
| Drive forward | > 0 | Positive current, forward torque |
| Coast / soft stop | = 0 (while moving) | Velocity loop commands **negative current → regen** |
| Reverse | < 0 | Negative current, reverse torque |

Regen comes for free because we use `SET_RPM` (velocity setpoint) — VESC's internal PI loop generates braking current whenever commanded RPM is below actual.

**Regen floor**: VESC regen is ineffective below ~5–10% of max RPM. This is the gap a future friction brake fills.

### Topics by version

**v1 (now, no brake servo):**
```
/cmd_vel  (geometry_msgs/Twist)   ← teleop_twist_keyboard
   ├── linear.x   : drive velocity (regen automatic on decel, reverse on negative)
   └── angular.z  : angular velocity (controller derives steering angle)
```

**v2 (when brake servo is added):**
```
/cmd_vel       (Twist)         ← drive + steer (unchanged)
/snail/brake   (Float32, 0–1)  ← friction brake intensity, independent of /cmd_vel
```
The brake servo node will subscribe to `/snail/brake` directly. Teleop maps a separate key. Reserve this topic now so we don't paint ourselves into a corner.

### Panic stop

Operator-side soft stop = publish `linear.x = 0` at high rate (spacebar in teleop). Hardware E-Stop relay remains the actual safety device.

## E-Stop

**v1**: Physical inline relay on 48V supply. No software involvement.

**Future**: Add `snail_safety` package with `/snail/estop` topic; `snail_vesc` plugin subscribes and commands zero on receipt. Optionally an ESP32 watchdog monitoring an RPi heartbeat to cut power on hang.

## VESC CAN protocol

Standard VESC firmware CAN protocol. The frames we use:

| Frame | Purpose | Direction |
|---|---|---|
| `CAN_PACKET_SET_RPM` (0x03) | Drive wheel speed command | TX broadcast |
| `CAN_PACKET_SET_POS` (0x04) | Steer wheel position command | TX to one ID |
| `CAN_PACKET_SET_CURRENT_BRAKE` (0x02) | Optional brake current | TX broadcast |
| `CAN_PACKET_STATUS` (0x09) | RPM, current, duty | RX |
| `CAN_PACKET_STATUS_4` (0x10) | Temps, current_in | RX |
| `CAN_PACKET_STATUS_5` (0x1B) | Tachometer, voltage | RX |

Broadcast = send to CAN ID `0xFF` (extended ID upper byte `packet_id`). All VESCs configured with same params respond.

## Repository conventions

- All packages prefixed `snail_`
- Topics namespaced `/snail/...` or stock `/cmd_vel`, `/joint_states`
- Python over C++ where possible (only `snail_vesc` plugin must be C++ — `hardware_interface::SystemInterface` is a pluginlib C++ class)
- Pre-commit: black, isort, flake8 (light touch)
- No copyright headers required
