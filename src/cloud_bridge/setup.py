from glob import glob
import os
from setuptools import setup

package_name = "cloud_bridge"

setup(
    name=package_name,
    version="0.0.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name, "web"),
            glob("web/*"),
        ),
    ],
    install_requires=["setuptools", "fastapi", "uvicorn"],
    zip_safe=True,
    maintainer="administrator",
    maintainer_email="todo@todo.com",
    description="Cloud Bridge for FastAPI and ROS 2",
    license="TODO",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": ["web_node = cloud_bridge.web_node:main"],
    },
)
