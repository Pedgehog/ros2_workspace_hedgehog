import os
from glob import glob
from setuptools import find_packages, setup

package_name = "sensor_envelope"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name, "launch"),
            glob(os.path.join("launch", "*.launch.py")),
        ),
        (
            os.path.join("share", package_name, "config"),
            glob(os.path.join("config", "*.yaml")),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="administrator",
    maintainer_email="administrator@todo.todo",
    description="Sensor envelope trigger and plotting package",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "trigger_node = sensor_envelope.trigger_node:main",
            "plotting_node = sensor_envelope.plotting_node:main",
        ],
    },
)
