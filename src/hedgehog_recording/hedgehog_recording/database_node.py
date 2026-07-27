import rclpy
from rclpy.node import Node
from pathlib import Path
from typing import Dict, Callable
from std_msgs.msg import Bool
from hedgehog_interfaces.srv import Capture
from tdk_ussm_interfaces.msg import Envelope
from .utils.database.database import Database
from .utils.database.database_senoric import SensorDB


class DatabaseNode(Node):
    def __init__(self) -> None:
        super().__init__("database_node")

        self._init_parameters()
        self._init_database()
        self._init_communication()

        self.get_logger().info(
            f"Database {self._db_name} ready. Listening to sensors: {list(self._sensor_map.values())}"
        )

    def _init_parameters(self) -> None:
        self.declare_parameter("db_name", "hedgehog_records.db")
        self.declare_parameter("ussm_sensoren", "1-4")

        self._db_name = self.get_parameter("db_name").get_parameter_value().string_value
        sensor_range = (
            self.get_parameter("ussm_sensoren").get_parameter_value().string_value
        )

        start, end = map(int, sensor_range.split("-"))
        self._sensor_map: Dict[str, int] = {
            f"/ussm_envelope{i}": i for i in range(start, end + 1)
        }

        self._old_measurment_id: int = 0
        self._record_triggered: bool = False

    def _init_database(self) -> None:
        db_path = Path.cwd() / "output" / "databases" / self._db_name
        self._db = Database(db_path)
        self._sdb = SensorDB(list(self._sensor_map.values()), self._db)
        self._db.init_db()

    def _init_communication(self) -> None:
        self.create_subscription(
            Bool,
            "/database/measurement_triggered",
            self._trigger_subscriber_callback,
            10,
        )

        self._success_publisher = self.create_publisher(
            Bool, "/database/measurement_success", 10
        )

        for topic, s_id in self._sensor_map.items():
            self.create_subscription(
                Envelope, topic, self._get_callback_for_sensor(s_id), 10
            )

        self.cli = self.create_client(Capture, "/hedgehog/capture_photo")
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for capture_photo service...")

    def _trigger_subscriber_callback(self, msg: Bool) -> None:
        self._record_triggered = msg.data
        if self._record_triggered:
            self.get_logger().info("----------------------------------------------")
            self.get_logger().info("[TRIGGER ACTIVATED] Recording started.")
            self.get_logger().info("----------------------------------------------")
        else:
            self.get_logger().info("----------------------------------------------")
            self.get_logger().info("[TRIGGER DEACTIVATED] Recording stopped.")
            self.get_logger().info("----------------------------------------------")

    def _get_callback_for_sensor(self, s_id: int) -> Callable[[Envelope], None]:
        def callback(msg: Envelope) -> None:
            self._envelope_callback(msg, s_id)

        return callback

    def _check_measurement_id(self, new_sensor_id: int) -> int:
        new_measurment = self._sdb.get_or_create_measurement(new_sensor_id)
        if new_measurment != self._old_measurment_id:
            self.get_logger().info(
                f"[NEW MEASUREMENT] ID changed from {self._old_measurment_id} to {new_measurment}"
            )
            self._trigger_capture()
        self._old_measurment_id = new_measurment
        return self._old_measurment_id

    def _envelope_callback(self, msg: Envelope, s_id: int) -> None:
        if not self._record_triggered:
            return

        try:
            meas_id = self._check_measurement_id(s_id)

            envelope_id, _ = self._sdb.insert_new_envelope(
                s_id,
                meas_id,
                list(msg.time_axis),
                list(msg.amplitudes),
            )

            self.get_logger().info(
                f"[ENVELOPE SAVED] Sensor {s_id} -> Measurement ID: {meas_id} | Envelope ID: {envelope_id}"
            )

            self._publish_success()

        except Exception as e:
            self.get_logger().error(
                f"[ERROR] Failed to save envelope for sensor {s_id}: {str(e)}"
            )

    def _trigger_capture(self) -> None:
        req = Capture.Request()
        future = self.cli.call_async(req)
        future.add_done_callback(self.capture_response_callback)

    def capture_response_callback(self, future) -> None:
        try:
            response = future.result()

            success = response.success
            file_paths = response.file_paths
            message = response.message

            if success:
                self.get_logger().info(f"[MEASUREMENT SUCCESS] {message}")
                self.get_logger().info(f"   Files: {file_paths}")

                for path in file_paths:
                    _, _ = self._sdb.insert_new_picture(self._old_measurment_id, path)
                    self.get_logger().info(f"   -> Image linked: {path}")

                self._publish_success()
            else:
                self.get_logger().error(
                    f"[MEASUREMENT ERROR] Capture failed: {message}"
                )

        except Exception as e:
            self.get_logger().error(f"[SERVICE ERROR] Capture service call failed: {e}")

    def _publish_success(self) -> None:
        success_msg = Bool()
        success_msg.data = True
        self._success_publisher.publish(success_msg)


def main() -> None:
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
