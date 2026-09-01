import time
from typing import Optional
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from tdk_ussm_interfaces.msg import ServoPositions
from hedgehog_interfaces.srv import SetServoUnit
from std_srvs.srv import Trigger


class ServoJoyNode(Node):

    BTN_CROSS = 0
    BTN_CIRCLE = 1
    BTN_SQUARE = 2
    BTN_TRIANGLE = 3

    BTN_UP = 13
    BTN_DOWN = 14
    BTN_LEFT = 11
    BTN_RIGHT = 12

    ENABLE_AXIS_IDX = 2

    LIMIT_Y_MIN, LIMIT_Y_MAX = 15, 275
    LIMIT_Z_MIN, LIMIT_Z_MAX = 0, 170

    TIME_DT_X = 2.0

    def __init__(self) -> None:
        super().__init__("servo_joy_node")

        self.positions: dict = {}
        self.step_y: int = 3
        self.step_z: int = 2
        self.last_buttons_state: list = []

        self.cross_press_start_time: Optional[float] = None
        self.save_triggered: bool = False

        self._init_ros()
        self.get_logger().info("Servo joy node initialized.")

    def _init_ros(self) -> None:
        self.declare_parameter("joy_topic", "/j100_0809/joy_teleop/joy")
        joy_topic = self.get_parameter("joy_topic").get_parameter_value().string_value

        self.create_subscription(Joy, joy_topic, self.joy_callback, 10)
        self.create_subscription(
            ServoPositions, "servo_positions", self.servo_positions_callback, 10
        )

        self.cli_move = self.create_client(SetServoUnit, "set_servo_unit")
        self.cli_default = self.create_client(Trigger, "load_defaults")
        self.cli_save_default = self.create_client(Trigger, "save_as_default")

        self._wait_for_services()

    def _wait_for_services(self) -> None:
        while not self.cli_move.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for set_servo_unit service...")
        while not self.cli_default.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for load_defaults service...")
        while not self.cli_save_default.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for save_as_default service...")

    def servo_positions_callback(self, msg: ServoPositions) -> None:
        group = msg.group_name.lower()
        unit_name = None
        if "left" in group or "links" in group:
            unit_name = "left"
        elif "middle" in group or "mitte" in group:
            unit_name = "middle"
        elif "right" in group or "rechts" in group:
            unit_name = "right"

        if unit_name:
            self.positions[unit_name] = {"y": msg.y, "z": msg.z}

    def _is_new_press(self, current_buttons: list, btn_idx: int) -> bool:
        if len(current_buttons) <= btn_idx:
            return False
        pressed_now = current_buttons[btn_idx] == 1
        pressed_before = (
            self.last_buttons_state[btn_idx] == 1
            if len(self.last_buttons_state) > btn_idx
            else False
        )
        return pressed_now and not pressed_before

    def _handle_deadman(self, msg: Joy, buttons: list) -> bool:
        enable_val = (
            msg.axes[self.ENABLE_AXIS_IDX]
            if len(msg.axes) > self.ENABLE_AXIS_IDX
            else 1.0
        )
        if enable_val > 0.0:
            self.cross_press_start_time = None
            self.save_triggered = False
            self.last_buttons_state = buttons
            return True
        return False

    def _handle_cross_button(self, buttons: list) -> bool:
        cross_is_pressed = (
            len(buttons) > self.BTN_CROSS and buttons[self.BTN_CROSS] == 1
        )
        cross_was_pressed = (
            len(self.last_buttons_state) > self.BTN_CROSS
            and self.last_buttons_state[self.BTN_CROSS] == 1
        )

        if cross_is_pressed and not cross_was_pressed:
            self.cross_press_start_time = time.time()
            self.save_triggered = False
            self.last_buttons_state = buttons
            return True

        if cross_is_pressed and cross_was_pressed:
            if self.cross_press_start_time and not self.save_triggered:
                if time.time() - self.cross_press_start_time >= self.TIME_DT_X:
                    self.get_logger().info("Saving current positions as default.")
                    req = Trigger.Request()
                    future = self.cli_save_default.call_async(req)
                    future.add_done_callback(self.handle_save_default_response)
                    self.save_triggered = True
            self.last_buttons_state = buttons
            return True

        if not cross_is_pressed and cross_was_pressed:
            press_duration = (
                time.time() - self.cross_press_start_time
                if self.cross_press_start_time
                else 0.0
            )
            self.cross_press_start_time = None

            if not self.save_triggered and press_duration < self.TIME_DT_X:
                self.get_logger().info("Loading default positions.")
                req = Trigger.Request()
                future = self.cli_default.call_async(req)
                future.add_done_callback(self.handle_default_response)

            self.save_triggered = False
            self.last_buttons_state = buttons
            return True

        return False

    def _handle_servo_selection(self, buttons: list) -> Optional[str]:
        unit_mapping = {
            self.BTN_TRIANGLE: "middle",
            self.BTN_SQUARE: "left",
            self.BTN_CIRCLE: "right",
        }
        return next(
            (
                name
                for btn, name in unit_mapping.items()
                if len(buttons) > btn and buttons[btn] == 1
            ),
            None,
        )

    def _handle_dpad_movement(self, buttons: list, active_unit: str) -> None:
        y_change = 0
        z_change = 0
        changed = False

        if self._is_new_press(buttons, self.BTN_UP):
            z_change = -self.step_z
            changed = True
        elif self._is_new_press(buttons, self.BTN_DOWN):
            z_change = self.step_z
            changed = True

        if self._is_new_press(buttons, self.BTN_LEFT):
            y_change = self.step_y
            changed = True
        elif self._is_new_press(buttons, self.BTN_RIGHT):
            y_change = -self.step_y
            changed = True

        if changed:
            current_y = self.positions[active_unit]["y"]
            current_z = self.positions[active_unit]["z"]

            new_y = max(self.LIMIT_Y_MIN, min(self.LIMIT_Y_MAX, current_y + y_change))
            new_z = max(self.LIMIT_Z_MIN, min(self.LIMIT_Z_MAX, current_z + z_change))

            self.positions[active_unit]["y"] = new_y
            self.positions[active_unit]["z"] = new_z

            self._send_servo_request(active_unit, new_y, new_z)

    def joy_callback(self, msg: Joy) -> None:
        if not msg.buttons:
            return

        buttons = list(msg.buttons)

        if not self.last_buttons_state:
            self.last_buttons_state = [0] * len(buttons)

        if self._handle_deadman(msg, buttons):
            return

        if self._handle_cross_button(buttons):
            return

        active_unit = self._handle_servo_selection(buttons)
        if not active_unit:
            self.last_buttons_state = buttons
            return

        if active_unit not in self.positions:
            self.last_buttons_state = buttons
            return

        self._handle_dpad_movement(buttons, active_unit)
        self.last_buttons_state = buttons

    def _send_servo_request(self, unit_name: str, y: int, z: int) -> None:
        req = SetServoUnit.Request()
        req.unit_name = unit_name
        req.y = int(y)
        req.z = int(z)
        future = self.cli_move.call_async(req)
        future.add_done_callback(
            lambda f: self._handle_move_response(f, unit_name, y, z)
        )

    def _handle_move_response(self, future, unit_name: str, y: int, z: int) -> None:
        try:
            response = future.result()
            if not response.success:
                self.get_logger().warning(
                    f"Move rejected for {unit_name}: {response.message}"
                )
        except Exception as e:
            self.get_logger().error(f"Service call failed: {e}")

    def handle_default_response(self, future) -> None:
        try:
            res = future.result()
            if not res.success:
                self.get_logger().warning(f"Reset failed: {res.message}")
        except Exception as e:
            self.get_logger().error(f"Default reset service call failed: {e}")

    def handle_save_default_response(self, future) -> None:
        try:
            res = future.result()
            if not res.success:
                self.get_logger().warning(f"Save default failed: {res.message}")
        except Exception as e:
            self.get_logger().error(f"Save default service call failed: {e}")


def main(args: Optional[list] = None) -> None:
    rclpy.init(args=args)
    node = ServoJoyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
