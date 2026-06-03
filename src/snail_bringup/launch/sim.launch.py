"""Launch the Snail kart in Gazebo Harmonic with ros2_control controllers."""

import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node, SetParameter
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_description = get_package_share_directory('snail_description')
    pkg_bringup = get_package_share_directory('snail_bringup')
    pkg_gz = get_package_share_directory('snail_gz')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    snail_config_file = os.path.join(pkg_bringup, 'config', 'snail.yaml')
    world_file = os.path.join(pkg_gz, 'worlds', 'empty.sdf')
    urdf_xacro = os.path.join(pkg_description, 'urdf', 'snail.urdf.xacro')
    controllers_yaml = os.path.join(pkg_bringup, 'config', 'controllers.yaml')

    with open(snail_config_file, 'r') as f:
        snail_params = yaml.safe_load(f)

    ros_parameters = snail_params['/**']['ros__parameters']
    teleop_mode = ros_parameters.get('teleop', 'joy')
    vesc_params = ros_parameters.get('vesc', {})

    robot_description = {
        'robot_description': ParameterValue(
            Command([
                'xacro ', urdf_xacro,
                ' use_sim:=true',
                ' controllers_config:=', controllers_yaml,
            ]),
            value_type=str,
        ),
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

    vesc_node = Node(
        package='snail_vesc',
        executable='vesc_node',
        name='snail_vesc',
        output='screen',
        parameters=[{
            'use_sim': True,
            'drive_ids':                vesc_params.get('drive_ids', [1, 2, 3, 4]),
            'steer_id':                 vesc_params.get('steer_id', 5),
            'pole_pairs':               vesc_params.get('pole_pairs', 7),
            'wheelbase':                vesc_params.get('wheelbase', 1.60),
            'wheel_radius':             vesc_params.get('wheel_radius', 0.19),
            'maximum_steering_degrees': vesc_params.get('maximum_steering_degrees', 45.0),
            'steering_gear_ratio':      vesc_params.get('steering_gear_ratio', 1.0),
        }],
        remappings=[('/cmd_vel', '/snail_steering_controller/reference')],
    )

    if teleop_mode == 'keyboard':
        teleop_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_bringup, 'launch', 'keyboard_control.launch.py')
            ),
        )
    else:
        teleop_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_bringup, 'launch', 'joy_control.launch.py')
            ),
        )

    return LaunchDescription([
        SetParameter(name='use_sim_time', value=True),
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
        teleop_launch,
        vesc_node,
    ])
