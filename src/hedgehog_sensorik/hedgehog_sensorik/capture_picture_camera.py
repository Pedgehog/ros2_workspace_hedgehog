import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_srvs.srv import Trigger
from cv_bridge import CvBridge
import cv2
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class CameraCaptureNode(Node):
    def __init__(self):
        super().__init__("camera_capture_node")

        self.save_path = Path.cwd() / "output" / "pictures"
        self.save_path.mkdir(parents=True, exist_ok=True)

        self._bridge = CvBridge()
        self._latest_images = {}

        self.create_subscription(
            Image,
            "cam_button/image_raw",
            lambda msg: self.update_image(msg, "button"),
            10,
        )
        self.create_subscription(
            Image, "cam_top/image_raw", lambda msg: self.update_image(msg, "top"), 10
        )

        self._srv = self.create_service(
            Trigger, "capture_photo", self.capture_service_callback
        )
        self.get_logger().info(f"Service bereit. Speichere unter: {self.save_path}")

    def update_image(self, msg, camera_name):
        self._latest_images[camera_name] = msg

    def capture_service_callback(
        self, request: Trigger.Request, response: Trigger.Response
    ):
        self.save_path.mkdir(parents=True, exist_ok=True)
        if not self._latest_images:
            response.success = False
            response.message = "Keine Bilder verfügbar."
            return response

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_files = []

        for name, img_msg in self._latest_images.items():
            filename = self.save_path / f"{name}_{timestamp}.jpg"

            try:
                cv_image = self._bridge.imgmsg_to_cv2(img_msg, desired_encoding="bgr8")
                cv2.imwrite(str(filename), cv_image)  # cv2 braucht einen String-Pfad
                saved_files.append(name)
            except Exception as e:
                self.get_logger().error(f"Fehler bei {name}: {e}")

        response.success = True
        response.message = f"Fotos gespeichert: {', '.join(saved_files)}"
        return response


def main(args=None):
    rclpy.init(args=args)
    node = CameraCaptureNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
