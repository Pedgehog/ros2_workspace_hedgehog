from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare("hedgehog_sensorik")

    # 1. Argument definieren
    sensor_ids_arg = DeclareLaunchArgument(
        "sensor_ids",
        default_value="[1, 2, 3, 4]",
        description="List of the active sensors",
    )

    base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_share, "launch", "sensor_base.launch.py"])
        ),
        launch_arguments={"sensor_ids": LaunchConfiguration("sensor_ids")}.items(),
    )

    # 3. Plotting Node mit LaunchConfiguration
    plotting_node = TimerAction(
        period=5.0,
        actions=[
            Node(
                package="hedgehog_sensorik",
                executable="plotting_node",
                name="plotting_node",
                parameters=[{"sensor_ids": LaunchConfiguration("sensor_ids")}],
            )
        ],
    )

    return LaunchDescription([sensor_ids_arg, base_launch, plotting_node])
