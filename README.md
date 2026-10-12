# SURVIVOR — Autonomous Underground Mine Exploration

A ROS 2 simulation prototype of a four-wheel unmanned ground vehicle (UGV) for exploring and mapping an underground mine. The robot uses simulated LiDAR, SLAM Toolbox, Nav2, and frontier exploration to navigate an initially unknown environment and produce a reusable 2D occupancy map.

This repository represents the exploration and navigation stage of a larger mine-rescue concept. Thermal survivor detection, communication degradation, and motor-fault handling are planned extensions.

## Demonstrated capabilities

- Custom four-wheel UGV with a URDF model, mesh visuals, wheel joints, a front RGB camera, and a 360° LiDAR sensor.
- Custom Gazebo mine with an entrance, corridors, rooms, rocky walls, obstacles, support structures, and lighting.
- Separate open and roofed world variants for inspecting the environment or simulating an enclosed mine.
- Teleoperation-based mapping with SLAM Toolbox.
- Saved-map navigation with Nav2 and AMCL.
- Frontier-based autonomous exploration with `explore_lite`, SLAM Toolbox, and Nav2 running together.
- Exploration pause/resume and a configurable return-to-initial-position attempt.
- Map export as an image and YAML metadata for later navigation.
- RViz visualization of the robot, laser scans, map, navigation paths, and exploration frontiers.

The working demonstration uses **ideal Gazebo world odometry**. Exploration completion means that the explorer has no remaining eligible goals; it does not establish that every reachable part of the mine has been mapped. No quantitative coverage or reliability results are claimed.

## Technology stack

| Component | Technology |
| --- | --- |
| Middleware | ROS 2 Humble |
| Simulator | Gazebo Classic |
| Runtime used for development | Ubuntu 22.04 container on an Ubuntu 24.04 host |
| Robot description | URDF, STL meshes, Gazebo ROS plugins |
| Environment description | SDF worlds and models, DAE visual meshes, STL collision meshes |
| Mapping | SLAM Toolbox, asynchronous online mapping |
| Navigation | Nav2; AMCL for saved-map localization |
| Exploration | `explore_lite` from `m-explore-ros2` |
| Visualization | RViz2 |
| Build and configuration | `ament_python`, `colcon`, Python launch files, YAML |

## How the system works

Gazebo simulates the robot, mine, wheel motion, LiDAR, and camera. The drive plugin accepts velocity commands and publishes odometry. Robot State Publisher provides transforms for the robot's links.

During mapping, SLAM Toolbox combines laser scans and odometry to update `/map` and the `map → odom` transform. Nav2 plans and executes navigation goals using the map and live obstacle observations. During autonomous exploration, `explore_lite` finds boundaries between known free space and unknown space and sends navigation goals to Nav2.

The RGB camera is available for visualization and future perception work. It is not used by the current LiDAR-based SLAM pipeline.

| Interface | Purpose |
| --- | --- |
| `/scan` | Simulated LiDAR measurements |
| `/camera/image_raw` | Simulated RGB images |
| `/camera/camera_info` | Camera calibration information |
| `/cmd_vel` | Velocity commands consumed by the drive plugin |
| `/odom` | Robot odometry |
| `/joint_states` | Wheel joint states |
| `/map` | Occupancy map produced by SLAM or the map server |
| `/tf`, `/tf_static` | Coordinate transforms |
| `/clock` | Simulation time |
| `/navigate_to_pose` | Nav2 navigation action |
| `/explore/resume` | Pause/resume input for exploration |
| `/explore/frontiers` | Exploration visualization markers |

The main transform chain is `map → odom → base_footprint → base_link`, followed by the sensor and wheel links.

## Repository layout

The commands below assume this package layout inside a ROS workspace. They describe the assembled project; earlier asset archives may contain only a subset of these files.

```text
lab_ws/
├── src/
│   ├── survivor_sim/
│   │   ├── package.xml
│   │   ├── setup.py
│   │   ├── setup.cfg
│   │   ├── resource/survivor_sim
│   │   ├── survivor_sim/__init__.py
│   │   ├── launch/mine_natural.launch.py
│   │   ├── urdf/survivor_classic.urdf
│   │   ├── meshes/
│   │   ├── worlds/
│   │   │   ├── mine_natural_open.sdf
│   │   │   └── mine_natural_roof.sdf
│   │   ├── models/
│   │   │   ├── natural_mine_lower/
│   │   │   ├── natural_mine_obstacles/
│   │   │   └── natural_mine_roof/
│   │   └── config/nav2.yaml
│   └── m-explore-ros2/
└── maps/
```

Each Gazebo model contains its `model.config`, `model.sdf`, and mesh assets. The roof is a separate static model included by the roofed world; it is not a mechanically detachable robot-controlled object.

## Prerequisites and build

Use the ROS 2 Humble environment with Gazebo Classic and the following packages available:

- `gazebo_ros`, `gazebo_plugins`, and `robot_state_publisher`
- `slam_toolbox`
- `nav2_bringup` and `nav2_map_server`
- `rviz2` and `teleop_twist_keyboard`
- `explore_lite` and its message dependencies

Run all commands in the same ROS/container environment. GUI forwarding for Gazebo and RViz must already be configured. The workspace path used below is `~/lab_ws`; adjust it if needed.

If the exploration dependency is not already present:

```bash
source /opt/ros/humble/setup.bash
cd ~/lab_ws/src
git clone https://github.com/robo-friends/m-explore-ros2.git
cd ~/lab_ws
rosdep install --from-paths src/m-explore-ros2/explore src/m-explore-ros2/explore_lite_msgs --ignore-src -r -y
colcon build --packages-up-to explore_lite
```

Build the simulation package:

```bash
source /opt/ros/humble/setup.bash
cd ~/lab_ws
colcon build --packages-select survivor_sim
source install/setup.bash
```

`setup.py` must install the launch files, URDF, robot meshes, worlds, and the complete recursive `models/` directory into the package share directory. Rebuild after changing these assets so that launch files use the updated installed versions.

**In every new terminal**, source:

```bash
source /opt/ros/humble/setup.bash
source ~/lab_ws/install/setup.bash
```

For the demonstrated ideal-odometry configuration, the drive plugin in `survivor_classic.urdf` uses:

```xml
<odometry_source>1</odometry_source>
```

This configuration was selected after turning-related mapping distortion during initial encoder-odometry tests. It simplifies the prototype and does not validate navigation with realistic wheel slip or sensor noise.

## Prepare the Nav2 configuration

If `config/nav2.yaml` is already committed, use it. Otherwise, start with the installed Humble configuration:

```bash
mkdir -p ~/lab_ws/src/survivor_sim/config
cp "$(ros2 pkg prefix --share nav2_bringup)/params/nav2_params.yaml" \
  ~/lab_ws/src/survivor_sim/config/nav2.yaml
```

Apply these settings within the corresponding existing sections:

| Setting | Demonstration value |
| --- | --- |
| Local costmap `robot_radius` | `0.43` m |
| Global costmap `robot_radius` | `0.43` m |
| Controller `FollowPath.max_vel_x` | `0.20` m/s |
| Controller `FollowPath.max_vel_theta` | `0.50` rad/s |
| Controller `FollowPath.max_speed_xy` | `0.20` m/s |

The circular radius conservatively represents the robot footprint. These controller limits do not independently limit every recovery behavior or direct teleoperation command. Keep simulation time enabled throughout the running system.

## 1. Launch the mine and robot

Terminal 1:

```bash
ros2 launch survivor_sim mine_natural.launch.py world_file:=mine_natural_open.sdf
```

For the roofed environment instead:

```bash
ros2 launch survivor_sim mine_natural.launch.py world_file:=mine_natural_roof.sdf
```

The launch file selects the world, sets Gazebo model search paths, starts Gazebo with ROS integration, publishes the robot description, and spawns the robot near the entrance.

`GAZEBO_MODEL_PATH` tells Gazebo where to find custom models and meshes. The supplied launch file sets it automatically; a manual export is only needed when starting Gazebo outside that launch environment. RViz resolves ROS package resources separately and needs the sourced workspace and installed mesh files.

## 2. Map manually with teleoperation

Keep the simulator running. Terminal 2:

```bash
ros2 launch slam_toolbox online_async_launch.py use_sim_time:=true
```

Terminal 3:

```bash
rviz2 --ros-args -p use_sim_time:=true
```

Set RViz's **Fixed Frame** to `map`. Add a Map display on `/map`, LaserScan on `/scan`, RobotModel using `/robot_description`, and TF if needed. If a display does not receive data, check its topic and QoS settings against the publisher.

Terminal 4:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args \
  -p speed:=0.20 -p turn:=0.40
```

Drive through the corridors and rooms while observing map alignment. Keep the teleoperation terminal focused for keyboard input. Teleoperation is an initial integration check; the autonomous workflow below selects its own goals.

## 3. Save the map

While SLAM is still publishing the map:

```bash
mkdir -p ~/lab_ws/maps
ros2 run nav2_map_server map_saver_cli -f "$HOME/lab_ws/maps/mine_map_corrected" \
  --ros-args -p use_sim_time:=true -p save_map_timeout:=10.0
```

This exports `mine_map_corrected.pgm` and `mine_map_corrected.yaml`. The YAML describes the image location, resolution, origin, and occupancy thresholds. Keep both files together.

`save_map_timeout` is the map saver's wait timeout in seconds. It does not control exploration duration. This export is a 2D occupancy map, not a 3D mesh or a serialized SLAM pose graph.

Open the PGM in an image viewer to inspect it, or load the YAML through Nav2 to visualize the map in RViz. If working in Docker, keep the maps in a mounted or otherwise persistent workspace.

## 4. Navigate using a saved map

Stop SLAM Toolbox, exploration, teleoperation, and any previously running Nav2 instance. Gazebo and RViz can remain open if the robot has not been reset.

Start saved-map navigation:

```bash
ros2 launch nav2_bringup bringup_launch.py \
  slam:=false \
  map:="$HOME/lab_ws/maps/mine_map_corrected.yaml" \
  params_file:="$HOME/lab_ws/src/survivor_sim/config/nav2.yaml" \
  use_sim_time:=true autostart:=true use_composition:=false
```

This starts the map server, AMCL localization, and Nav2. In RViz, use **2D Pose Estimate** to indicate the robot's current position and heading. Check that the laser scan aligns with the map, then send a **Nav2 Goal**.

Add a Path display on `/plan` to see the global route. The local route can be displayed on `/local_plan` when published. Costmaps are available on `/global_costmap/costmap` and `/local_costmap/costmap`.

## 5. Explore and map autonomously

Start a fresh session for an unknown-map demonstration. Stop the saved-map Nav2 instance and any existing explorer or SLAM process. Restart the simulator to begin at the entrance, then start the following in separate sourced terminals.

**Terminal 1 — simulation:**

```bash
ros2 launch survivor_sim mine_natural.launch.py world_file:=mine_natural_roof.sdf
```

**Terminal 2 — live SLAM:**

```bash
ros2 launch slam_toolbox online_async_launch.py use_sim_time:=true
```

**Terminal 3 — navigation servers:**

```bash
ros2 launch nav2_bringup navigation_launch.py \
  params_file:="$HOME/lab_ws/src/survivor_sim/config/nav2.yaml" \
  use_sim_time:=true autostart:=true use_composition:=false
```

This launches navigation against the live SLAM map. Do not also run the saved-map bringup: SLAM owns the map and `map → odom` transform in this mode.

**Terminal 4 — visualization:**

```bash
rviz2 --ros-args -p use_sim_time:=true
```

Use the `map` fixed frame and the mapping displays described above. Add MarkerArray on `/explore/frontiers` to inspect frontier candidates.

Before starting exploration, verify that a map and laser scan are available and Nav2 has an action server:

```bash
ros2 action info /navigate_to_pose
ros2 lifecycle get /bt_navigator
ros2 lifecycle get /planner_server
ros2 lifecycle get /controller_server
```

Expect one navigation action server and active navigation nodes.

**Terminal 5 — frontier exploration:**

```bash
ros2 run explore_lite explore --ros-args \
  -p use_sim_time:=true \
  -p robot_base_frame:=base_footprint \
  -p costmap_topic:=/map \
  -p costmap_updates_topic:=/map_updates \
  -p visualize:=true \
  -p planner_frequency:=0.5 \
  -p progress_timeout:=45.0 \
  -p min_frontier_size:=0.5 \
  -p return_to_init:=true
```

The explorer selects frontier goals and delegates motion to Nav2 while SLAM continues updating the map. `progress_timeout` controls how long lack of progress is tolerated for a goal. `min_frontier_size` filters small frontier candidates. The planner reevaluates goals at the configured frequency.

With `return_to_init` enabled, the explorer attempts to return to the pose recorded when exploration started. That pose is not necessarily the mine entrance if the robot has already moved. Return success depends on navigation succeeding.

Do not send teleoperation commands or manual RViz navigation goals while the explorer controls the robot.

Pause or resume exploration:

```bash
# Pause
ros2 topic pub --once /explore/resume std_msgs/msg/Bool "{data: false}"

# Resume
ros2 topic pub --once /explore/resume std_msgs/msg/Bool "{data: true}"
```

Save the autonomous map while SLAM is still running:

```bash
ros2 run nav2_map_server map_saver_cli -f "$HOME/lab_ws/maps/mine_autonomous" \
  --ros-args -p use_sim_time:=true -p save_map_timeout:=10.0
```

Map saving is currently manual. Exploration may stop after candidates are exhausted or rejected; inspect the resulting map before treating the mission as complete. The entrance is open and no exploration boundary currently prevents goals outside the mine.

## Troubleshooting

| Symptom | Checks and fixes |
| --- | --- |
| `NameError: name 'PY' is not defined` during build | Remove an accidentally pasted shell heredoc delimiter from `setup.py`. |
| Spawn fails with an XML encoding declaration error | Remove the XML encoding declaration from the URDF used by `spawn_entity.py`. |
| Robot appears but the mine does not | Check the selected world path, `worlds/` installation, model installation, and Gazebo model search paths. |
| Old robot or world remains after editing | Rebuild `survivor_sim`, source the workspace, and restart the affected launch processes. |
| RViz cannot load STL meshes | Check installed mesh files and URDF resource paths; run RViz in the sourced ROS environment. |
| `/spawn_entity` is unavailable | Ensure Gazebo was launched with the ROS factory plugin through `gazebo_ros`; inspect server errors and model-loading delays. |
| Robot does not respond to commands | Confirm that the drive plugin subscribes to `/cmd_vel` and that Gazebo is not paused. |
| No autonomous movement | Check `/map`, `/scan`, transforms, active Nav2 nodes, and `/navigate_to_pose`; pause exploration and test a manual goal to isolate navigation problems. |
| Path is not visible in RViz | Add a Path display on `/plan`, use the `map` fixed frame, and send a goal. |
| Map or robot jumps in RViz | Check for duplicate localization/SLAM publishers, inconsistent simulation time, and odometry problems. |

Useful inspection commands:

```bash
ros2 node list
ros2 topic list
ros2 topic info /odom --verbose
ros2 topic info /cmd_vel --verbose
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 param get /slam_toolbox use_sim_time
```

## Current limitations and future work

The prototype demonstrates simulation integration, 2D mapping, navigation, and frontier exploration. It has not been validated on a physical robot or for operational mine rescue.

Planned extensions include:

- Encoder and IMU fusion with realistic noise and wheel slip.
- Motor/encoder fault injection, health monitoring, and degraded mission behavior.
- RF link emulation with packet loss, latency, bandwidth limits, and prioritized status reporting.
- Thermal sensing, survivor detection, and human confirmation of detections.
- A mission supervisor, exploration boundaries, automatic map saving, and mission logs.
- Repeatable evaluation of coverage, completion time, failed goals, collisions, and return success.
- Hardware testing and migration to a maintained simulator for further development.

The current prototype does not implement GPS-based underground localization, thermal perception, survivor detection, communication fault handling, or motor fault recovery.

## Development and attribution

Developed by Sreerag as a laboratory prototype. Personal work included defining requirements, assembling the ROS workspace, integrating robot and environment assets, configuring sensors and navigation, running experiments, debugging build and launch issues, and demonstrating the mapping and exploration workflow.

SLAM, localization, navigation, and frontier exploration use existing open-source packages; their underlying algorithms were not implemented from scratch for this project.
