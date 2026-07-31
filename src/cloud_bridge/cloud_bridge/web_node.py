import threading
from fastapi import FastAPI
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSHistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import uvicorn

from hedgehog_interfaces.srv import GetSensorIds
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

app = FastAPI()
app.include_router(web_router)
app.include_router(recording_router)
app.include_router(ussm_router)
app.include_router(camera_router)


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

        set_web_node(self)
        set_recording_node(self)
        set_ussm_node(self)
        set_camera_node(self)

        client = self.create_client(GetSensorIds, "/sensoric/get_active_sensors")
        while not client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(
                "Waiting for service '/sensoric/get_active_sensors'..."
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
            "/camstream/cam_button/image_raw",
            self.cam_button_callback,
            qos_profile,
        )
        self.create_subscription(
            Image,
            "/camstream/cam_top/image_raw",
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

    def start_recording(self):
        self.get_logger().info("Recording started via API request.")

    def stop_recording(self):
        self.get_logger().info("Recording stopped via API request.")


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
