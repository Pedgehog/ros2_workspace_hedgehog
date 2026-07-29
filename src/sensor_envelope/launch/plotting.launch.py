from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare("sensor_envelope")

    namespace_arg = DeclareLaunchArgument(
        "namespace",
        default_value="sensoric",
        description="Namespace for all nodes",
    )

    sensor_ids_arg = DeclareLaunchArgument(
        "sensor_ids",
        default_value="[0, 1, 2, 3, 4]",
        description="List of active sensors",
    )

    # Sensor-Base (USSM + Trigger) mit Namespace einbinden
    sensor_base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_share, "launch", "sensor_base.launch.py"])
        ),
        launch_arguments={
            "namespace": LaunchConfiguration("namespace"),
            "sensor_ids": LaunchConfiguration("sensor_ids"),
        }.items(),
    )

    # Plotting-Node mit demselben Namespace starten
    plotting_node = TimerAction(
        period=3.0,
        actions=[
            Node(
                package="sensor_envelope",
                executable="plotting_node",
                name="plotting_node",
                namespace=LaunchConfiguration("namespace"),
                parameters=[{"sensor_ids": LaunchConfiguration("sensor_ids")}],
                output="screen",
            )
        ],
    )

    return LaunchDescription(
        [
            namespace_arg,
            sensor_ids_arg,
            sensor_base_launch,
            plotting_node,
        ]
    )
