from launch import LaunchDescription
from launch.actions import TimerAction, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    sensor_ids_arg = DeclareLaunchArgument(
        "sensor_ids",
        default_value="[1, 2, 3, 4]",
        description="List of the active sensors",
    )

    tdk_node = Node(
        package="tdk_ussm", executable="tdk_ussm_node", name="tdk_ussm_node"
    )

    trigger_node = TimerAction(
        period=3.0,
        actions=[
            Node(
                package="hedgehog_sensorik",
                executable="trigger_node",
                name="trigger_node",
                # Nutze die LaunchConfiguration für den Parameter
                parameters=[{"sensor_ids": LaunchConfiguration("sensor_ids")}],
            )
        ],
    )

    return LaunchDescription([sensor_ids_arg, tdk_node, trigger_node])
