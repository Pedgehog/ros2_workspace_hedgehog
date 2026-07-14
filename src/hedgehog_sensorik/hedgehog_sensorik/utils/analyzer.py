import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from matplotlib.figure import Figure


class Analyzer:
    def __init__(self, sensor_id: str | int) -> None:
        self._sensor_id = sensor_id
        self._slice = slice(0, 22)
        self._threshold = 100

    def analyze_peak(self, amplitudes: List[float]) -> Optional[List[Dict[str, Any]]]:
        target_range = amplitudes[self._slice]
        threshold = 100

        high_indices = [i for i, val in enumerate(target_range) if val >= threshold]

        if not high_indices:
            return None

        ranges = []
        start = high_indices[0]
        for i in range(len(high_indices) - 1):
            if high_indices[i + 1] > high_indices[i] + 1:
                ranges.append((start, high_indices[i]))
                start = high_indices[i + 1]
        ranges.append((start, high_indices[-1]))

        analyze_output = []
        start_offset = self._slice.start

        for idx, (start_idx, end_idx) in enumerate(ranges):
            length = end_idx - start_idx + 1
            segment = target_range[start_idx : end_idx + 1]
            height = max(segment)

            abs_start_index = start_idx + start_offset

            peak_data = {
                "index_peak": idx + 1,
                "start_index": abs_start_index,
                "length": length,
                "height": round(height, 2),
                "warning": "(WARNUNG: LANGER PEAK!)" if length >= 12 else "",
            }
            analyze_output.append(peak_data)

        return analyze_output


class MeasurementExporter:
    def __init__(self, sensor_id: str | int, base_dir="output"):
        self._base_dir = base_dir
        self._sensor_id = sensor_id
        if not os.path.exists(self._base_dir):
            os.makedirs(self._base_dir)

    def save(self, analyze_output: List[str], fig: Figure):
        existing = [d for d in os.listdir(self._base_dir) if d.isdigit()]
        meas_n = max([int(d) for d in existing], default=0) + 1
        meas_folder = os.path.join(self._base_dir, str(meas_n))
        os.makedirs(meas_folder, exist_ok=True)

        with open(os.path.join(meas_folder, f"peaks_s{self._sensor_id}.txt"), "a") as f:
            f.write(f"{datetime.now()}\n\n" + "\n".join(analyze_output) + "\n")
        fig.savefig(os.path.join(meas_folder, f"plot_s{self._sensor_id}.png"))
        return meas_n
