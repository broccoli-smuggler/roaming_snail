"""Republish geometry_msgs/Twist as geometry_msgs/TwistStamped.

Bridges teleop_twist_keyboard (which only publishes unstamped Twist) into the
steering controller's stamped reference topic.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped


class CmdVelBridge(Node):

    def __init__(self):
        super().__init__('cmd_vel_bridge')
        self.declare_parameter('input_topic', '/cmd_vel')
        self.declare_parameter('output_topic',
                               '/snail_steering_controller/reference')
        self.declare_parameter('frame_id', 'base_link')

        in_topic = self.get_parameter('input_topic').value
        out_topic = self.get_parameter('output_topic').value
        self.frame_id = self.get_parameter('frame_id').value

        self.pub = self.create_publisher(TwistStamped, out_topic, 10)
        self.sub = self.create_subscription(Twist, in_topic, self._on_twist, 10)
        self.get_logger().info(
            'Bridging {} (Twist) -> {} (TwistStamped)'.format(in_topic, out_topic)
        )

    def _on_twist(self, msg: Twist) -> None:
        stamped = TwistStamped()
        stamped.header.stamp = self.get_clock().now().to_msg()
        stamped.header.frame_id = self.frame_id
        stamped.twist = msg
        self.pub.publish(stamped)


def main():
    rclpy.init()
    try:
        rclpy.spin(CmdVelBridge())
    finally:
        rclpy.shutdown()


if __name__ == '__main__':
    main()
