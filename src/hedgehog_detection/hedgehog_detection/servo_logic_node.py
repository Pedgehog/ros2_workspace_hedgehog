import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from dataclasses import dataclass
from ament_index_python.packages import get_package_share_directory
from pathlib import Path
import yaml


@dataclass
class ServoHolder:
    base: int
    top: int
    default: tuple = (0, 150)


MAPPING_STANDBY = {
    "right": ServoHolder(2, 1, (150, 165)),
    "middle": ServoHolder(5, 6, (135, 150)),
    "left": ServoHolder(8, 7, (120, 150)),
}


MAPPING_WORKING = {
    "right": ServoHolder(2, 1, (170, 165)),
    "middle": ServoHolder(5, 6, (135, 150)),
    "left": ServoHolder(8, 7, (100, 150)),
}


class ServoLogicNode(Node):
    def __init__(self):
        super().__init__("servo_logic_node")

        pkg_path = Path(get_package_share_directory("hedgehog_detection"))
        config_path = pkg_path / "config" / "servo_config.yaml"
        pos_path = pkg_path / "config" / "servo_positions.yaml"

        with open(config_path, "r") as f:
            self.servo_map = yaml.safe_load(f)
        with open(pos_path, "r") as f:
            self.positions = yaml.safe_load(f)

        self.publisher = self.create_publisher(String, "/servo/command", 10)

        self.timer = self.create_timer(5.0, self.timer_callback)

        self.is_working = True
        self.get_logger().info("ServoLogicNode gestartet.")

    def move_servo(self, servo_id, angle):
        msg = String()
        msg.data = f"{servo_id} {angle}"
        self.get_logger().info(msg.data)
        self.publisher.publish(msg)

    def init_servos(self):
        self.apply_positions("default_normal")

    def timer_callback(self):
        mode = "default_looking_in" if self.is_working else "default_normal"
        self.get_logger().info(f"Wechsle zu: {mode}")
        self.apply_positions(mode)
        self.is_working = not self.is_working

    def apply_positions(self, mode: str):
        pos_data = self.positions.get(mode, {})
        for name, angles in pos_data.items():
            ids = self.servo_map.get(name, {}).get("servo_id", {})
            base_id = ids.get("base")
            top_id = ids.get("top")

            if base_id is not None and top_id is not None:
                self.move_servo(base_id, angles["z"])
                self.move_servo(top_id, angles["y"])


def main(args=None):
    rclpy.init(args=args)
    node = ServoLogicNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
