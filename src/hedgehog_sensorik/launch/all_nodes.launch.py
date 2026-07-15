from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Argument definieren
    sensor_ids_arg = DeclareLaunchArgument(
        "sensor_ids",
        default_value="[1, 2, 3, 4]",
        description="Liste der aktiven Sensor-IDs",
    )

    pkg_share = FindPackageShare("hedgehog_sensorik")

    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_share, "launch", "cameras.launch.py"])
        )
    )

    sensor_logic_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_share, "launch", "plotter.launch.py"])
        ),
        launch_arguments={"sensor_ids": LaunchConfiguration("sensor_ids")}.items(),
    )

    return LaunchDescription([sensor_ids_arg, camera_launch, sensor_logic_launch])
