# Lab 1 exercise

This folder contains my solution for the ROS 2 robot exercise. It has four
packages:

- `diffdrive_bot` - the robot model, Gazebo world, and the original lab nodes
- `lab_interfaces` - the interfaces supplied with the lab
- `my_robot_interfaces` - the message, service, and action used in my nodes
- `my_robot_nodes` - my obstacle avoidance and square-driving nodes

## Requirements

The project was tested with Ubuntu 22.04, ROS 2 Humble, and Gazebo Harmonic.

Before using any command, source ROS 2:

```bash
source /opt/ros/humble/setup.bash
```

## Build

Build from this folder, not from the parent workspace. This keeps the copied
lab packages together with the packages written for the exercise.

```bash
cd ~/ros2_ws/src/intro_robotics_intelligent_systems_labs/lab1_exercise
colcon build --symlink-install
source install/setup.bash
```

After opening a new terminal, source both setup files again:

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/src/intro_robotics_intelligent_systems_labs/lab1_exercise/install/setup.bash
```

## Step 1: depth camera and IMU

To view the robot model and its TF frames without Gazebo:

```bash
ros2 launch diffdrive_bot display.launch.py
```

To run the sensors in Gazebo:

```bash
ros2 launch diffdrive_bot gazebo.launch.py
```

The added topics are:

```text
/depth_camera/image
/depth_camera/points
/depth_camera/camera_info
/imu
```

Useful checks:

```bash
ros2 topic hz /imu
ros2 topic echo /imu --once
ros2 run tf2_ros tf2_echo base_link depth_camera_link
```

In RViz, the depth image is shown with an Image display using
`/depth_camera/image`, and the point cloud is shown with a PointCloud2 display
using `/depth_camera/points`.

## Step 2: turn away from obstacles

Start the simulation and the original lab nodes:

```bash
ros2 launch diffdrive_bot control.launch.py
```

In another terminal, start my node:

```bash
ros2 run my_robot_nodes turn_away
```

The node subscribes to `/obstacle` and publishes `/cmd_vel`. It drives
forward when the path is clear and turns away from an obstacle when
`too_close` is true.

## Step 3: change the speeds with parameters

With `turn_away` running:

```bash
ros2 param list /turn_away
ros2 param set /turn_away forward_speed 0.4
ros2 param set /turn_away turn_speed 1.0
```

The parameters are read when an obstacle message arrives, so the change takes
effect without restarting the node.

## Step 4: robot status message

The custom message can be inspected with:

```bash
ros2 interface show my_robot_interfaces/msg/RobotStatus
ros2 topic echo /robot_status
```

The node publishes `forward`, `turning`, or `stopped`, together with the
latest obstacle distance.

## Step 5: enable service and turn-speed service

The `turn_away` node starts disabled. With the simulation and node running:

```bash
ros2 service call /turn_away_enable std_srvs/srv/SetBool "{data: true}"
ros2 service call /set_turn_speed my_robot_interfaces/srv/SetTurnSpeed "{turn_speed: 1.0}"
ros2 service call /set_turn_speed my_robot_interfaces/srv/SetTurnSpeed "{turn_speed: 3.0}"
ros2 service call /turn_away_enable std_srvs/srv/SetBool "{data: false}"
```

The `1.0` request is accepted. The `3.0` request is rejected because it is
above the default `max_turn_speed` of `1.5` rad/s. Disabling the node sends a
zero velocity and publishes the `stopped` status.

## Step 6: rotate action

Start the control launch, then start the action server:

```bash
ros2 launch diffdrive_bot control.launch.py
ros2 run my_robot_nodes rotate_server
```

In another terminal, send a quarter-turn goal:

```bash
ros2 action send_goal --feedback \
  /rotate \
  my_robot_interfaces/action/Rotate \
  "{angle: 1.57}"
```

Positive angles turn left. The server measures the turn using `/odom` and
continues to work when yaw crosses from `pi` to `-pi`.

## Step 7: drive a square

This launch file starts Gazebo, the original robot nodes, `rotate_server`, and
`square_driver`:

```bash
ros2 launch my_robot_nodes square.launch.py side_length:=0.8
```

The square driver sends one `/drive_distance` goal and waits for it to finish,
then sends one `/rotate` goal. It repeats this sequence four times.

Useful checks while it is running:

```bash
ros2 node list
rqt_graph
```

The expected graph includes `square_driver`, `rotate_server`,
`drive_distance_server`, `obstacle_detector`, and `ros_gz_bridge`.

## Screenshots

The exercise submission includes:

1. An RViz screenshot showing the depth image, point cloud, and TF frames
   including `depth_camera_link` and `imu_link`.

   https://drive.google.com/file/d/1DdbC-N7BMtV0jzTHZo5UDbsw7zuAtuC6/view?usp=sharing

   https://drive.google.com/file/d/1wrG8iVFh6gHrZtkUJkdFMgm-AkQohdbe/view?usp=sharing
2. An `rqt_graph` screenshot taken while `square.launch.py` is running,
   showing the square driver and both action connections.
https://drive.google.com/file/d/1gV4sOU_c3nCfK4VVzKSGIOC6GZRBhl1C/view?usp=sharing