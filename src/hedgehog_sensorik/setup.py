from setuptools import setup, find_packages
import os
from glob import glob

package_name = "hedgehog_sensorik"

setup(
    name=package_name,
    version="0.0.0",
    # Wichtig: Explizit alle Unterordner einbeziehen
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Lukas Köppl",
    maintainer_email="lukas.koeppl@tdk.com",
    description="The Sensorik which is used in the hedgehog detection",
    license="TODO: License declaration",
    entry_points={
        "console_scripts": [
            "trigger_node = hedgehog_sensorik.trigger_node:main",
            "plotting_node = hedgehog_sensorik.plotting_node:main",
            "capture_camera = hedgehog_sensorik.capture_picture_camera:main",
            "servo_controller = hedgehog_sensorik.servo_controller_node:main",
            "servo_logic = hedgehog_sensorik.servo_logic_node:main",
        ],
    },
)
