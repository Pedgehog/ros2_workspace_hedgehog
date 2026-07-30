import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from ament_index_python.packages import get_package_share_directory
from pathlib import Path
import yaml
from enum import Enum
from typing import Dict, Any, Optional
from hedgehog_interfaces.srv import SetMode


class ServoLogicNode(Node):
    class Position(Enum):
        right = "front_right"
        middle = "front_middle"
        left = "front_left"

    def __init__(self) -> None:
        super().__init__("servo_logic_node")

        pkg_path: Path = Path(get_package_share_directory("hedgehog_detection"))
        self.config_path: Path = pkg_path / "config" / "servo_config.yaml"
        self.pos_path: Path = pkg_path / "config" / "servo_positions.yaml"

        with open(self.config_path, "r") as f:
            self.servo_map: Dict[str, Any] = yaml.safe_load(f)
        with open(self.pos_path, "r") as f:
            self.positions: Dict[str, Any] = yaml.safe_load(f)

        self.current_live_positions: Dict[str, Dict[str, int]] = {}

        self.publisher = self.create_publisher(String, "servo/command", 10)

        self.create_service(SetMode, "set_servo_mode", self.mode_service_callback)
        self.create_service(SetMode, "set_servo_live", self.live_service_callback)
        self.create_service(SetMode, "save_live_as_mode", self.save_service_callback)

        self.get_logger().info("ServoLogicNode gestartet. Services bereit.")

    def move_servo_live(self, position: Position, z: int, y: int) -> None:
        ids: Dict[str, int] = self.servo_map.get(position.value, {}).get("servo_id", {})

        if "base" in ids and "top" in ids:
            self.move_servo(ids["base"], z)
            self.move_servo(ids["top"], y)

            if position.value not in self.current_live_positions:
                self.current_live_positions[position.value] = {}
            self.current_live_positions[position.value] = {"z": z, "y": y}
        else:
            self.get_logger().error(f"Konnte IDs für {position.value} nicht finden!")

    def live_service_callback(
        self, request: SetMode.Request, response: SetMode.Response
    ) -> SetMode.Response:

        try:

            start = request.data.find("[")
            end = request.data.find("]")
            if start == -1 or end == -1:
                raise ValueError("Format muss 'mov[Name] y z' sein")

            name = request.data[start + 1 : end]

            rest = request.data[end + 1 :].strip().split()
            if len(rest) != 2:
                raise ValueError("Bitte Y und Z Werte angeben")

            y, z = int(rest[0]), int(rest[1])

            for pos in self.Position:
                if pos.value == name:
                    self.move_servo_live(pos, z, y)
                    response.success = True
                    response.message = f"Live bewegt: {name} zu Y:{y} Z:{z}"
                    return response

            raise ValueError(f"Position {name} nicht gefunden")

        except Exception as e:
            response.success = False
            response.message = f"Fehler: {str(e)}"
            return response

    def save_service_callback(
        self, request: SetMode.Request, response: SetMode.Response
    ) -> SetMode.Response:
        """
        Erwartet Format: 'sto[mode_name]'
        Beispiel: 'sto[pose_v1]'
        """
        try:
            # Format: 'sto[mode_name]'
            start = request.data.find("[")
            end = request.data.find("]")
            if not request.data.startswith("sto") or start == -1 or end == -1:
                raise ValueError("Format muss 'sto[mode_name]' sein")

            mode_name = request.data[start + 1 : end]

            # Speichern-Logik aufrufen
            self.save_current_as_mode(mode_name)

            response.success = True
            response.message = f"Modus '{mode_name}' wurde erfolgreich gespeichert."

        except Exception as e:
            response.success = False
            response.message = f"Fehler: {str(e)}"

        return response

    def save_current_as_mode(self, mode_name: str) -> None:
        """Speichert den RAM-Status in die Datei."""
        # RAM-Daten in das Positions-Dictionary übertragen
        self.positions[mode_name] = self.current_live_positions.copy()

        # In die Datei schreiben
        with open(self.pos_path, "w") as f:
            yaml.dump(self.positions, f, default_flow_style=False, sort_keys=False)

        self.get_logger().info(f"Modus '{mode_name}' in {self.pos_path} gespeichert.")

    def move_servo(self, servo_id: int, angle: int) -> None:
        msg = String()
        msg.data = f"{servo_id} {angle}"
        self.publisher.publish(msg)

    def apply_positions(self, mode: str) -> None:
        pos_data: Dict[str, Any] = self.positions.get(mode, {})
        for name, angles in pos_data.items():
            ids: Dict[str, int] = self.servo_map.get(name, {}).get("servo_id", {})
            base_id: Optional[int] = ids.get("base")
            top_id: Optional[int] = ids.get("top")

            if base_id is not None and top_id is not None:
                self.move_servo(base_id, angles["z"])
                self.move_servo(top_id, angles["y"])

    def mode_service_callback(
        self, request: SetMode.Request, response: SetMode.Response
    ) -> SetMode.Response:
        mode_name: str = request.data
        if mode_name in self.positions:
            self.get_logger().info(f"Wechsle zu Modus: {mode_name}")
            self.apply_positions(mode_name)
            response.success = True
            response.message = f"Modus {mode_name} angewendet."
        else:
            response.success = False
            response.message = f"Modus {mode_name} unbekannt."
        return response


def main(args: Optional[list] = None) -> None:
    rclpy.init(args=args)
    node = ServoLogicNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
