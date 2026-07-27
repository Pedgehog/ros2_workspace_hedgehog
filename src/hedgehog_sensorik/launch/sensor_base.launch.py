from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    sensor_ids_arg = DeclareLaunchArgument(
        "sensor_ids",
        default_value="[1, 2, 3, 4]",
        description="List of the active sensors",
    )

    tdk_node = Node(
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
    )

    trigger_node = TimerAction(
        period=3.0,
        actions=[
            Node(
                package="hedgehog_sensorik",
                executable="trigger_node",
                name="trigger_node",
                parameters=[{"sensor_ids": LaunchConfiguration("sensor_ids")}],
            )
        ],
    )

    return LaunchDescription([sensor_ids_arg, tdk_node, trigger_node])
