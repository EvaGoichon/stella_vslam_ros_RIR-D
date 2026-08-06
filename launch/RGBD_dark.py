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
        default_value=os.path.join(pkg_share, 'yaml', 'RGBD_dark.yaml'),
    )
    bag_file_arg = DeclareLaunchArgument(
        'bag_file',
        default_value=os.path.join(home_dir, 'data', 'AKDK', 'HDR_lab', 'dark.db3'),
    )
    bag_rate_arg = DeclareLaunchArgument(
        'bag_rate',
        default_value='1.0',
    )
    dimming_arg = DeclareLaunchArgument(
        'dimming',
        default_value='0',
    )

    # t=0s : occlusion via ExecuteProcess 
    occlusion_proc = ExecuteProcess(
        cmd=[
            os.path.join(os.path.expanduser('~'), 'ros2_ws', 'install',
                         'image_processing', 'lib', 'image_processing', 'occlusion'),
            '-i', 'rgb',
            '-m', 'dimming',
            '-r', LaunchConfiguration('dimming'),
        ],
        output='screen'
    )


    # t=5s : SLAM RGBD
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
                '--map-db-out', os.path.join(os.getcwd(), 'map_HDR_dark_RGBD.msg')
            ],
            output='screen'
        )]
    )

    # t=10s : bag
    bag_play = TimerAction(
        period=10.0,
        actions=[ExecuteProcess(
            cmd=[
                'ros2', 'bag', 'play',
                LaunchConfiguration('bag_file'),
                '--rate', LaunchConfiguration('bag_rate'),
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
        occlusion_proc,      # t=0s
        stella_vslam_node,   # t=5 : SLAM RGBD
        bag_play,            # t=10 : bag
    ])