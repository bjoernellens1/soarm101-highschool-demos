# Web interface decision

## What exists

### Official option: LeLab

Hugging Face now has LeLab, an official browser UI on top of LeRobot. It covers
calibration, teleoperation, recording, training, replay, inference, and Hub upload.
This is the most complete path for a polished LeRobot web workflow.

Why not depend on it for the 3-hour school demo?

- It is broader than we need.
- It may change quickly together with LeRobot.
- A school workshop benefits from a very small, auditable launcher with only the
  buttons the teacher needs.

### Community option: WhitneyDesignLabs/lerobot-web-interface

This appears to be an easy-to-use web interface for SO101 arms with single-arm
and bimanual teleoperation ideas.

Why not copy it?

- We should not inherit unknown workshop-time complexity.
- We need a self-contained transferable repo.
- Our launcher should just wrap known-good official commands.

## Decision

Use the local `soarm-web` launcher in this repo for high-school sessions:

- local-only Flask app
- station selector for multiple rigs
- buttons for calibration, teleop, local recording, replay
- logs stored under `logs/`
- no training/VLA buttons in the default UI

For advanced sessions, inspect LeLab first before building more custom UI.
