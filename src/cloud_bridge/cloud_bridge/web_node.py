import threading
from fastapi import FastAPI
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSHistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import BatteryState
import uvicorn

from cloud_bridge.routes.web import router as web_router, set_node

app = FastAPI()
app.include_router(web_router)


class WebpageNode(Node):
    def __init__(self):
        super().__init__("webpage_node")
        self.get_logger().info(
            "Webpage Node with BatteryState subscription has been started."
        )

        self.battery_voltage = 0.0
        self.battery_percentage = 0.0

        set_node(self)

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self.battery_subscription = self.create_subscription(
            BatteryState,
            "/j100_0809/platform/bms/state",
            self.battery_callback,
            qos_profile,
        )

    def battery_callback(self, msg: BatteryState):
        self.battery_voltage = msg.voltage
        self.battery_percentage = msg.percentage * 100.0 if msg.percentage >= 0 else 0.0
        self.get_logger().info(
            f"Battery update: {self.battery_percentage:.1f}% ({msg.voltage}V)"
        )


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
