from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    namespace_arg = DeclareLaunchArgument(
        "namespace",
        default_value="tdk_robot/database",
        description="Namespace for all nodes",
    )

    namespace = LaunchConfiguration("namespace")

    database_node = Node(
        package="data_recording",
        executable="database_node",
        name="database_node",
        namespace=namespace,
        output="screen",
    )

    recording_controller_node = Node(
        package="data_recording",
        executable="recording_controller_node",
        name="recording_controller_node",
        namespace=namespace,
        output="screen",
    )

    return LaunchDescription(
        [
            namespace_arg,
            database_node,
            recording_controller_node,
        ]
    )
