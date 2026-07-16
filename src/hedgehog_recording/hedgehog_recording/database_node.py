import rclpy
from rclpy.node import Node
from pathlib import Path
from typing import Optional, List, Set, Dict, Callable
from datetime import datetime

from tdk_ussm_interfaces.msg import Envelope
from .utils.database.database import Database
from .utils.database.database_senoric import SensorDB


class DatabaseNode(Node):
    def __init__(self) -> None:
        super().__init__("database_node")

        self.declare_parameter("db_name", "hedgehog_records.db")
        self.declare_parameter("ussm_sensoren", "1-4")

        db_name = self.get_parameter("db_name").get_parameter_value().string_value
        sensor_range = (
            self.get_parameter("ussm_sensoren").get_parameter_value().string_value
        )

        start, end = map(int, sensor_range.split("-"))
        self._sensor_map: Dict[str, int] = {
            f"/ussm_envelope{i}": i for i in range(start, end + 1)
        }

        db_path = Path.cwd() / "output" / "databases" / db_name
        self._db = Database(db_path)
        self._sdb = SensorDB(list(self._sensor_map.values()), self._db)
        self._db.init_db()

        for topic, s_id in self._sensor_map.items():
            self.create_subscription(
                Envelope, topic, self._get_callback_for_sensor(s_id), 10
            )

        self.get_logger().info(
            f"Datenbank {db_name} bereit. Höre auf Sensoren: {list(self._sensor_map.values())}"
        )

    def _get_callback_for_sensor(self, s_id: int) -> Callable[[Envelope], None]:
        def callback(msg: Envelope) -> None:
            self._envelope_callback(msg, s_id)

        return callback

    def _envelope_callback(self, msg: Envelope, s_id: int) -> None:
        try:
            envelope_id, meas_id = self._sdb.insert_new_envelope(
                s_id, list(msg.time_axis), list(msg.amplitudes)
            )
            self.get_logger().info(
                f"Gespeichert: Sensor {s_id} -> Messung ID {meas_id}; Envelope ID:{envelope_id}"
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
