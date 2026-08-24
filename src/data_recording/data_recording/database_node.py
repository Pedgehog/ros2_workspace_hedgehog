import rclpy
from rclpy.node import Node
from pathlib import Path
from typing import Dict, Callable
from std_msgs.msg import Bool
from std_srvs.srv import Trigger
from hedgehog_interfaces.srv import Capture, GetSensorIds, ManageDatabase
from hedgehog_interfaces.srv import ManageDatabase
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
        self.declare_parameter("ussm_sensoren", "")

        self._db_name = self.get_parameter("db_name").get_parameter_value().string_value
        sensor_range = (
            self.get_parameter("ussm_sensoren").get_parameter_value().string_value
        )

        sensor_ids = []

        if sensor_range:
            try:
                start, end = map(int, sensor_range.split("-"))
                sensor_ids = list(range(start, end + 1))
                self.get_logger().info(
                    f"Using sensors from parameter range: {sensor_ids}"
                )
            except Exception as e:
                self.get_logger().warn(
                    f"Failed to parse 'ussm_sensoren' parameter ({e}), falling back to service."
                )

        if not sensor_ids:
            sensor_ids = self._fetch_active_sensors_from_service()

        self._sensor_map: Dict[str, int] = {f"/ussm_envelope{i}": i for i in sensor_ids}

        self._old_measurment_id: int = 0
        self._record_triggered: bool = False

    def _fetch_active_sensors_from_service(self) -> list:
        client = self.create_client(GetSensorIds, "/sensoric/get_active_sensors")
        while not client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(
                "Waiting for service '/sensoric/get_active_sensors'..."
            )

        future = client.call_async(GetSensorIds.Request())
        rclpy.spin_until_future_complete(self, future)

        result = future.result()
        if result is not None:
            active_sensors = list(result.sensor_ids)
            self.get_logger().info(f"Received sensors from service: {active_sensors}")
            return active_sensors
        else:
            self.get_logger().error(
                "Service call failed. Using default sensors [0, 1, 2, 3, 4]."
            )
            return [0, 1, 2, 3, 4]

    def _init_database(self) -> None:
        db_path = Path.cwd() / "output" / "databases" / self._db_name
        self._db = Database(db_path)
        self._sdb = SensorDB(list(self._sensor_map.values()), self._db)
        self._db.init_db()

    def _init_communication(self) -> None:
        self._success_publisher = self.create_publisher(
            Bool, "/database/measurement_success", 10
        )

        for topic, s_id in self._sensor_map.items():
            self.create_subscription(
                Envelope, topic, self._get_callback_for_sensor(s_id), 10
            )

        self.cli = self.create_client(Capture, "/camstream/capture_photo")
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for capture_photo service...")

        self._status_service = self.create_service(
            Trigger, "/database/get_recording_status", self._status_service_callback
        )
        self._start_service = self.create_service(
            Trigger, "/database/start_recording", self._start_service_callback
        )
        self._stop_service = self.create_service(
            Trigger, "/database/stop_recording", self._stop_service_callback
        )
        self._toggle_service = self.create_service(
            Trigger, "/database/toggle_recording", self._toggle_service_callback
        )

        self._db_management_service = self.create_service(
            ManageDatabase,
            "/database/manage_database",
            self._manage_database_service_callback,
        )

    def _set_recording_state(self, new_state: bool, source: str) -> None:
        if self._record_triggered == new_state:
            return

        self._record_triggered = new_state
        state_str = "started" if new_state else "stopped"

        self.get_logger().info("----------------------------------------------")
        self.get_logger().info(f"[{source}] Recording {state_str}.")
        self.get_logger().info("----------------------------------------------")

    def _status_service_callback(self, request, response) -> Trigger.Response:
        response.success = True
        response.message = str(self._record_triggered)
        return response

    def _start_service_callback(self, request, response) -> Trigger.Response:
        self._set_recording_state(True, "START SERVICE")
        response.success = True
        response.message = str(self._record_triggered)
        return response

    def _stop_service_callback(self, request, response) -> Trigger.Response:
        self._set_recording_state(False, "STOP SERVICE")
        response.success = True
        response.message = str(self._record_triggered)
        return response

    def _toggle_service_callback(self, request, response) -> Trigger.Response:
        new_state = not self._record_triggered
        self._set_recording_state(new_state, "TOGGLE SERVICE")
        response.success = True
        response.message = str(self._record_triggered)
        return response

    def _manage_database_service_callback(
        self, request: ManageDatabase.Request, response: ManageDatabase.Response
    ) -> ManageDatabase.Response:
        action = request.action.lower()
        db_name = request.db_name.strip()

        output_dir = Path.cwd() / "output" / "databases"
        output_dir.mkdir(parents=True, exist_ok=True)

        if action == "current":
            response.success = True
            response.message = self._db_name
            response.available_db_names = self._get_all_db_files(output_dir)
            return response

        elif action == "list":
            response.success = True
            response.message = (
                f"Found {len(self._get_all_db_files(output_dir))} databases."
            )
            response.available_db_names = self._get_all_db_files(output_dir)
            return response

        elif action == "create":
            if not db_name:
                response.success = False
                response.message = "Database name cannot be empty."
                response.available_db_names = self._get_all_db_files(output_dir)
                return response

            if not db_name.endswith(".db"):
                db_name += ".db"

            db_path = output_dir / db_name
            try:
                new_db = Database(db_path)
                new_db.init_db()
                response.success = True
                response.message = f"Database '{db_name}' created successfully."
                response.available_db_names = self._get_all_db_files(output_dir)
                self.get_logger().info(
                    f"[DB MANAGEMENT] Created new database: {db_name}"
                )
            except Exception as e:
                response.success = False
                response.message = f"Failed to create database: {str(e)}"
                response.available_db_names = self._get_all_db_files(output_dir)
            return response

        elif action == "switch":
            if not db_name:
                response.success = False
                response.message = "Database name cannot be empty for switching."
                response.available_db_names = self._get_all_db_files(output_dir)
                return response

            if not db_name.endswith(".db"):
                db_name += ".db"

            db_path = output_dir / db_name
            if not db_path.exists():
                response.success = False
                response.message = (
                    f"Database '{db_name}' does not exist. Use 'create' first."
                )
                response.available_db_names = self._get_all_db_files(output_dir)
                return response

            try:
                if self._record_triggered:
                    self._set_recording_state(False, "DB SWITCH")

                self._db_name = db_name
                self._db = Database(db_path)
                self._sdb = SensorDB(list(self._sensor_map.values()), self._db)
                self._db.init_db()

                response.success = True
                response.message = f"Successfully switched to database '{db_name}'."
                response.available_db_names = self._get_all_db_files(output_dir)
                self.get_logger().info(
                    f"[DB MANAGEMENT] Switched active database to: {db_name}"
                )
            except Exception as e:
                response.success = False
                response.message = f"Failed to switch database: {str(e)}"
                response.available_db_names = self._get_all_db_files(output_dir)
            return response

        else:
            response.success = False
            response.message = f"Unknown action '{action}'. Use 'current', 'list', 'create', or 'switch'."
            response.available_db_names = self._get_all_db_files(output_dir)
            return response

    def _get_all_db_files(self, output_dir: Path) -> list:
        if not output_dir.exists():
            return []
        return [p.name for p in output_dir.glob("*.db")]

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
