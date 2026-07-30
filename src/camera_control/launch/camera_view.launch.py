import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, LaunchConfigurationNotEquals
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_camera_control = get_package_share_directory("camera_control")

    namespace_arg = DeclareLaunchArgument(
        "namespace",
        default_value="camstream",
        description="Namespace for camera nodes",
    )

    camera_arg = DeclareLaunchArgument(
        "cams",
        default_value="TB",
        description="Cameras to view (T = Top, B = Bottom, TB = Both)",
    )

    start_base_arg = DeclareLaunchArgument(
        "start_base",
        default_value="false",
        description="Start camera driver nodes if not already running",
    )

    namespace = LaunchConfiguration("namespace")
    cams = LaunchConfiguration("cams")

    usb_cam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_camera_control, "launch", "usb_cam.launch.py")
        ),
        launch_arguments={"namespace": namespace, "cams": cams}.items(),
        condition=IfCondition(LaunchConfiguration("start_base")),
    )

    view_top_node = Node(
        package="image_view",
        executable="image_view",
        namespace=namespace,
        name="camera_view_top",
        remappings=[("image", "/camstream/cam_top/image_raw")],
        parameters=[{"autosize": True}],
        condition=LaunchConfigurationNotEquals("cams", "T"),
        output="screen",
    )

    view_button_node = Node(
        package="image_view",
        executable="image_view",
        namespace=namespace,
        name="camera_view_button",
        remappings=[("image", "/camstream/cam_button/image_raw")],
        parameters=[{"autosize": True}],
        condition=LaunchConfigurationNotEquals("cams", "B"),
        output="screen",
    )

    return LaunchDescription(
        [
            namespace_arg,
            camera_arg,
            start_base_arg,
            usb_cam_launch,
            view_top_node,
            view_button_node,
        ]
    )
