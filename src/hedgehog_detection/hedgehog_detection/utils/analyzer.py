def analyze_peak(amplitudes, sensor_id) -> str | None:
    threshold = 100
    high_indices = [i for i, val in enumerate(amplitudes) if val >= threshold]

    if not high_indices:
        return

    ranges = []
    start = high_indices[0]
    for i in range(len(high_indices) - 1):
        if high_indices[i + 1] > high_indices[i] + 1:
            ranges.append((start, high_indices[i]))
            start = high_indices[i + 1]
    ranges.append((start, high_indices[-1]))

    for idx, (start_idx, end_idx) in enumerate(ranges):
        length = end_idx - start_idx + 1
        segment = amplitudes[start_idx : end_idx + 1]
        height = max(segment)

        if length >= 12:
            return f"Sensor {sensor_id} | Peak {idx+1}: Länge={length}, Höhe={height:.2f} (WARNUNG: LANGER PEAK!)"
        else:
            return (
                f"Sensor {sensor_id} | Peak {idx+1}: Länge={length}, Höhe={height:.2f}"
            )
