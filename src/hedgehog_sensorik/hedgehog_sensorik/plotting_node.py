import rclpy
from rclpy.node import Node
import matplotlib.pyplot as plt
import math
from tdk_ussm_interfaces.msg import Envelope
from typing import List, Dict
from hedgehog_interfaces.srv import GetSensorIds


class PlottingNode(Node):
    def __init__(self):
        super().__init__("plotting_node")
        self.active_sensors: List[int] = []

        # Warten, bis Trigger-Node da ist und IDs abfragen
        client = self.create_client(GetSensorIds, "get_active_sensors")
        while not client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Warte auf Trigger-Node...")

        future = client.call_async(GetSensorIds.Request())
        rclpy.spin_until_future_complete(self, future)

        # Pylance-Sicherheit: Prüfung auf None
        result = future.result()
        if result is not None:
            self.active_sensors = list(result.sensor_ids)
        else:
            self.get_logger().error("Service-Aufruf fehlgeschlagen. Verwende Default.")
            self.active_sensors = [1, 2, 3, 4]

        self.get_logger().info(f"Sensoren vom Trigger erhalten: {self.active_sensors}")

        self._data_buffer: Dict[int, List[float]] = {
            sid: [] for sid in self.active_sensors
        }
        self._init_plot()

        # Timer für das Rendering
        self.create_timer(0.033, self._render_plot)

        # Subscriptions
        for sid in self.active_sensors:
            self.create_subscription(
                Envelope, f"/ussm_envelope{sid}", self._get_callback_for_sid(sid), 1
            )

    def _init_plot(self):
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
        for i, sid in enumerate(self.active_sensors):
            ax = self._axs[i]
            (line,) = ax.plot([], [], label=f"Sensor {sid}", color="#1f77b4")
            self._lines[sid] = line
            ax.set_ylim(0, 200)
            ax.set_xlim(0, 256)
            ax.set_title(f"Sensor {sid}")
            ax.grid(True)

        for j in range(len(self.active_sensors), len(self._axs)):
            self._axs[j].axis("off")

        self._fig.tight_layout()

    def _get_callback_for_sid(self, sid: int):
        def callback(msg: Envelope):
            self._callback(msg, sid)

        return callback

    def _callback(self, msg: Envelope, sensor_id: int):
        self._data_buffer[sensor_id] = list(msg.amplitudes)

    def _render_plot(self):
        for sid, line in self._lines.items():
            if self._data_buffer[sid]:
                line.set_data(
                    range(len(self._data_buffer[sid])), self._data_buffer[sid]
                )
        self._fig.canvas.draw_idle()
        self._fig.canvas.flush_events()


def main():
    rclpy.init()
    node = PlottingNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        plt.close(node._fig)
        rclpy.shutdown()


if __name__ == "__main__":
    main()
