from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="tdk_ussm",
                executable="tdk_ussm_node",
                namespace="hedgehog",
                name="hedgehog_tdk_ussm_node",
            ),
            TimerAction(
                period=3.0,
                actions=[
                    Node(
                        package="hedgehog_sensorik",
                        executable="envelope_simple",
                        namespace="hedgehog",
                        name="hedgehog_simple_envelope_node",
                    )
                ],
            ),
        ]
    )
