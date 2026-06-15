# ROS2 decision for the 3-hour workshop

## Recommendation

Do not use ROS2 for the base high-school demo.

Use LeRobot directly:

- lower setup complexity
- fewer moving parts on workshop laptops
- official SO-101 teleoperation/record/replay commands
- built-in `--display_data=true` visualization path
- easier for students to understand

## When ROS2 starts to make sense

Use ROS2 only for an advanced follow-up session where you want:

- RViz robot model visualization
- TF frames and camera transforms
- integration with ROS cameras or robot stacks
- ros2_control and MoveIt-style trajectories
- remote inference pipelines

## Middle option: Foxglove without ROS2

Foxglove has a LeRobot integration path using the LeRobot Python API and Foxglove SDK. This is a cleaner optional visualization layer than full ROS2 for this workshop.

## Advanced ROS2 references to inspect later

- `ros-physical-ai/demos`: full ROS2 + LeRobot bridge, ros2_control, Gazebo/MuJoCo, RViz/cameras.
- `legalaspro/so101-ros-physical-ai`: policy inference with ROS2 client/server patterns.

Do not put these in front of students during a 3-hour first contact workshop.
