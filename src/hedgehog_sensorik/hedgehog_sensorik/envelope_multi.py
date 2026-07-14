import rclpy
from rclpy.node import Node
import matplotlib.pyplot as plt
import math
from tdk_ussm_interfaces.srv import DistanceStreamoutService
from tdk_ussm_interfaces.msg import Envelope
from .utils.ussm_helper import Sensor


class MultiEnvelope(Node):
    def __init__(self):
        super().__init__("multi_envelope_node")

        self.active_sensors = [1, 2, 3, 4]
        self._data_buffer = {sid: [] for sid in self.active_sensors}

        n = len(self.active_sensors)
        cols = 2
        rows = math.ceil(n / cols)

        plt.ion()
        self._fig, self._axs = plt.subplots(rows, cols, figsize=(10, 3 * rows))

        if n == 1:
            self._axs = [self._axs]
        else:
            self._axs = self._axs.flatten()

        self._lines = {}
        i = -1

        for i, sid in enumerate(self.active_sensors):
            ax = self._axs[i]
            (line,) = ax.plot([], [], label=f"Sensor {sid}", color="#1f77b4")
            self._lines[sid] = line
            ax.set_ylim(0, 200)
            ax.set_xlim(0, 256)
            ax.set_title(f"Sensor {sid}")
            ax.grid(True, linestyle="--", alpha=0.7)
            ax.legend(loc="upper right")

        for j in range(i + 1, len(self._axs)):
            self._axs[j].axis("off")

        self._fig.tight_layout()
        self._fig.canvas.draw()

        self.subs = {}
        for sid in self.active_sensors:
            topic = f"/ussm_envelope{sid}"
            self.subs[sid] = self.create_subscription(
                Envelope, topic, lambda msg, s=sid: self._callback(msg, s), 1
            )
            self.get_logger().info(f"Subscribed auf: {topic}")

        self.cli = self.create_client(
            DistanceStreamoutService, "tdk_ussm/req_dist_streamout"
        )
        self.timer = self.create_timer(0.5, self._start_stream)
        self.create_timer(0.033, self._render_plot)

    def _callback(self, msg, sensor_id):
        self._data_buffer[sensor_id] = msg.amplitudes

    def _render_plot(self):
        for sid, line in self._lines.items():
            if self._data_buffer[sid]:
                line.set_data(
                    range(len(self._data_buffer[sid])), self._data_buffer[sid]
                )

        self._fig.canvas.draw_idle()
        self._fig.canvas.flush_events()

    def _start_stream(self):
        if not self.cli.service_is_ready():
            return

        sensor_helper = Sensor(self.active_sensors)
        req = DistanceStreamoutService.Request()
        req.cmd_request = sensor_helper(Sensor.Commando.ENVELOPE)
        self.cli.call_async(req)


def main():
    rclpy.init()
    node = MultiEnvelope()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        plt.close(node._fig)
        rclpy.shutdown()


if __name__ == "__main__":
    main()
