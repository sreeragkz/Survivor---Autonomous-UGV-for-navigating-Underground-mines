import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    package_path = get_package_share_directory('survivor_sim')
    gazebo_path = get_package_share_directory('gazebo_ros')

    world_path = os.path.join(
        package_path, 'worlds', 'mine_classic.sdf'
    )
    robot_path = os.path.join(
        package_path, 'urdf', 'survivor_classic.urdf'
    )

    with open(robot_path) as file:
        robot_description = file.read()

    # Start Gazebo with the mine and ROS spawning services.
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_path, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={'world': world_path}.items(),
    )

    # Publish the robot's link transforms from its URDF and joint states.
    state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }],
        output='screen',
    )

    # Wait for Gazebo's spawning service, then insert the robot.
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'survivor',
            '-file', robot_path,
            '-x', '0',
            '-y', '0',
            '-z', '0.015',
            '-timeout', '60',
        ],
        output='screen',
    )

    return LaunchDescription([
        gazebo,
        state_publisher,
        spawn_robot,
    ])