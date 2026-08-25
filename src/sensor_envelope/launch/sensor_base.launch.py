import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    namespace_arg = DeclareLaunchArgument(
        "namespace",
        default_value="tdk_robot/sensoric",
        description="Namespace for custom nodes",
    )

    sensor_ids_arg = DeclareLaunchArgument(
        "sensor_ids",
        default_value="",
        description="List of active sensors",
    )

    start_ussm_arg = DeclareLaunchArgument(
        "start_ussm",
        default_value="false",
        description="True or false to start ussm sensor launch",
    )

    ussm_launch_path = os.path.join(
        FindPackageShare("tdk_ussm_backup").find("tdk_ussm_backup"),
        "launch",
        "ussm_sensor_board.launch.py",
    )

    ussm_sensor_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(ussm_launch_path),
        launch_arguments={"namespace": LaunchConfiguration("namespace")}.items(),
        condition=IfCondition(LaunchConfiguration("start_ussm")),
    )

    trigger_node = Node(
        package="sensor_envelope",
        executable="trigger_node",
        name="trigger_node",
        namespace=LaunchConfiguration("namespace"),
        parameters=[{"sensor_ids": LaunchConfiguration("sensor_ids")}],
        output="screen",
    )

    return LaunchDescription(
        [
            namespace_arg,
            sensor_ids_arg,
            start_ussm_arg,
            ussm_sensor_launch,
            trigger_node,
        ]
    )
