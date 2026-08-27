from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    namespace_arg = DeclareLaunchArgument(
        "namespace",
        default_value="tdk_robot",
        description="Namespace for all nodes",
    )

    com_port_arg = DeclareLaunchArgument(
        "com_port",
        default_value="/dev/servo_board",
        description="Serieller Port für das Servo-Board",
    )

    joy_topic_arg = DeclareLaunchArgument(
        "joy_topic",
        default_value="/j100_0809/joy_teleop/joy",
        description="ROS 2 Topic für den Joystick",
    )

    namespace = LaunchConfiguration("namespace")
    com_port = LaunchConfiguration("com_port")
    joy_topic = LaunchConfiguration("joy_topic")

    servo_control_node = Node(
        package="servo_control",
        executable="servo_control_node",
        name="servo_control_node",
        namespace=namespace,
        output="screen",
        parameters=[{"com_port": com_port}],
    )

    servo_joy_node = Node(
        package="servo_control",
        executable="servo_joy_node",
        name="servo_joy_node",
        namespace=namespace,
        output="screen",
        parameters=[{"joy_topic": joy_topic}],
    )

    return LaunchDescription(
        [
            namespace_arg,
            com_port_arg,
            joy_topic_arg,
            servo_control_node,
            servo_joy_node,
        ]
    )
