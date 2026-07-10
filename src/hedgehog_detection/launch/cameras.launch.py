from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="usb_cam",
                executable="usb_cam_node_exe",
                name="cam_front",
                parameters=[
                    {
                        "video_device": "/dev/video0",
                        "image_width": 1024,
                        "image_height": 576,
                        "pixel_format": "yuyv",
                        "framerate": 30.0,
                        "brightness": 100,
                    }
                ],
                remappings=[("/image_raw", "/cam_front/image_raw")],
            ),
            Node(
                package="usb_cam",
                executable="usb_cam_node_exe",
                name="cam_back",
                parameters=[
                    {
                        "video_device": "/dev/video3",
                        "image_width": 1280,
                        "image_height": 720,
                        "pixel_format": "yuyv",
                        "framerate": 30.0,
                        "brightness": 100,
                    }
                ],
                remappings=[("/image_raw", "/cam_back/image_raw")],
            ),
            Node(
                package="rqt_image_view",
                executable="rqt_image_view",
                name="rqt_image_view_front",
                arguments=["/cam_front/image_raw"],
            ),
            Node(
                package="rqt_image_view",
                executable="rqt_image_view",
                name="rqt_image_view_back",
                arguments=["/cam_back/image_raw"],
            ),
        ]
    )
