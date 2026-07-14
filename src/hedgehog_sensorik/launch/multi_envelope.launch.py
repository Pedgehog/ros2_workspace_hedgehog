from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="tdk_ussm",
                executable="tdk_ussm_node",
                name="hedgehog_tdk_ussm_node",
            ),
            TimerAction(
                period=3.0,
                actions=[
                    Node(
                        package="hedgehog_sensorik",
                        executable="envelope_multi",
                        name="hedgehog_multi_envelope_node",
                    )
                ],
            ),
        ]
    )
