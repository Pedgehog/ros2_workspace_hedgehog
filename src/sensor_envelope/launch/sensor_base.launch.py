from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


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

    tdk_ussm_node = Node(
        package="tdk_ussm",
        executable="tdk_ussm_node",
        name="tdk_ussm_node",
        parameters=[
            {
                "com_port": "/dev/tdk_ussm",
                "avg_window": 5,
                "sensor_ids": LaunchConfiguration("sensor_ids"),
            }
        ],
        output="screen",
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
            tdk_ussm_node,
            trigger_node,
        ]
    )
