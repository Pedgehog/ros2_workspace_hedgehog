from setuptools import find_packages, setup
import os
from glob import glob

package_name = "hedgehog_sensorik"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name, "launch"),
            glob(os.path.join("launch", "*launch.[pxy][yma]*")),
        ),
        (
            os.path.join("share", package_name, "config"),
            glob(os.path.join("config", "*.yaml")),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Lukas Köppl",
    maintainer_email="lukas.koeppl@tdk.com",
    description="The Sensric which is used in the hedgehog detection",
    license="TODO: License declaration",
    extras_require={
        "test": [
            "pytest",
        ],
    },
    entry_points={
        "console_scripts": [
            "envelope_simple = hedgehog_sensorik.envelope_simple:main",
            "envelope_multi = hedgehog_sensorik.envelope_multi:main",
            "capture_camera = hedgehog_sensorik.chapture_picture_camera:main",
            "servo_controller = hedgehog_sensorik.servo_controller_node:main",
            "servo_logic = hedgehog_sensorik.servo_logic_node:main",
        ],
    },
)
