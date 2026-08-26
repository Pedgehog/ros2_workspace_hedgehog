import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Absoluter Start-Namespace
    namespace_arg = DeclareLaunchArgument(
        "namespace",
        default_value="/tdk_robot",
        description="Namespace for all nodes",
    )

    ns = LaunchConfiguration("namespace")

    # --------------- Sensor (Eingekapselt) --------------- #
    sensor_base_launch_path = os.path.join(
        FindPackageShare("sensor_envelope").find("sensor_envelope"),
        "launch",
        "sensor_base.launch.py",
    )

    sensor_group = GroupAction(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(sensor_base_launch_path),
                launch_arguments={
                    "namespace": [ns, "/sensoric"],
                    "sensor_ids": "[1,2,3,4,5,6]",
                    "start_ussm": "true",
                }.items(),
            )
        ]
    )

    # --------------- Camera (Eingekapselt) --------------- #
    camera_control_dir = get_package_share_directory("camera_control")

    camera_group = GroupAction(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(camera_control_dir, "launch", "usb_cam.launch.py")
                ),
                launch_arguments={
                    "namespace": [ns, "/sensoric/camera"],
                }.items(),
            )
        ]
    )

    # --------------- Webpage (Eingekapselt) --------------- #
    webpage_dir = get_package_share_directory("cloud_bridge")

    web_group = GroupAction(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(webpage_dir, "launch", "webpage.launch.py")
                ),
                launch_arguments={
                    "namespace": [ns, "/web"],
                }.items(),
            )
        ]
    )

    # --------------- Data Recording (Eingekapselt) --------------- #
    data_recording_dir = get_package_share_directory("data_recording")

    database_group = GroupAction(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        data_recording_dir, "launch", "data_recording.launch.py"
                    )
                ),
                launch_arguments={
                    "namespace": [ns, "/database"],
                }.items(),
            )
        ]
    )

    return LaunchDescription(
        [
            namespace_arg,
            sensor_group,
            camera_group,
            web_group,
            database_group,
        ]
    )
