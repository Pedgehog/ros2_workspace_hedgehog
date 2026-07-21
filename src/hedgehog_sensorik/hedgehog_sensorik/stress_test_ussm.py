import rclpy
from rclpy.node import Node
from tdk_ussm_interfaces.msg import Envelope
import time


class MultiEnvelopeReaderNode(Node):
    def __init__(self):
        super().__init__("multi_envelope_reader_node")

        # Deklariere den Parameter für die Liste der IDs
        self.declare_parameter("sensor_ids", [1, 2, 3, 4])
        sensor_ids = (
            self.get_parameter("sensor_ids").get_parameter_value().integer_array_value
        )

        # Dictionary zum Speichern der letzten Zeit pro Sensor
        self.last_times = {sid: time.time() for sid in sensor_ids}

        # Ändere den Variablennamen hier von self.subscriptions zu etwas Eigenem
        self.my_subs_list = []

        for sid in sensor_ids:
            topic_name = f"/ussm_envelope{sid}"
            # Callback-Funktion mit Sensor-ID als Parameter
            sub = self.create_subscription(
                Envelope,
                topic_name,
                lambda msg, s=sid: self._listener_callback(msg, s),
                10,
            )
            self.my_subs_list.append(sub)
            self.get_logger().info(f"Abonniert: {topic_name}")

    def _listener_callback(self, msg, sid):
        now = time.time()
        diff = now - self.last_times[sid]

        self.get_logger().info(
            f"Sensor {sid} | Zeit seit letztem Envelope: {diff:.4f} s"
        )

        self.last_times[sid] = now


def main(args=None):
    rclpy.init(args=args)
    node = MultiEnvelopeReaderNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
