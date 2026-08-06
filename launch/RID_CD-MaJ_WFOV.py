#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, TimerAction, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_share = get_package_share_directory('stella_vslam_ros')
    home_dir = os.path.expanduser('~')

    vocab_file_arg = DeclareLaunchArgument(
        'vocab_file',
        default_value=os.path.join(home_dir, 'data', 'orb_vocab.fbow'),
    )
    config_file_arg = DeclareLaunchArgument(
        'config_file',
        default_value=os.path.join(pkg_share, 'yaml', 'RID_WFOV.yaml'),
    )
    bag_file_arg = DeclareLaunchArgument(
        'bag_file',
        default_value=os.path.join(home_dir, 'data', 'AKDK', 'CD-MaJ',
                                   'WFOV_Unbinned_15HZ', 'WFOV_Unbinned_15HZ.db3'),
    )
    bag_rate_arg = DeclareLaunchArgument('bag_rate', default_value='1.0')
    dimming_arg  = DeclareLaunchArgument('dimming',  default_value='0.0')

    # /k4a/rgb/image_raw/compressed -> /rgb/image_raw
    rgb_decompressor = Node(
        package='image_transport',
        executable='republish',
        name='rgb_decompressor',
        arguments=['compressed', 'raw'],
        remappings=[
            ('in/compressed', '/k4a/rgb/image_raw/compressed'),
            ('out',           '/rgb/image_raw'),
        ],
        output='screen'
    )

    # /k4a/depth_to_rgb/image_raw -> /depth_to_rgb/image_raw
    depth_to_rgb_republisher = Node(
        package='image_transport',
        executable='republish',
        name='depth_to_rgb_republisher',
        arguments=['raw'],
        remappings=[
            ('in',  '/k4a/depth_to_rgb/image_raw'),
            ('out', '/depth_to_rgb/image_raw'),
        ],
        output='screen'
    )

    # /k4a/depth/image_raw -> /depth/image_raw
    depth_ir_republisher = Node(
        package='image_transport',
        executable='republish',
        name='depth_ir_republisher',
        arguments=['raw'],
        remappings=[
            ('in',  '/k4a/depth/image_raw'),
            ('out', '/depth/image_raw'),
        ],
        output='screen'
    )

    # /k4a/ir/image_raw -> /ir/image_raw
    ir_republisher = Node(
        package='image_transport',
        executable='republish',
        name='ir_republisher',
        arguments=['raw'],
        remappings=[
            ('in',  '/k4a/ir/image_raw'),
            ('out', '/ir/image_raw'),
        ],
        output='screen'
    )

    # /ir/image_raw -> /ir_processed/image_raw
    active_ir_processor = Node(
        package='image_processing',
        executable='active_ir_processor',
        name='active_ir_processor',
        output='screen'
    )


    occlusion_proc = ExecuteProcess(
        cmd=[
            os.path.join(home_dir, 'ros2_ws', 'install',
                         'image_processing', 'lib', 'image_processing', 'occlusion'),
            '-i', 'rgb',
            '-m', 'dimming',
            '-r', LaunchConfiguration('dimming'),
        ],
        output='screen'
    )


    stella_vslam_node = TimerAction(
        period=5.0,
        actions=[Node(
            package='stella_vslam_ros',
            executable='run_slam',
            name='stella_vslam',
            arguments=[
                '-v', LaunchConfiguration('vocab_file'),
                '-c', LaunchConfiguration('config_file'),
                '--eval-log',
                '--map-db-out', os.path.join(os.getcwd(), 'map_WFOV_u_15Hz_RID.msg'),
            ],
            output='screen'
        )]
    )


    bag_play = TimerAction(
        period=20.0,
        actions=[ExecuteProcess(
            cmd=[
                'ros2', 'bag', 'play',
                LaunchConfiguration('bag_file'),
                '--rate', LaunchConfiguration('bag_rate'),
                '--topics',
                '/k4a/rgb/image_raw/compressed',
                '/k4a/ir/image_raw',
                '/k4a/depth_to_rgb/image_raw',
                '/k4a/depth/image_raw',
            ],
            output='screen'
        )]
    )

    return LaunchDescription([
        vocab_file_arg,
        config_file_arg,
        bag_file_arg,
        bag_rate_arg,
        dimming_arg,
        rgb_decompressor,          # t=0s  /k4a/rgb/compressed -> /rgb/image_raw
        depth_to_rgb_republisher,  # t=0s  /k4a/depth_to_rgb   -> /depth_to_rgb/image_raw
        depth_ir_republisher,      # t=0s  /k4a/depth          -> /depth/image_raw
        ir_republisher,            # t=0s  /k4a/ir             -> /ir/image_raw
        active_ir_processor,       # t=0s  /ir/image_raw       -> /ir_processed/image_raw
        occlusion_proc,            # t=0s  -> /camera/*/image_raw
        stella_vslam_node,         # t=5s 
        bag_play,                  # t=20s
    ])
