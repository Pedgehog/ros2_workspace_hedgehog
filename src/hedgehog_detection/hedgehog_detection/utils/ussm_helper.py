from enum import Enum
from typing import Any


class Sensor:
    def __init__(self, sensor_id: str | int) -> None:
        self.sensor_id = sensor_id
        self.sensor_mask = self._get_sensor_mask(sensor_id)

    class Commando(Enum):
        RANGE = "range"
        ENVELOPE = "envelope"

    def _get_sensor_mask(self, sensor_id: str | int) -> str:
        if isinstance(sensor_id, str):
            try:
                n = int(sensor_id.split("_")[-1])
            except (ValueError, IndexError):
                return "0x0"
        else:
            n = sensor_id
        return hex(1 << n)

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

    def __call__(
        self, command: Commando, sample_count: int = 256, time_per_sample: int = 50
    ) -> str:
        return self._get_comando(
            command, self.sensor_mask, sample_count, time_per_sample
        )
