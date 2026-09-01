import os
import time
from typing import Optional
import rclpy
from rclpy.node import Node
from rclpy.timer import Timer
import yaml
from ament_index_python.packages import get_package_share_directory

from tdk_ussm_interfaces.msg import ServoPositions
from hedgehog_interfaces.srv import SetServoUnit, SavePreset
from std_srvs.srv import Trigger

from .servo.servo_board import ServoBoardInterface


class ServoControlNode(Node):

    def __init__(self) -> None:
        super().__init__("servo_control_node")

        self.unit_positions = {
            "left": {"y": 150, "z": 125},
            "middle": {"y": 150, "z": 125},
            "right": {"y": 150, "z": 125},
        }
        self.last_published_positions = {}
        self.config: dict = {}
        self.port: str = "/dev/servo_board"
        self.package_path: str = ""
        self.config_dir: str = ""
        self.presets_dir: str = ""

        self.servo_board: Optional[ServoBoardInterface] = None
        self.servo_timer: Optional[Timer] = None
        self.startup_timer: Optional[Timer] = None

        self._init_parameters()
        self._init_paths()
        self._init_hardware()

        self.load_main_config()
        self.load_defaults()

        self._init_ros()

        self.startup_timer = self.create_timer(
            1.0, self._startup_default_timer_callback
        )

        self.get_logger().info("Servo control node successfully initialized.")

    def _init_parameters(self) -> None:
        self.declare_parameter("com_port", "/dev/servo_board")
        self.port = self.get_parameter("com_port").get_parameter_value().string_value

    def _init_paths(self) -> None:
        self.package_path = get_package_share_directory("servo_control")
        self.config_dir = os.path.join(self.package_path, "config")
        self.presets_dir = os.path.join(self.config_dir, "presets")
        os.makedirs(self.presets_dir, exist_ok=True)

    def _init_hardware(self) -> None:
        self.get_logger().info(f"Connecting to servo board on {self.port}...")
        self.servo_board = ServoBoardInterface(self.port)
        time.sleep(0.5)

    def _init_ros(self) -> None:
        self.servo_pub = self.create_publisher(
            ServoPositions,
            "servo_positions",
            10,
        )

        self.create_service(SetServoUnit, "set_servo_unit", self.handle_set_servo_unit)
        self.create_service(Trigger, "save_as_default", self.handle_save_as_default)
        self.create_service(SavePreset, "save_preset", self.handle_save_preset)
        self.create_service(Trigger, "load_defaults", self.handle_load_defaults)

        self.servo_timer = self.create_timer(0.1, self.publish_servo_positions)

    def _startup_default_timer_callback(self) -> None:
        if self.startup_timer:
            self.destroy_timer(self.startup_timer)
        req = Trigger.Request()
        res = Trigger.Response()
        self.handle_load_defaults(req, res)
        self.get_logger().info("Startup defaults successfully applied.")

    def load_main_config(self) -> None:
        config_path = os.path.join(self.config_dir, "servo_config.yaml")
        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            self.get_logger().warning(
                f"Could not load main config ({e}), using fallback."
            )
            self.config = {
                "units": {
                    "left": {"z_id": 1, "y_id": 2},
                    "middle": {"z_id": 7, "y_id": 8},
                    "right": {"z_id": 10, "y_id": 9},
                },
                "limits": {"z_axis": [0, 170], "y_axis": [15, 275]},
            }

    def load_defaults(self) -> None:
        defaults_path = os.path.join(self.config_dir, "servo_defaults.yaml")
        if os.path.exists(defaults_path):
            try:
                with open(defaults_path, "r") as f:
                    defaults = yaml.safe_load(f)
                if defaults:
                    self.unit_positions.update(defaults)
            except Exception as e:
                self.get_logger().error(f"Failed to load defaults: {e}")

    def handle_set_servo_unit(
        self, request: SetServoUnit.Request, response: SetServoUnit.Response
    ) -> SetServoUnit.Response:
        unit_name = request.unit_name.lower()
        y_val = request.y
        z_val = request.z

        units_map = self.config.get("units", {})
        if unit_name not in units_map:
            response.success = False
            response.message = f"Unknown unit: {unit_name}"
            return response

        z_min, z_max = self.config.get("limits", {}).get("z_axis", [0, 170])
        y_min, y_max = self.config.get("limits", {}).get("y_axis", [15, 275])

        if not (z_min <= z_val <= z_max) or not (y_min <= y_val <= y_max):
            response.success = False
            response.message = "Values out of bounds."
            return response

        z_id = units_map[unit_name]["z_id"]
        y_id = units_map[unit_name]["y_id"]

        if self.servo_board:
            self.servo_board.move_servo(z_id, float(z_val))
            time.sleep(0.02)
            self.servo_board.move_servo(y_id, float(y_val))

        self.unit_positions[unit_name]["y"] = y_val
        self.unit_positions[unit_name]["z"] = z_val

        response.success = True
        response.message = f"Moved {unit_name} to Y={y_val}, Z={z_val}"
        return response

    def handle_save_as_default(
        self, request: Trigger.Request, response: Trigger.Response
    ) -> Trigger.Response:
        defaults_path = os.path.join(self.config_dir, "servo_defaults.yaml")
        try:
            with open(defaults_path, "w") as f:
                yaml.dump(self.unit_positions, f, default_flow_style=False)
            response.success = True
            response.message = "Current positions saved as default."
        except Exception as e:
            response.success = False
            response.message = f"Failed to save defaults: {e}"
        return response

    def handle_save_preset(
        self, request: SavePreset.Request, response: SavePreset.Response
    ) -> SavePreset.Response:
        preset_name = request.name.strip()
        if not preset_name:
            response.success = False
            response.message = "Preset name cannot be empty."
            return response

        preset_path = os.path.join(self.presets_dir, f"{preset_name}.yaml")
        try:
            with open(preset_path, "w") as f:
                yaml.dump(self.unit_positions, f, default_flow_style=False)
            response.success = True
            response.message = f"Preset '{preset_name}' saved successfully."
        except Exception as e:
            response.success = False
            response.message = f"Failed to save preset: {e}"
        return response

    def handle_load_defaults(
        self, request: Trigger.Request, response: Trigger.Response
    ) -> Trigger.Response:
        defaults_path = os.path.join(self.config_dir, "servo_defaults.yaml")
        if not os.path.exists(defaults_path):
            response.success = False
            response.message = "No defaults file found."
            return response

        try:
            with open(defaults_path, "r") as f:
                defaults = yaml.safe_load(f)

            if not defaults:
                response.success = False
                response.message = "Defaults file is empty."
                return response

            units_map = self.config.get("units", {})
            for unit_name, pos in defaults.items():
                if unit_name not in units_map:
                    continue

                y_val = int(pos["y"])
                z_val = int(pos["z"])

                z_id = units_map[unit_name]["z_id"]
                y_id = units_map[unit_name]["y_id"]

                if self.servo_board:
                    self.servo_board.move_servo(z_id, float(z_val))
                    time.sleep(0.04)
                    self.servo_board.move_servo(y_id, float(y_val))
                    time.sleep(0.04)

                self.unit_positions[unit_name]["y"] = y_val
                self.unit_positions[unit_name]["z"] = z_val

            response.success = True
            response.message = "Successfully moved all units to default positions."
        except Exception as e:
            response.success = False
            response.message = f"Failed to load/apply defaults: {e}"

        return response

    def publish_servo_positions(self) -> None:
        now = self.get_clock().now().to_msg()
        units_map = self.config.get("units", {})

        for unit_key, pos in self.unit_positions.items():
            if unit_key not in units_map:
                continue

            msg = ServoPositions()
            msg.header.stamp = now
            msg.header.frame_id = "base_link"
            msg.group_name = units_map[unit_key].get("display_name", unit_key)
            msg.z = int(pos["z"])
            msg.y = int(pos["y"])
            self.servo_pub.publish(msg)

    def destroy_node(self) -> None:
        super().destroy_node()


def main(args: Optional[list] = None) -> None:
    rclpy.init(args=args)
    node = ServoControlNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.servo_timer is not None:
            node.servo_timer.cancel()

        try:
            if node.servo_board:
                node.servo_board.thread_close()
        except Exception:
            pass

        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
