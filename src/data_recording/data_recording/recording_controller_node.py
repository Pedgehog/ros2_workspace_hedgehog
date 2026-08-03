import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool
import time


class RecordingControllerNode(Node):
    def __init__(self) -> None:
        super().__init__("recording_controller_node")

        self._is_recording: bool = False
        self._last_toggle_time: float = 0.0
        self._debounce_threshold: float = 0.5

        self._init_communication()

        self.get_logger().info(
            "RecordingControllerNode initialized with debounce threshold."
        )

    def _init_communication(self) -> None:
        self.create_subscription(
            Joy, "/j100_0809/joy_teleop/joy", self._joy_callback, 10
        )

        self.create_subscription(
            Bool, "/database/measurement_success", self._success_callback, 10
        )

        self._trigger_publisher = self.create_publisher(
            Bool, "/database/measurement_triggered", 10
        )

    def _joy_callback(self, msg: Joy) -> None:
        if len(msg.buttons) > 0 and msg.buttons[0] == 1:
            current_time = time.time()

            if current_time - self._last_toggle_time < self._debounce_threshold:
                return

            self._last_toggle_time = current_time

            if not self._is_recording:
                self.get_logger().info(
                    "[CONTROL] Button A pressed. Starting recording..."
                )
                self._is_recording = True

                trigger_msg = Bool()
                trigger_msg.data = True
                self._trigger_publisher.publish(trigger_msg)
            else:
                self.get_logger().info(
                    "[CONTROL] Button A pressed. Stopping recording..."
                )
                self._is_recording = False

                trigger_msg = Bool()
                trigger_msg.data = False
                self._trigger_publisher.publish(trigger_msg)

    def _success_callback(self, msg: Bool) -> None:
        if msg.data and self._is_recording:
            self.get_logger().info(
                "[CONTROL] Measurement success confirmed while recording active."
            )


def main() -> None:
    rclpy.init()
    node = RecordingControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
