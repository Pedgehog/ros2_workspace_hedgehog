import rclpy
from rclpy.node import Node
from pathlib import Path
from typing import Optional, List, Set, Dict, Callable
from datetime import datetime

from tdk_ussm_interfaces.msg import Envelope
from .utils.database.database import Database
from .utils.database.models import Measurement, SensorEnvelope


class DatabaseNode(Node):
    def __init__(self) -> None:
        super().__init__("database_node")

        self.declare_parameter("db_name", "hedgehog_records.db")
        self.declare_parameter("ussm_sensoren", "1-4")

        db_name = self.get_parameter("db_name").get_parameter_value().string_value
        sensor_range = (
            self.get_parameter("ussm_sensoren").get_parameter_value().string_value
        )

        db_path = Path.cwd() / "output" / "databases" / db_name
        self.db = Database(db_path)
        self.db.init_db()

        self.active_measurement_id: Optional[int] = None
        self.sensors_received: Set[int] = set()

        start, end = map(int, sensor_range.split("-"))
        self.sensor_map: Dict[str, int] = {
            f"/ussm_envelope{i}": i for i in range(start, end + 1)
        }

        for topic, s_id in self.sensor_map.items():
            self.create_subscription(
                Envelope, topic, self.get_callback_for_sensor(s_id), 10
            )

        self.get_logger().info(
            f"Datenbank {db_name} bereit. Höre auf Sensoren: {list(self.sensor_map.values())}"
        )

    def get_callback_for_sensor(self, s_id: int) -> Callable[[Envelope], None]:
        def callback(msg: Envelope) -> None:
            self.envelope_callback(msg, s_id)

        return callback

    def get_or_create_measurement(self, sensor_id: int) -> int:
        if sensor_id in self.sensors_received:
            self.active_measurement_id = None
            self.sensors_received.clear()

        if self.active_measurement_id is None:
            with self.db.session_scope() as session:
                new_meas = Measurement(
                    label="Auto-recorded", underground="unknown", conditions="unknown"
                )
                session.add(new_meas)
                session.flush()
                self.active_measurement_id = new_meas.id
                self.get_logger().info(
                    f"Neue Messung gestartet: ID {self.active_measurement_id}"
                )

        assert self.active_measurement_id is not None

        self.sensors_received.add(sensor_id)
        return self.active_measurement_id

    def envelope_callback(self, msg: Envelope, s_id: int) -> None:
        try:
            meas_id = self.get_or_create_measurement(s_id)

            with self.db.session_scope() as session:
                env = SensorEnvelope(
                    measurement_id=meas_id,
                    sensor_id=s_id,
                    time_axis=list(msg.time_axis),
                    amplitudes=list(msg.amplitudes),
                )
                session.add(env)

            self.get_logger().info(
                f"Gespeichert: Sensor {s_id} -> Messung ID {meas_id}"
            )

        except Exception as e:
            self.get_logger().error(f"Fehler bei Sensor {s_id}: {str(e)}")


def main():
    rclpy.init()
    node = DatabaseNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
