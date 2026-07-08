import rclpy
from rclpy.node import Node
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from time import sleep
from tdk_ussm_interfaces.srv import DistanceStreamoutService
from tdk_ussm_interfaces.msg import Envelope
from .utils.ussm_helper import Sensor
from .utils.analyzer import Analyzer, MeasurementExporter


class SimpleEnvelope(Node):
    def __init__(self):
        super().__init__("simple_envelope_node")
        # constants
        self._max_ussm_sensor = 9

        self.declare_parameter("sensor_range", "0:8")
        self.declare_parameter("max_cycles", 5)

        range_str = (
            self.get_parameter("sensor_range").get_parameter_value().string_value
        )
        self.max_cycles = (
            self.get_parameter("max_cycles").get_parameter_value().integer_value
        )

        self._start, self._stop = map(int, range_str.split(":"))
        if self._start < 0 or self._stop >= self._max_ussm_sensor:
            self.get_logger().error(f"Ungültige Range: {self._start}:{self._stop}")
            return
        self._range = range(self._start, self._stop + 1)

        # running variables
        self._ussm_sensor = self._range[0]
        self._current_cycle = 0

        # analyze classes
        self._exporter = MeasurementExporter(self._ussm_sensor)
        self._analyzer = Analyzer(self._ussm_sensor)

        # setup for plot
        plt.ion()
        self._fig, self._ax = plt.subplots(figsize=(8, 5))
        (self._line,) = self._ax.plot(
            [], [], color="#1f77b4", linewidth=2, label="Envelope Amp"
        )
        self._ax.set_title(
            f"Live USSM Envelope - Sensor {self._ussm_sensor}",
            fontsize=14,
            fontweight="bold",
        )
        self._ax.set_xlabel("Sample Index", fontsize=12)
        self._ax.set_ylabel("Amplitude", fontsize=12)
        self._ax.xaxis.set_major_locator(MultipleLocator(20))
        self._ax.xaxis.set_minor_locator(MultipleLocator(5))
        self._ax.grid(True, linestyle="--", alpha=0.7)
        self._ax.set_xlim(0, 256)
        self._ax.set_ylim(0, 150)
        self._ax.legend()

        # ros2 spezific items
        self.cli = self.create_client(
            DistanceStreamoutService, "/tdk_ussm/req_dist_streamout"
        )
        self.sub = None
        self._update_sensor(self._ussm_sensor)
        self.timer = self.create_timer(1, self._start_stream)

        sleep(2)

    def _start_stream(self):
        if not self.cli.service_is_ready():
            return
        req = DistanceStreamoutService.Request()
        req.cmd_request = Sensor(self._ussm_sensor)(Sensor.Commando.ENVELOPE)
        self.cli.call_async(req)
        self.get_logger().info(f"Streamanfrage gesendet: {req.cmd_request}")

    def _callback(self, msg):
        self.get_logger().info(f"Empfangen: {list(msg.amplitudes[:10])}...")

        self._line.set_data(range(len(msg.amplitudes)), msg.amplitudes)
        self._fig.canvas.draw_idle()
        plt.pause(0.01)
        self._current_cycle += 1
        peak_msg = self._analyzer.analyze_peak(msg.amplitudes)

        if peak_msg:
            log_lines = [
                f"Sensor {self._ussm_sensor} | Peak {p['index_peak']}: Zeit={p['start_index']}, "
                f"Länge={p['length']}, Höhe={p['height']} {p['warning']}"
                for p in peak_msg
            ]

            self.get_logger().info("\n" + "\n".join(log_lines))

            self._exporter.save(log_lines, self._fig)

        if self._current_cycle >= self._stop:
            self.get_logger().info("Maximale Anzahl an Zyklen erreicht.")
            self._update_sensor(self._ussm_sensor + 1)
            self._current_cycle = 0

    def _update_sensor(self, new_sensor_id):
        if self.sub:
            self.destroy_subscription(self.sub)

        if new_sensor_id >= self._max_ussm_sensor or new_sensor_id > self._stop:
            new_sensor_id = self._start

        self._ussm_sensor = new_sensor_id

        topic = f"/ussm_envelope{self._ussm_sensor}"
        self.sub = self.create_subscription(Envelope, topic, self._callback, 1)

        self._ax.set_title(
            f"Live USSM Envelope - Sensor {self._ussm_sensor}",
            fontsize=14,
            fontweight="bold",
        )
        self.get_logger().info(f"Subscriber aktualisiert auf: {topic}")


def main():
    rclpy.init()
    node = SimpleEnvelope()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
