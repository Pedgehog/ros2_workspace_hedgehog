import threading
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSHistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image, BatteryState
from std_msgs.msg import Bool
from std_srvs.srv import Trigger
from cv_bridge import CvBridge
import cv2
import uvicorn
import json
import psutil
from hedgehog_interfaces.srv import GetSensorIds, ManageDatabase
from tdk_ussm_interfaces.msg import Envelope
from cloud_bridge.routes.web import router as web_router, set_node as set_web_node
from cloud_bridge.routes.recording import (
    router as recording_router,
    set_node as set_recording_node,
)
from cloud_bridge.routes.ussm import router as ussm_router, set_node as set_ussm_node
from cloud_bridge.routes.camera import (
    router as camera_router,
    set_node as set_camera_node,
)
from cloud_bridge.routes.system import (
    router as system_router,
    set_node_reference as set_system_node,
)
from cloud_bridge.routes.database import (
    router as database_router,
    set_node as set_database_node,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(web_router)
app.include_router(recording_router)
app.include_router(ussm_router)
app.include_router(camera_router)
app.include_router(system_router)
app.include_router(database_router)


class DatabaseRequest(BaseModel):
    db_name: str


class WebpageNode(Node):
    def __init__(self):
        super().__init__("webpage_node")
        self.get_logger().info(
            "Webpage Node for USSM, Cameras & Recording has been started."
        )

        self.active_sensors = []
        self.ussm_data = {}
        self.ussm_id = 0

        self.bridge = CvBridge()
        self.cam_button_frame = None
        self.cam_button_id = 0
        self.cam_top_frame = None
        self.cam_top_id = 0

        self.bms_voltage = 0.0
        self.bms_percentage = 0.0

        bms_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self.bms_sub = self.create_subscription(
            BatteryState, "/j100_0809/platform/bms/state", self._bms_callback, bms_qos
        )

        set_web_node(self)
        set_recording_node(self)
        set_ussm_node(self)
        set_camera_node(self)
        set_system_node(self)
        set_database_node(self)

        self.create_subscription(
            Bool, "/tdk_robot/database/measurement_success", self._success_callback, 10
        )
        self._status_client = self.create_client(
            Trigger, "/tdk_robot/database/get_recording_status"
        )
        self._start_client = self.create_client(
            Trigger, "/tdk_robot/database/start_recording"
        )
        self._stop_client = self.create_client(
            Trigger, "/tdk_robot/database/stop_recording"
        )
        self._toggle_client = self.create_client(
            Trigger, "/tdk_robot/database/toggle_recording"
        )
        self._db_management_service = self.create_client(
            ManageDatabase, "/tdk_robot/database/manage_database"
        )

        client = self.create_client(
            GetSensorIds, "/tdk_robot/sensoric/get_active_sensors"
        )
        while not client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(
                "Waiting for service '/tdk_robot/sensoric/get_active_sensors'..."
            )

        future = client.call_async(GetSensorIds.Request())
        rclpy.spin_until_future_complete(self, future)

        result = future.result()
        if result is not None:
            self.active_sensors = list(result.sensor_ids)
        else:
            self.get_logger().error("Service call failed. Using default.")
            self.active_sensors = [0, 1, 2, 3, 4]

        self.get_logger().info(f"Received sensors from service: {self.active_sensors}")

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )

        for sid in self.active_sensors:
            self.create_subscription(
                Envelope,
                f"/ussm_envelope{sid}",
                self._get_callback_for_sid(sid),
                qos_profile,
            )

        self.create_subscription(
            Image,
            "/tdk_robot/camera/cam_button/image_raw",
            self.cam_button_callback,
            qos_profile,
        )
        self.create_subscription(
            Image,
            "/tdk_robot/camera/cam_top/image_raw",
            self.cam_top_callback,
            qos_profile,
        )

    def _get_callback_for_sid(self, sid: int):
        def callback(msg: Envelope):
            self._ussm_callback(msg, sid)

        return callback

    def _ussm_callback(self, msg: Envelope, sensor_id: int):
        self.ussm_data[sensor_id] = list(msg.amplitudes)
        self.ussm_id += 1

    def _bms_callback(self, msg: BatteryState):
        self.bms_voltage = float(msg.voltage)
        self.bms_percentage = (
            round(float(msg.percentage) * 100.0, 1) if msg.percentage >= 0 else 0.0
        )

    def get_bms_values(self) -> dict:
        return {
            "voltage": round(self.bms_voltage, 2),
            "percentage": self.bms_percentage,
        }

    def get_sys_values(self) -> dict:
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            temps = {}
            try:
                sensor_temps = psutil.sensors_temperatures()
                if sensor_temps:
                    for name, entries in sensor_temps.items():
                        temps[name] = [
                            {"label": e.label, "current": e.current} for e in entries
                        ]
            except Exception:
                pass

            return {
                "cpu_percent": cpu,
                "memory": {
                    "total": mem.total,
                    "available": mem.available,
                    "percent": mem.percent,
                    "used": mem.used,
                },
                "temperatures": temps,
            }
        except Exception as e:
            self.get_logger().warn(f"Fehler bei Systemwerten: {e}")
            return {}

    def cam_button_callback(self, msg: Image):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            _, encoded_image = cv2.imencode(".jpg", cv_image)
            self.cam_button_frame = encoded_image.tobytes()
            self.cam_button_id += 1
        except Exception as e:
            self.get_logger().error(f"Failed to process cam_button image: {e}")

    def cam_top_callback(self, msg: Image):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            _, encoded_image = cv2.imencode(".jpg", cv_image)
            self.cam_top_frame = encoded_image.tobytes()
            self.cam_top_id += 1
        except Exception as e:
            self.get_logger().error(f"Failed to process cam_top image: {e}")

    def _success_callback(self, msg: Bool) -> None:
        if msg.data:
            self.get_logger().info(
                "[CONTROL] Measurement success confirmed from database."
            )

    def start_recording(self):
        self.get_logger().info("Recording started via API request.")
        if self._start_client.wait_for_service(timeout_sec=0.1):
            future = self._start_client.call_async(Trigger.Request())
            rclpy.spin_until_future_complete(self, future, timeout_sec=0.5)

    def stop_recording(self):
        self.get_logger().info("Recording stopped via API request.")
        if self._stop_client.wait_for_service(timeout_sec=0.1):
            future = self._stop_client.call_async(Trigger.Request())
            rclpy.spin_until_future_complete(self, future, timeout_sec=0.5)

    def trigger_recording(self):
        self.get_logger().info("Recording triggered (toggled) via API request.")
        if self._toggle_client.wait_for_service(timeout_sec=0.1):
            future = self._toggle_client.call_async(Trigger.Request())
            rclpy.spin_until_future_complete(self, future, timeout_sec=0.5)

    def is_recording(self):
        if not self._status_client.wait_for_service(timeout_sec=0.1):
            return False

        future = self._status_client.call_async(Trigger.Request())
        rclpy.spin_until_future_complete(self, future, timeout_sec=0.5)

        result = future.result()
        if result is not None:
            return result.message.lower() == "true"
        return False

    def get_ussm_settings(self) -> dict:
        client = self.create_client(Trigger, "/tdk_robot/sensoric/get_ussm_settings")
        if not client.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn(
                "Service /tdk_robot/sensoric/get_ussm_settings nicht verfügbar!"
            )
            return {}

        req = Trigger.Request()
        future = client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)

        result = future.result()
        if result is not None:
            if result.success:
                try:
                    return json.loads(result.message)
                except Exception:
                    return {"raw_message": result.message}
        return {}

    def list_databases(self) -> dict:
        try:
            if self._db_management_service.wait_for_service(timeout_sec=0.5):
                req_list = ManageDatabase.Request()
                req_list.action = "list"
                req_list.db_name = ""
                res_list = self._db_management_service.call(req_list)

                req_curr = ManageDatabase.Request()
                req_curr.action = "current"
                req_curr.db_name = ""
                res_curr = self._db_management_service.call(req_curr)

                databases = (
                    list(res_list.available_db_names)
                    if res_list and res_list.success
                    else []
                )
                active_db = res_curr.message if res_curr and res_curr.success else ""

                return {"databases": databases, "active_database": active_db}
        except Exception as e:
            self.get_logger().warn(
                f"Fehler beim Abrufen der Datenbanken via Service: {e}"
            )

        return {"databases": [], "active_database": ""}

    def create_database(self, db_name: str) -> bool:
        try:
            if self._db_management_service.wait_for_service(timeout_sec=0.5):
                req = ManageDatabase.Request()
                req.action = "create"
                req.db_name = db_name

                result = self._db_management_service.call(req)
                if result:
                    return result.success
        except Exception as e:
            self.get_logger().error(f"Fehler beim Erstellen der DB via Service: {e}")
        return False

    def select_database(self, db_name: str) -> bool:
        try:
            if self._db_management_service.wait_for_service(timeout_sec=0.5):
                req = ManageDatabase.Request()
                req.action = "switch"
                req.db_name = db_name

                result = self._db_management_service.call(req)
                if result:
                    return result.success
        except Exception as e:
            self.get_logger().error(f"Fehler beim Wechseln der DB via Service: {e}")
        return False


def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


def main(args=None):
    rclpy.init(args=args)
    node = WebpageNode()

    server_thread = threading.Thread(target=run_fastapi, daemon=True)
    server_thread.start()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
