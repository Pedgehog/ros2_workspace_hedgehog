from typing import Dict, List
from pathlib import Path
from .database import Database
from .models import Measurement, SensorEnvelope, MeasurementPicture, ServoPosition


class SensorDB:
    def __init__(self, sensors: List[int], db: Database) -> None:
        self._db = db

        self._sensor_map: Dict[str, int] = {
            f"/ussm_envelope{element}": element for element in sensors
        }

        self._received_sensor: Dict[int, bool] = {}
        self._clear_recived_sensors()
        self._active_measurement_id = None

    def _clear_recived_sensors(self) -> None:
        self._received_sensor: Dict[int, bool] = {
            sensor_id: False for sensor_id in self._sensor_map.values()
        }

    def _check_sensor(self, new_sensor_id: int) -> bool:
        return new_sensor_id in self._sensor_map

    def get_or_create_measurement(self, new_sensor_id: int) -> int | None:
        all_sensors_received = False not in self._received_sensor.values()
        sensor_already_received = self._received_sensor.get(new_sensor_id, False)

        if all_sensors_received or sensor_already_received:
            self._active_measurement_id = None
            self._clear_recived_sensors()

        if new_sensor_id in self._received_sensor:
            self._received_sensor[new_sensor_id] = True

        if self._active_measurement_id is None:
            self._active_measurement_id = self.insert_new_measurement()

        return self._active_measurement_id

    def insert_new_measurement(self) -> int:
        with self._db.session_scope() as session:
            new_meas = Measurement(
                label="Auto-recorded", underground="unknown", conditions="unknown"
            )
            session.add(new_meas)
            session.flush()
            self.active_measurement_id = new_meas.id
        return self.active_measurement_id

    def insert_new_envelope(
        self, sensor_id: int, measurement_id: int, time_axis: list, amplitudes: list
    ):
        envelope_id = None
        with self._db.session_scope() as session:
            envelope = SensorEnvelope(
                measurement_id=measurement_id,
                sensor_id=sensor_id,
                time_axis=time_axis,
                amplitudes=amplitudes,
            )
            session.add(envelope)
            session.flush()
            envelope_id = envelope.id

        return envelope_id, measurement_id

    def insert_new_picture(self, measurement_id: int, picture_path: str):
        path = Path(picture_path)
        try:
            path = path.relative_to(Path.cwd() / "output")
        except ValueError:
            pass

        with self._db.session_scope() as session:
            picture = MeasurementPicture(measurement_id=measurement_id, path=str(path))
            session.add(picture)
            session.flush()
            return picture.id, measurement_id

    def insert_servo_position(
        self, measurement_id: int, group_name: str, y: int, z: int
    ):
        with self._db.session_scope() as session:
            pos = ServoPosition(
                measurement_id=measurement_id,
                group_name=group_name,
                y_value=y,
                z_value=z,
            )
            session.add(pos)
            session.flush()
