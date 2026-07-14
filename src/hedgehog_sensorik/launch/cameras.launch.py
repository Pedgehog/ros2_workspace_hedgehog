import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import LaunchConfigurationNotEquals
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("hedgehog_sensorik"),
        "config",
        "camera_config.yaml",
    )

    camera_arg = DeclareLaunchArgument("cams", default_value="TB")

    return LaunchDescription(
        [
            camera_arg,
            Node(
                package="usb_cam",
                executable="usb_cam_node_exe",
                name="hedgehog_cam_button",
                parameters=[config],
                condition=LaunchConfigurationNotEquals("cams", "B"),
                remappings=[("/image_raw", "/cam_button/image_raw")],
            ),
            Node(
                package="usb_cam",
                executable="usb_cam_node_exe",
                name="hedgehog_cam_top",
                parameters=[config],
                condition=LaunchConfigurationNotEquals("cams", "T"),
                remappings=[("/image_raw", "/cam_top/image_raw")],
            ),
            Node(
                package="rqt_image_view",
                executable="rqt_image_view",
                name="hedgehog_rqt_image_view_button",
                condition=LaunchConfigurationNotEquals("cams", "B"),
                arguments=["/cam_button/image_raw"],
            ),
            Node(
                package="rqt_image_view",
                executable="rqt_image_view",
                name="hedgehog_rqt_image_view_top",
                condition=LaunchConfigurationNotEquals("cams", "T"),
                arguments=["/cam_top/image_raw"],
            ),
            Node(
                package="hedgehog_sensorik",
                executable="capture_camera",
                name="hedgehog_camera_capture_node",
                output="screen",
            ),
        ]
    )
