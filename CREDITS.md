# Credits, references, and code reuse policy

This repository is a thin teaching wrapper around the official Hugging Face
LeRobot command-line tools. It is intentionally not a fork of LeRobot.

## Code reuse status

No external source code was copied into this repository.

The local launcher, shell scripts, calibration backup tool, udev helper, and
OpenCV color demo were written for this workshop repository. The LeRobot command
syntax is based on the official LeRobot documentation and examples.

## Primary upstream references

- Hugging Face LeRobot: official robot-learning library and CLI tools.
- Hugging Face SO-101 documentation: official SO-101 setup, calibration, leader
  and follower workflow.
- Hugging Face LeLab: official web UI for LeRobot; useful as a reference for
  what a full web workflow can become.
- TheRobotStudio SO-ARM100/SO-101 repository: hardware reference and optional
  printed parts/camera mounts.

## Community examples inspected for ideas, not copied

- WhitneyDesignLabs/lerobot-web-interface: community web interface idea for
  SO101 arms, including single-arm and bimanual teleoperation.
- legalaspro/so101-ros-physical-ai: advanced ROS2 stack for SO-101 with Rerun,
  rosbag-to-LeRobot conversion, and policy inference.
- CreatorKanata/gum-pickup-so-arm101 and related SO101 pick-place examples:
  task inspiration for candy/gum/cube manipulation.

When using snippets from any external project later, copy the exact source URL,
commit hash, license, copied file/function, and local destination into this file.
