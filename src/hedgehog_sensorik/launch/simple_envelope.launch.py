from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            # 1. Hardware Node starten
            Node(
                package="tdk_ussm",
                executable="tdk_ussm_node",
                name="hedgehog_tdk_ussm_node",
            ),
            # 2. Analyse Node mit 3s Verzögerung starten
            TimerAction(
                period=3.0,
                actions=[
                    Node(
                        package="hedgehog_sensorik",
                        executable="envelope_simple",
                        name="hedgehog_simple_envelope_node",
                    )
                ],
            ),
        ]
    )
