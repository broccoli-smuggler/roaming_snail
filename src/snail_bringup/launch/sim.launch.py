"""Launch the Snail kart in Gazebo Harmonic with ros2_control controllers."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_description = get_package_share_directory('snail_description')
    pkg_bringup = get_package_share_directory('snail_bringup')
    pkg_gz = get_package_share_directory('snail_gz')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    world_file = os.path.join(pkg_gz, 'worlds', 'empty.sdf')
    urdf_xacro = os.path.join(pkg_description, 'urdf', 'snail.urdf.xacro')
    controllers_yaml = os.path.join(pkg_bringup, 'config', 'controllers.yaml')

    robot_description = {
        'robot_description': ParameterValue(
            Command([
                'xacro ', urdf_xacro,
                ' use_sim:=true',
                ' controllers_config:=', controllers_yaml,
            ]),
            value_type=str,
        ),
        'use_sim_time': True,
    }

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': '-r ' + world_file}.items(),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description],
    )

    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'snail',
            '-z', '0.05',
        ],
        output='screen',
    )

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen',
    )

    load_jsb = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        output='screen',
    )

    load_steering = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['snail_steering_controller', '--controller-manager', '/controller_manager'],
        output='screen',
    )

    cmd_vel_bridge = Node(
        package='snail_teleop',
        executable='cmd_vel_bridge',
        name='cmd_vel_bridge',
        output='screen',
        parameters=[{
            'input_topic': '/cmd_vel',
            'output_topic': '/snail_steering_controller/reference',
            'frame_id': 'base_link',
            'use_sim_time': True,
        }],
    )

    return LaunchDescription([
        gz_sim,
        clock_bridge,
        robot_state_publisher,
        spawn_entity,
        # Load controllers only once the entity is in the sim and ros2_control has come up.
        RegisterEventHandler(
            OnProcessExit(target_action=spawn_entity, on_exit=[load_jsb])
        ),
        RegisterEventHandler(
            OnProcessExit(target_action=load_jsb, on_exit=[load_steering])
        ),
        cmd_vel_bridge,
    ])
