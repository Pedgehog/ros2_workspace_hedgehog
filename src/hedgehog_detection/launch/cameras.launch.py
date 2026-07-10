import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("hedgehog_detection"),
        "config",
        "camera_config.yaml",
    )

    return LaunchDescription(
        [
            Node(
                package="usb_cam",
                executable="usb_cam_node_exe",
                name="cam_front",
                parameters=[config],
                remappings=[("/image_raw", "/cam_front/image_raw")],
            ),
            # Kamera Back
            Node(
                package="usb_cam",
                executable="usb_cam_node_exe",
                name="cam_back",
                parameters=[config],
                remappings=[("/image_raw", "/cam_back/image_raw")],
            ),
            # Viewer Front
            Node(
                package="rqt_image_view",
                executable="rqt_image_view",
                name="rqt_image_view_front",
                arguments=["/cam_front/image_raw"],
            ),
            # Viewer Back
            Node(
                package="rqt_image_view",
                executable="rqt_image_view",
                name="rqt_image_view_back",
                arguments=["/cam_back/image_raw"],
            ),
        ]
    )
