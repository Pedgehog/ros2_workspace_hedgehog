import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import LaunchConfigurationNotEquals
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    config_button = os.path.join(
        get_package_share_directory("hedgehog_sensorik"), "config", "cam_button.yaml"
    )
    config_top = os.path.join(
        get_package_share_directory("hedgehog_sensorik"), "config", "cam_top.yaml"
    )

    camera_arg = DeclareLaunchArgument("cams", default_value="TB")

    return LaunchDescription(
        [
            camera_arg,
            Node(
                package="usb_cam",
                executable="usb_cam_node_exe",
                namespace="hedgehog",
                name="hedgehog_cam_button",
                parameters=[config_button],
                condition=LaunchConfigurationNotEquals("cams", "B"),
                remappings=[("image_raw", "cam_button/image_raw")],
            ),
            Node(
                package="usb_cam",
                executable="usb_cam_node_exe",
                namespace="hedgehog",
                name="hedgehog_cam_top",
                parameters=[config_top],
                condition=LaunchConfigurationNotEquals("cams", "T"),
                remappings=[("image_raw", "cam_top/image_raw")],
            ),
            Node(
                package="rqt_image_view",
                executable="rqt_image_view",
                namespace="hedgehog",
                name="hedgehog_rqt_image_view_button",
                condition=LaunchConfigurationNotEquals("cams", "B"),
                arguments=["/hedgehog/cam_button/image_raw"],
            ),
            Node(
                package="rqt_image_view",
                executable="rqt_image_view",
                namespace="hedgehog",
                name="hedgehog_rqt_image_view_top",
                condition=LaunchConfigurationNotEquals("cams", "T"),
                arguments=["/hedgehog/cam_top/image_raw"],
            ),
            Node(
                package="hedgehog_sensorik",
                executable="capture_camera",
                namespace="hedgehog",
                name="hedgehog_camera_capture_node",
                output="screen",
            ),
        ]
    )
