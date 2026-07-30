import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import LaunchConfigurationNotEquals
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # Konfigurationspfade aus dem camera_control Paket laden
    config_button = os.path.join(
        get_package_share_directory("camera_control"), "config", "cam_button.yaml"
    )
    config_top = os.path.join(
        get_package_share_directory("camera_control"), "config", "cam_top.yaml"
    )

    # Launch-Argumente definieren
    namespace_arg = DeclareLaunchArgument(
        "namespace",
        default_value="camstream",
        description="Namespace for camera nodes",
    )

    camera_arg = DeclareLaunchArgument(
        "cams",
        default_value="TB",
        description="Cameras to activate (T = Top, B = Bottom, TB = Both)",
    )

    namespace = LaunchConfiguration("namespace")
    cams = LaunchConfiguration("cams")

    # Nodes definieren
    cam_button_node = Node(
        package="usb_cam",
        executable="usb_cam_node_exe",
        namespace=namespace,
        name="cam_button",
        parameters=[config_button],
        condition=LaunchConfigurationNotEquals("cams", "B"),
        remappings=[("image_raw", "cam_button/image_raw")],
        output="screen",
    )

    cam_top_node = Node(
        package="usb_cam",
        executable="usb_cam_node_exe",
        namespace=namespace,
        name="cam_top",
        parameters=[config_top],
        condition=LaunchConfigurationNotEquals("cams", "T"),
        remappings=[("image_raw", "cam_top/image_raw")],
        output="screen",
    )

    capture_node = Node(
        package="camera_control",
        executable="capture_picture_camera",
        namespace=namespace,
        name="camera_capture_node",
        output="screen",
    )

    return LaunchDescription(
        [
            namespace_arg,
            camera_arg,
            cam_button_node,
            cam_top_node,
            capture_node,
        ]
    )
