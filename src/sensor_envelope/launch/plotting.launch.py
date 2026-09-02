import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    namespace_arg = DeclareLaunchArgument(
        "namespace",
        default_value="tdk_robot/sensoric",
        description="Namespace for all nodes",
    )

    sensor_ids_arg = DeclareLaunchArgument(
        "sensor_ids",
        default_value="[0, 1, 2, 3, 4]",
        description="List of active sensors",
    )

    start_base_arg = DeclareLaunchArgument(
        "start_base",
        default_value="false",
        description="Start sensor base launch if not already running",
    )

    sensor_base_launch_path = os.path.join(
        FindPackageShare("sensor_envelope").find("sensor_envelope"),
        "launch",
        "sensor_base.launch.py",
    )

    sensor_base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(sensor_base_launch_path),
        launch_arguments={
            "namespace": LaunchConfiguration("namespace"),
            "sensor_ids": LaunchConfiguration("sensor_ids"),
            "start_ussm": "true",
        }.items(),
        condition=IfCondition(LaunchConfiguration("start_base")),
    )

    plotting_node = TimerAction(
        period=3.0,
        actions=[
            Node(
                package="sensor_envelope",
                executable="plotting_node",
                name="plotting_node",
                namespace=LaunchConfiguration("namespace"),  # <--- Hier direkt!
                parameters=[{"sensor_ids": LaunchConfiguration("sensor_ids")}],
                output="screen",
            )
        ],
    )

    return LaunchDescription(
        [
            namespace_arg,
            sensor_ids_arg,
            start_base_arg,
            sensor_base_launch,
            plotting_node,
        ]
    )
