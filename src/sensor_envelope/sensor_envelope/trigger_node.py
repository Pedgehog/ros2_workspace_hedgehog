import rclpy
from rclpy.node import Node
from tdk_ussm_interfaces.srv import DistanceStreamoutService
from .utils.ussm_helper import Sensor
from hedgehog_interfaces.srv import GetSensorIds


class TriggerNode(Node):
    def __init__(self):
        super().__init__("trigger_node")
        self.declare_parameter("sensor_ids", [1, 2, 3, 4])
        self.active_sensors = list(
            self.get_parameter("sensor_ids").get_parameter_value().integer_array_value
        )

        self.srv = self.create_service(
            GetSensorIds, "get_active_sensors", self._handle_get_sensors
        )

        self.cli = self.create_client(
            DistanceStreamoutService, "/tdk_ussm/req_dist_streamout"
        )

        self.get_logger().info("Warte auf Service im Namespace 'sensoric'...")
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn("Service nicht verfügbar, warte...")
        self.get_logger().info("Service gefunden!")

        self.pending_futures = []
        self.timer = self.create_timer(1, self._send_trigger)
        self.get_logger().info("TriggerNode gestartet mit Namespace-Support")

    def _handle_get_sensors(self, request, response):
        response.sensor_ids = list(self.active_sensors)
        return response

    def _send_trigger(self):
        if not self.cli.service_is_ready():
            return

        req = DistanceStreamoutService.Request()
        req.cmd_request = Sensor(self.active_sensors)(Sensor.Commando.ENVELOPE)

        future = self.cli.call_async(req)
        self.get_logger().info("send")

        self.pending_futures.append(future)
        if len(self.pending_futures) > 5:
            self.pending_futures.pop(0)


def main():
    rclpy.init()
    node = TriggerNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
