from enum import Enum
from typing import Any


class Sensor:
    def __init__(self, sensor_id: str | int | list) -> None:
        self.sensor_id = sensor_id
        self.sensor_mask = self._get_sensor_mask(sensor_id)

    class Commando(Enum):
        RANGE = "range"
        ENVELOPE = "envelope"

    def _get_sensor_mask(self, sensor_id: str | int | list) -> str:
        if isinstance(sensor_id, list):
            mask = 0
            for s in sensor_id:
                mask |= 1 << self._check_sensor_range(s)
            return hex(mask)
        else:
            return hex(1 << int(self._check_sensor_range(sensor_id)))

    def _get_comando(
        self,
        commando: Commando,
        sensor_hex: str,
        sample_count: int = 256,
        time_per_sample: int = 50,
    ) -> str:
        command_map = {
            self.Commando.RANGE: f"sto[{sensor_hex}] -1 100 0;",
            self.Commando.ENVELOPE: f"esa[{sensor_hex}] {sample_count} {time_per_sample};",
        }
        return command_map.get(commando, "")

    def _check_sensor_range(self, sensor_id: int | str, length: int = 8) -> int:
        if 0 <= (val := int(sensor_id)) < (1 << length):
            return val
        raise ValueError(f"Sensor_id {sensor_id} out of range")

    def __call__(
        self, command: Commando, sample_count: int = 256, time_per_sample: int = 50
    ) -> str:
        return self._get_comando(
            command, self.sensor_mask, sample_count, time_per_sample
        )
