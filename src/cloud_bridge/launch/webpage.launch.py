import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    namespace_arg = DeclareLaunchArgument(
        "namespace",
        default_value="tdk_robot/web",
        description="Namespace for the webpage / cloud bridge node",
    )

    namespace = LaunchConfiguration("namespace")

    web_node = Node(
        package="cloud_bridge",
        executable="web_node",
        name="web_node",
        namespace=namespace,
        output="screen",
    )

    return LaunchDescription(
        [
            namespace_arg,
            web_node,
        ]
    )
