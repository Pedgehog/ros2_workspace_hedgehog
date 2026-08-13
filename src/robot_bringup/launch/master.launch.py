import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    data_recording_dir = get_package_share_directory("data_recording")
    sensor_envelope_dir = get_package_share_directory("sensor_envelope")
    camera_control_dir = get_package_share_directory("camera_control")

    data_recording_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(data_recording_dir, "launch", "data_recording.launch.py")
        ),
        launch_arguments={"namespace": "tdk_robot/database"}.items(),
    )

    sensor_base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(sensor_envelope_dir, "launch", "sensor_base.launch.py")
        ),
        launch_arguments={"namespace": "tdk_robot/sensoric"}.items(),
    )

    camera_control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(camera_control_dir, "launch", "usb_cam.launch.py")
        ),
        launch_arguments={"namespace": "tdk_robot/camera"}.items(),
    )

    webpage_dir = get_package_share_directory("cloud_bridge")
    webpage_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(webpage_dir, "launch", "webpage.launch.py")
        ),
        launch_arguments={"namespace": "tdk_robot/web"}.items(),
    )

    return LaunchDescription(
        [
            data_recording_launch,
            sensor_base_launch,
            camera_control_launch,
            webpage_launch,
        ]
    )
