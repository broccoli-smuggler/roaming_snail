#!/usr/bin/env python3
"""Translate /cmd_vel into VESC CAN commands.

In sim mode (use_sim:=true)  : logs the frames that would be sent.
In real mode (use_sim:=false): broadcasts over SocketCAN via python-can.

Steer angle: atan(wheelbase * angular_z / linear_x)  — standard Ackermann / tricycle formula.
             Multiplied by steering_gear_ratio to get motor shaft degrees.
Drive eRPM:  linear_x / wheel_radius * 60 / (2π) * pole_pairs  (broadcast to all drive VESCs).
"""

import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped

from snail_vesc import vesc_protocol as vp

# Below this speed the steer angle is held rather than recomputed — avoids
# division by zero and prevents the wheels snapping to centre when stopped.
_MINIMUM_LINEAR_VELOCITY_FOR_STEER = 0.05  # m/s


class VescNode(Node):
    def __init__(self) -> None:
        super().__init__('snail_vesc')

        self.declare_parameter('use_sim',                   True)
        self.declare_parameter('can_interface',             'can0')
        self.declare_parameter('drive_ids',                 [1, 2, 3, 4])
        self.declare_parameter('steer_id',                  5)
        self.declare_parameter('pole_pairs',                7)
        self.declare_parameter('wheelbase',                 1.60)
        self.declare_parameter('wheel_radius',              0.19)
        self.declare_parameter('maximum_steering_degrees',  45.0)
        self.declare_parameter('steering_gear_ratio',       1.0)

        self._use_sim                  = self.get_parameter('use_sim').value
        self._drive_ids                = self.get_parameter('drive_ids').value
        self._steer_id                 = self.get_parameter('steer_id').value
        self._pole_pairs               = self.get_parameter('pole_pairs').value
        self._wheelbase                = self.get_parameter('wheelbase').value
        self._wheel_radius             = self.get_parameter('wheel_radius').value
        self._maximum_steering_degrees = self.get_parameter('maximum_steering_degrees').value
        self._steering_gear_ratio      = self.get_parameter('steering_gear_ratio').value

        self._can_bus = None
        if not self._use_sim:
            import can
            can_interface_name = self.get_parameter('can_interface').value
            self._can_bus = can.interface.Bus(channel=can_interface_name, bustype='socketcan')
            self.get_logger().info(f'CAN bus open on {can_interface_name}')
        else:
            self.get_logger().info('sim mode — CAN frames will be logged, not sent')

        self._last_steering_degrees = 0.0

        self.create_subscription(TwistStamped, '/cmd_vel', self._on_cmd_vel, 10)

    def _on_cmd_vel(self, msg: TwistStamped) -> None:
        linear_x  = msg.twist.linear.x
        angular_z = msg.twist.angular.z

        electrical_rpm = int(round(
            linear_x / self._wheel_radius * 60.0 / math.tau * self._pole_pairs
        ))

        if abs(linear_x) >= _MINIMUM_LINEAR_VELOCITY_FOR_STEER:
            steering_degrees = math.degrees(
                math.atan(self._wheelbase * angular_z / linear_x)
            )
            # Clamp to physical joint limits — atan can exceed the limit at low speed.
            steering_degrees = max(
                -self._maximum_steering_degrees,
                min(self._maximum_steering_degrees, steering_degrees),
            )
            self._last_steering_degrees = steering_degrees

        motor_position_degrees = self._last_steering_degrees * self._steering_gear_ratio

        drive_can_frames = [
            (vp.make_frame_id(vp.VescPacketId.SET_RPM, vesc_id), vp.encode_set_rpm(electrical_rpm))
            for vesc_id in self._drive_ids
        ]
        steering_can_frame = (
            vp.make_frame_id(vp.VescPacketId.SET_POS, self._steer_id),
            vp.encode_set_pos(motor_position_degrees),
        )

        if self._use_sim:
            self._log_can_frames(electrical_rpm, self._last_steering_degrees, motor_position_degrees, drive_can_frames, steering_can_frame)
        else:
            self._send_can_frames(drive_can_frames, steering_can_frame)

    def _log_can_frames(self, electrical_rpm, steering_degrees, motor_position_degrees, drive_can_frames, steering_can_frame) -> None:
        lines = [
            f'  eRPM={electrical_rpm:+7d}  '
            f'steer={steering_degrees:+7.2f} deg  '
            f'motor={motor_position_degrees:+8.2f} deg'
        ]
        for frame_id, data in drive_can_frames:
            lines.append(f'    DRIVE  frame_id=0x{frame_id:04X}  data={data.hex()}')
        frame_id, data = steering_can_frame
        lines.append(f'    STEER  frame_id=0x{frame_id:04X}  data={data.hex()}')
        self.get_logger().info('\n' + '\n'.join(lines))

    def _send_can_frames(self, drive_can_frames, steering_can_frame) -> None:
        import can
        for frame_id, data in drive_can_frames:
            self._can_bus.send(can.Message(
                arbitration_id=frame_id, data=data, is_extended_id=True))
        frame_id, data = steering_can_frame
        self._can_bus.send(can.Message(
            arbitration_id=frame_id, data=data, is_extended_id=True))

    def destroy_node(self) -> None:
        if self._can_bus is not None:
            self._can_bus.shutdown()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = VescNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
