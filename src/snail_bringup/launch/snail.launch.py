"""Top-level Snail launch. Picks sim or hardware via `sim:=true|false`."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    sim = LaunchConfiguration('sim')

    sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution(
                [FindPackageShare('snail_bringup'), 'launch', 'sim.launch.py']
            )
        ]),
        condition=IfCondition(sim),
    )

    # hardware_launch will be wired in when snail_vesc is implemented.

    return LaunchDescription([
        DeclareLaunchArgument(
            'sim', default_value='true',
            description='Run in Gazebo Harmonic if true, real hardware if false'
        ),
        sim_launch,
    ])
