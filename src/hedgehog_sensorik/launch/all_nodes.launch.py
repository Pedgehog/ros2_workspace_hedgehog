import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare("hedgehog_sensorik")

    config_button = os.path.join(
        get_package_share_directory("hedgehog_sensorik"), "config", "cam_button.yaml"
    )
    config_top = os.path.join(
        get_package_share_directory("hedgehog_sensorik"), "config", "cam_top.yaml"
    )

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

    top_cam = TimerAction(
        period=6.0,
        actions=[
            Node(
                package="usb_cam",
                executable="usb_cam_node_exe",
                namespace="hedgehog",
                name="hedgehog_cam_top",
                parameters=[config_top],
                remappings=[("image_raw", "cam_top/image_raw")],
            )
        ],
    )

    button_cam = TimerAction(
        period=6.0,
        actions=[
            Node(
                package="usb_cam",
                executable="usb_cam_node_exe",
                namespace="hedgehog",
                name="hedgehog_cam_button",
                parameters=[config_button],
                remappings=[("image_raw", "cam_button/image_raw")],
            )
        ],
    )

    capture_pictures = TimerAction(
        period=6.0,
        actions=[
            Node(
                package="hedgehog_sensorik",
                executable="capture_camera",
                namespace="hedgehog",
                name="hedgehog_camera_capture_node",
                output="screen",
            ),
        ],
    )

    view_top = Node(
        package="image_view",
        executable="image_view",
        name="view_top",
        remappings=[("image", "/hedgehog/cam_top/image_raw")],
        parameters=[{"autosize": True}],
    )

    view_button = Node(
        package="image_view",
        executable="image_view",
        name="view_button",
        remappings=[("image", "/hedgehog/cam_button/image_raw")],
        parameters=[{"autosize": True}],
    )

    plotting_node = TimerAction(
        period=1.0,
        actions=[
            Node(
                package="hedgehog_sensorik",
                executable="plotting_node",
                name="plotting_node",
                parameters=[{"sensor_ids": LaunchConfiguration("sensor_ids")}],
            )
        ],
    )

    return LaunchDescription(
        [
            sensor_ids_arg,
            base_launch,
            top_cam,
            button_cam,
            view_top,
            view_button,
            plotting_node,
            capture_pictures,
        ]
    )
