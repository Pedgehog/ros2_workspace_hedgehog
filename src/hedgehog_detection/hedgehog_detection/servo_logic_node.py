import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from dataclasses import dataclass


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

        self.publisher = self.create_publisher(String, "/servo/command", 10)

        self.timer = self.create_timer(5.0, self.timer_callback)

        self.is_working = True
        self.get_logger().info("ServoLogicNode gestartet.")

    def move_servo(self, servo_id, angle):
        msg = String()
        msg.data = f"{servo_id} {angle}"
        self.get_logger().info(msg.data)
        self.publisher.publish(msg)

    def init_servos_once(self):
        self.get_logger().info("Fahre Servos in Default-Position...")
        for name, holder in MAPPING_STANDBY.items():
            self.move_servo(holder.base, holder.default[0])
            self.move_servo(holder.top, holder.default[1])

    def timer_callback(self):
        # Logik: Standby = default, Working = 90
        # Hier nutzen wir holder.default[0] für Standby

        for name, holder in (
            MAPPING_STANDBY.items() if not self.is_working else MAPPING_WORKING.items()
        ):
            base_angle = holder.default[0]
            top_angle = holder.default[1]

            self.move_servo(holder.base, base_angle)
            self.move_servo(holder.top, top_angle)

        self.is_working = not self.is_working


def main(args=None):
    rclpy.init(args=args)
    node = ServoLogicNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
