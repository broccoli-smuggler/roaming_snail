"""Launch keyboard teleop (teleop_twist_keyboard) in a dedicated xterm window."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='teleop_twist_keyboard',
            executable='teleop_twist_keyboard',
            name='teleop_keyboard',
            output='screen',
            prefix='xterm -e',
            parameters=[{'stamped': True}],
            remappings=[('/cmd_vel', '/snail_steering_controller/reference')],
        ),
    ])
