import rclpy
from rclpy.node import Node
from tdk_ussm_interfaces.srv import DistanceStreamoutService
from tdk_ussm_interfaces.msg import Envelope


class SimpleEnvelope(Node):
    def __init__(self):
        super().__init__("simple_envelope_node")

        self.cli = self.create_client(
            DistanceStreamoutService, "/tdk_ussm/req_dist_streamout"
        )
        self.sub = self.create_subscription(
            Envelope, "/ussm_envelope0", self.callback, 1
        )

        self.timer = self.create_timer(1.0, self.start_stream)

    def start_stream(self):
        if not self.cli.service_is_ready():
            return

        req = DistanceStreamoutService.Request()
        req.cmd_request = "esa[0x01] 256 50;"
        self.cli.call_async(req)
        self.get_logger().info("Streamanfrage gesendet: esa[0x01] 256 50;")

    def callback(self, msg):
        print(f"Empfangen: {list(msg.amplitudes[:10])}...")


def main():
    rclpy.init()
    node = SimpleEnvelope()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
