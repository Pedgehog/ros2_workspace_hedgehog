from setuptools import find_packages, setup

package_name = "camera_control"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            "share/" + package_name + "/launch",
            [
                "launch/usb_cam.launch.py",
                "launch/camera_view.launch.py",
            ],
        ),
        (
            "share/" + package_name + "/config",
            [
                "config/cam_button.yaml",
                "config/cam_top.yaml",
            ],
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="administrator",
    maintainer_email="traktor.koeppl@gmail.com",
    description="Package for camera control, view, and capture logic",
    license="TODO: License declaration",
    extras_require={
        "test": [
            "pytest",
        ],
    },
    entry_points={
        "console_scripts": [
            "capture_picture_camera = camera_control.capture_picture_camera:main",
        ],
    },
)
