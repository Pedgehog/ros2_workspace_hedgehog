import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Trigger
from .utils.Servo.servo_board import ServoBoardInterface


class ServoControllerNode(Node):
    def __init__(self):
        super().__init__("servo_controller_node")
        self.servo_board = ServoBoardInterface(port="/dev/ttyUSB0")
        self.create_subscription(String, "/servo/command", self.move_callback, 10)
        # self.srv_get = self.create_service(Trigger, "/servo/get_position", self.get_pos_callback)
        self.get_logger().info(
            "ServoControllerNode bereit. Sende Befehle via Topic /servo/command"
        )

    def move_callback(self, msg):
        try:
            parts = msg.data.split()
            servo_id = int(parts[0])
            angle = float(parts[1])
            self.servo_board.move_servo(servo_id, angle)
            self.get_logger().info(f"Bewege Servo {servo_id} auf {angle}")
        except Exception as e:
            self.get_logger().error(f"Fehler beim Parsen: {e}")

    # TODO NEED TO FIX WITH INTERFACES
    # def get_pos_callback(self, request, response):
    #     angle = self.servo_board.get_servo_angle_blocking(0)
    #     response.success = (angle is not None)
    #     response.message = str(angle) if angle is not None else "Timeout"
    #     return response

    def destroy_node(self):
        self.servo_board.thread_close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ServoControllerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
