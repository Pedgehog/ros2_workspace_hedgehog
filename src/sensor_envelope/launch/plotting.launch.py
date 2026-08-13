from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare("sensor_envelope")

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
        description="Start sensor base nodes (USSM & Trigger) if not already running",
    )

    sensor_base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_share, "launch", "sensor_base.launch.py"])
        ),
        launch_arguments={
            "namespace": LaunchConfiguration("namespace"),
            "sensor_ids": LaunchConfiguration("sensor_ids"),
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
                namespace=LaunchConfiguration("namespace"),
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
