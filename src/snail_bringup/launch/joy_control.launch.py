"""Launch joystick teleop (joy_node + teleop_twist_joy).

Reads snail.yaml for the joystick device path and joy_teleop.yaml for
axis/button mappings. Skips gracefully if no device is found.
"""

import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import LogInfo
from launch_ros.actions import Node


def generate_launch_description():
    pkg_bringup = get_package_share_directory('snail_bringup')
    snail_config_file = os.path.join(pkg_bringup, 'config', 'snail.yaml')
    joy_config_file = os.path.join(pkg_bringup, 'config', 'joy_teleop.yaml')

    with open(snail_config_file, 'r') as f:
        snail_params = yaml.safe_load(f)

    device_port = snail_params['/**']['ros__parameters']['joystick']['dev']

    ld = LaunchDescription()

    if not os.path.exists(device_port):
        ld.add_action(LogInfo(
            msg=f'No joystick detected at {device_port}, skipping joystick teleop'
        ))
        return ld

    ld.add_action(LogInfo(msg=f'Joystick detected at {device_port}, launching joystick teleop'))

    ld.add_action(Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        output='screen',
        parameters=[{'dev': device_port}],
    ))

    ld.add_action(Node(
        package='teleop_twist_joy',
        executable='teleop_node',
        name='teleop_node',
        output='screen',
        parameters=[joy_config_file],
        remappings=[('/cmd_vel', '/snail_steering_controller/reference')],
    ))

    return ld
