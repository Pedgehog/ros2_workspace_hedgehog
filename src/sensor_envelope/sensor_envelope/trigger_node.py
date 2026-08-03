import os
import yaml
import json
from ament_index_python.packages import get_package_share_directory
import rclpy
from rclpy.node import Node
from tdk_ussm_interfaces.srv import DistanceStreamoutService
from .utils.ussm_helper import Sensor
from hedgehog_interfaces.srv import GetSensorIds
from std_srvs.srv import Trigger


class TriggerNode(Node):
    def __init__(self):
        super().__init__("trigger_node")

        self.settings = self._load_ussm_config()

        self.declare_parameter("sensor_ids", "")
        param_value = self.get_parameter("sensor_ids").value
        raw_sensor_ids = []

        if isinstance(param_value, list):
            raw_sensor_ids = [int(x) for x in param_value]
        elif isinstance(param_value, str) and param_value.strip():
            cleaned = param_value.strip("[] ")
            if cleaned:
                raw_sensor_ids = [int(x.strip()) for x in cleaned.split(",")]

        if not raw_sensor_ids:
            fallback_order = self.settings.get("order", [1, 2, 3, 4])
            self.active_sensors = fallback_order
            self.get_logger().info(
                f"Parameter 'sensor_ids' is empty. Loaded sensors from config: {self.active_sensors}"
            )
        else:
            self.active_sensors = raw_sensor_ids
            self.get_logger().info(
                f"Using sensors from parameter: {self.active_sensors}"
            )

        self.srv = self.create_service(
            GetSensorIds, "get_active_sensors", self._handle_get_sensors
        )

        self.settings_srv = self.create_service(
            Trigger, "get_ussm_settings", self._handle_get_settings
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

    def _load_ussm_config(self) -> dict:
        try:
            config_path = os.path.join(
                get_package_share_directory("sensor_envelope"),
                "config",
                "ussm_settings.yaml",
            )
            with open(config_path, "r") as f:
                data = yaml.safe_load(f)
                return (
                    data.get("sensor_base", data)
                    .get("ros__parameters", data)
                    .get(
                        "settings",
                        {
                            "order": [4, 3, 6, 5, 2, 1],
                            "sensorpositions": {
                                "right": {"right": 1, "left": 2},
                                "left": {"right": 3, "left": 4},
                                "center": {"right": 5, "left": 6},
                            },
                        },
                    )
                )
        except Exception as e:
            self.get_logger().warn(
                f"Konnte config.yaml nicht laden ({e}), nutze Fallback."
            )
            return {"order": [4, 3, 6, 5, 2, 1], "sensorpositions": {}}

    def _handle_get_sensors(self, request, response):
        response.sensor_ids = list(self.active_sensors)
        return response

    def _handle_get_settings(self, request, response):
        response.success = True
        response.message = json.dumps(self.settings)
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
