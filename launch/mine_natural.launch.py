"""Load selected mine world, publish existing robot URDF, then spawn robot."""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, EnvironmentVariable, PathJoinSubstitution
from launch_ros.actions import Node

def generate_launch_description():
    share = get_package_share_directory('survivor_sim')
    robot = os.path.join(share, 'urdf', 'survivor_classic.urdf')
    with open(robot) as f:
        description = f.read()
    return LaunchDescription([
        DeclareLaunchArgument('world_file', default_value='mine_natural_open.sdf'),
        # First directory resolves mine models; second resolves robot package meshes.
        SetEnvironmentVariable('GAZEBO_MODEL_PATH', [
            os.path.join(share, 'models'), ':', os.path.dirname(share), ':',
            EnvironmentVariable('GAZEBO_MODEL_PATH', default_value='')]),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')),
            launch_arguments={'world': PathJoinSubstitution([
                share, 'worlds', LaunchConfiguration('world_file')]),
                'verbose': 'true'}.items()),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': description, 'use_sim_time': True}],
             output='screen'),
        Node(package='gazebo_ros', executable='spawn_entity.py',
             arguments=['-entity', 'survivor', '-file', robot,
                        '-x', '0', '-y', '0', '-z', '0.015', '-timeout', '60'],
             output='screen'),
    ])
