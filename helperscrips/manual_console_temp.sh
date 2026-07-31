# "envelope": f"esa[{sensor_hex}] {sample_count} {time_per_sample};",
# ros2 launch ussm_launch_file program.launch.py category:=envelope plotter:=true pairs:=fm
# clear && ros2 topic echo /ussm_envelope0
# ros2 run tdk_ussm tdk_ussm_node

# ros2 service call /tdk_ussm/req_dist_streamout tdk_ussm_interfaces/srv/DistanceStreamoutService "{cmd_request: 'esa[0x01] 256 50;'}"


# sudo systemctl restart clearpath-robot.service


# 1. In das Workspace-Verzeichnis wechseln
cd ~/ros2_ws_hedgehog

# 2. ALLES löschen, was noch nach "detection" riecht
rm -rf build/ install/ log/
colcon build --packages-select hedgehog_interfaces
# 3. Nur die zwei Pakete bauen, die du willst
colcon build --packages-select hedgehog_recording sensor_envelope servo_control camera_control cloud_bridge  --symlink-install

# 4. Neu sourcen
source install/setup.bash