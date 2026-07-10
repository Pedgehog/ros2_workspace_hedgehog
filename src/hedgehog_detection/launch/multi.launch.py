from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(package="tdk_ussm", executable="tdk_ussm_node", name="tdk_ussm_node"),
            TimerAction(
                period=3.0,
                actions=[
                    Node(
                        package="hedgehog_detection",
                        executable="envelope_multi",
                        name="multi_envelope_node",
                    )
                ],
            ),
        ]
    )
