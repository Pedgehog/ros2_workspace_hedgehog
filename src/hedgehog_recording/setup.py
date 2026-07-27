from setuptools import find_packages, setup
import os
from glob import glob

package_name = "hedgehog_recording"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name, "launch"),
            glob(os.path.join("launch", "*launch.py")),
        ),
    ],
    install_requires=[
        "setuptools",
        "sqlalchemy",
    ],
    zip_safe=True,
    maintainer="Lukas Köppl",
    maintainer_email="lukas.koeppl@tdk.com",
    description="Recording functionality for hedgehog detection",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "database_node = hedgehog_recording.database_node:main",
            "recording_controller_node = hedgehog_recording.recording_controller_node:main",
        ],
    },
)
