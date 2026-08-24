import os
from glob import glob
from setuptools import find_packages, setup

package_name = "servo_control"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="administrator",
    maintainer_email="traktor.koeppl@gmail.com",
    description="Package for servo controlling and servo position logic",
    license="TODO: License declaration",
    extras_require={
        "test": [
            "pytest",
        ],
    },
    entry_points={
        "console_scripts": [
            "servo_control_node = servo_control.servo_controller_node:main",
            "servo_joy_node = servo_control.servo_joy_node:main",
        ],
    },
)
