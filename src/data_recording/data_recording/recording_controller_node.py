import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool
from std_srvs.srv import Trigger
import time


class RecordingControllerNode(Node):
    def __init__(self) -> None:
        super().__init__("recording_controller_node")

        self._last_toggle_time: float = 0.0
        self._debounce_threshold: float = 0.5

        self._init_communication()

        self.get_logger().info(
            "RecordingControllerNode initialized with toggle service client."
        )

    def _init_communication(self) -> None:
        self.create_subscription(
            Joy, "/j100_0809/joy_teleop/joy", self._joy_callback, 10
        )

        self.create_subscription(
            Bool, "/tdk_robot/database/measurement_success", self._success_callback, 10
        )

        self._toggle_client = self.create_client(Trigger, "/database/toggle_recording")

    def _joy_callback(self, msg: Joy) -> None:
        if len(msg.buttons) > 0 and msg.buttons[0] == 1:
            current_time = time.time()

            if current_time - self._last_toggle_time < self._debounce_threshold:
                return

            self._last_toggle_time = current_time
            self.get_logger().info("[CONTROL] Button A pressed. Requesting toggle...")

            if not self._toggle_client.wait_for_service(timeout_sec=0.1):
                self.get_logger().error("[CONTROL] Toggle service not available!")
                return

            request = Trigger.Request()
            future = self._toggle_client.call_async(request)
            future.add_done_callback(self._toggle_response_callback)

    def _toggle_response_callback(self, future) -> None:
        try:
            response = future.result()
            if response and response.success:
                self.get_logger().info(
                    f"[CONTROL] Toggle successful. New state: {response.message}"
                )
            else:
                self.get_logger().error(
                    "[CONTROL] Toggle service call returned failure."
                )
        except Exception as e:
            self.get_logger().error(f"[CONTROL] Service call failed: {e}")

    def _success_callback(self, msg: Bool) -> None:
        if msg.data:
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
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
