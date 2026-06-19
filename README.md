# SO-ARM101 High-School Demo Lab

A self-contained, transferable workshop repo for 3-hour high-school robotics sessions with the SO-ARM101 / SO-101 kit and the official Hugging Face LeRobot tools.

The design goal is simple:

> manual control -> teach poses -> replay automation -> camera color reaction -> optional dataset recording

This repo intentionally avoids ROS2 for the base workshop. It uses LeRobot's official CLI and Python API where helpful. ROS2/Foxglove are left as optional advanced visualization tracks.

## Recommended 3-hour session

| Time | Activity | File / command |
|---:|---|---|
| 0:00-0:15 | Wow demo: teleop or replay a saved episode | `scripts/03_teleop_wow.sh` or `scripts/05_replay_episode.sh` |
| 0:15-0:45 | Students drive the follower with the leader arm | `scripts/03_teleop_wow.sh` |
| 0:45-1:20 | Pose automation: define HOME, PICK, DROP | `python -m soarm101_workshop.pose_recorder --port <follower-port> --id <follower-id>` |
| 1:20-1:35 | Break + robot wave / dance | `python -m soarm101_workshop.replay_poses` |
| 1:35-2:20 | Camera color detection | `python scripts/06_color_sort_cv.py` |
| 2:20-2:55 | Sorting / rescue mini challenge | `docs/teacher_checklist.md` |
| 2:55-3:00 | Wrap-up: robotics = sensing + control + debugging | discussion |

## What students learn

- A robot arm is a chain of joints.
- Teleoperation maps human motion to robot motion.
- Automation is a sequence of repeatable states.
- Cameras can make robot behavior conditional.
- Learning from demonstrations starts with clean, consistent data.

## Quick install

Current LeRobot requires Python 3.12+. The easiest transferable install is:

```bash
bash scripts/10_install_linux_uv.sh
source .venv/bin/activate
```

Fallback without `uv`:

```bash
PYTHON_BIN=python3.12 bash scripts/11_install_linux_pip.sh
source .venv/bin/activate
```

## API-based architecture

The project is API-first: a FastAPI service (`soarm-api`) is the single source of
truth for every rig operation. The `soarm-workshop` CLI and the web UI are both
clients of that API.

Start the API (serves the web UI at `/` and OpenAPI docs at `/docs`):

```bash
export SOARM_API_TOKEN=choose-a-token      # or SOARM_ALLOW_LOCALHOST_NO_AUTH=1 for local-only
soarm-api                                  # http://127.0.0.1:7860
# or: bash scripts/32_web_launcher.sh
```

Configuration (env, all prefixed `SOARM_`): `SOARM_API_TOKEN`, `SOARM_HOST`
(default `127.0.0.1`), `SOARM_PORT` (default `7860`), `SOARM_CONFIG_PATH`,
`SOARM_ALLOW_LOCALHOST_NO_AUTH`, `SOARM_CORS_ORIGINS`.

The CLI talks to a running API (`SOARM_API_URL`, default `http://127.0.0.1:7860`;
`SOARM_API_TOKEN` for auth):

```bash
soarm-workshop rigs
soarm-workshop find-ports
soarm-workshop --rig rig01 teleop
soarm-workshop status
soarm-workshop stop-all
```

Direct HTTP (token required unless loopback bypass is enabled):

```bash
curl -H "Authorization: Bearer $SOARM_API_TOKEN" http://127.0.0.1:7860/api/rigs
curl -X POST -H "Authorization: Bearer $SOARM_API_TOKEN" \
  http://127.0.0.1:7860/api/rigs/rig01/teleop
```

The web UI exposes the workshop-critical actions: select station, calibrate
follower/leader, teleop, record, replay, and stop. **Single worker only** —
serial ports are exclusive, so never run more than one API worker.

Deploy artifacts: `deploy/soarm-api.service` (systemd) and `deploy/Dockerfile`
(needs USB `--device` passthrough). See those files for usage.

## Multiple arms on one PC

Prefer `configs/arms.yaml` over only `.env` files. Each station gets stable names:

```yaml
rig01:
  follower:
    id: hs_rig01_follower
    port: /dev/so101/rig01_follower
  leader:
    id: hs_rig01_leader
    port: /dev/so101/rig01_leader
```

Do not rely on `/dev/ttyACM0` ordering in a workshop. Use `/dev/serial/by-id` or generated udev symlinks.

Snapshot devices:

```bash
bash scripts/12_snapshot_devices.sh
```

Generate udev rules after filling `serial_hint` in `configs/arms.yaml`:

```bash
bash scripts/13_generate_udev_rules.sh
sudo cp 99-so101-workshop.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Run selected rig:

```bash
soarm-workshop --rig rig01 teleop
soarm-workshop --rig rig02 record --hf-user local --episodes 5
```

Teacher-only two-rig teleop:

```bash
bash scripts/33_parallel_teleop_two_rigs.sh rig01 rig02
```

See `docs/multi_arm_setup.md`.

## Configure single-station legacy scripts

For the simple shell scripts, copy the env file:

```bash
cp configs/arms.env.example configs/arms.env
```

Edit the serial ports and IDs:

```bash
FOLLOWER_PORT=/dev/so101/rig01_follower
LEADER_PORT=/dev/so101/rig01_leader
FOLLOWER_ID=hs_rig01_follower
LEADER_ID=hs_rig01_leader
CAMERA_CONFIG="{ front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}"
HF_USER=your-hf-user
```

Find ports with:

```bash
bash scripts/00_find_ports.sh
```

## First-time hardware setup

```bash
bash scripts/01_calibrate_follower.sh
bash scripts/02_calibrate_leader.sh
```

Use the same IDs for calibration, teleoperation, recording, and replay.

## Calibration backup and restore

Backup after a successful calibration:

```bash
bash scripts/20_backup_calibration.sh --note "rig01 calibrated and tested"
```

Dry-run restore on a new PC:

```bash
bash scripts/21_restore_calibration.sh calibration_backups/<backup>.tar.gz --dry-run
```

Restore:

```bash
bash scripts/21_restore_calibration.sh calibration_backups/<backup>.tar.gz
```

See `docs/calibration_backup_restore.md`.

## Run the wow teleoperation demo

```bash
bash scripts/03_teleop_wow.sh
```

By default it runs with `--display_data=true`, so LeRobot/Rerun can show camera and state data without ROS2.

## Record a tiny demo dataset

For high-school sessions, keep this tiny: 3-5 short episodes is enough to explain the idea of imitation learning without doing full training live.

```bash
bash scripts/04_record_micro_dataset.sh
```

YAML-based alternative:

```bash
bash scripts/31_rig_record_local.sh rig01
```

## Replay an episode

```bash
bash scripts/05_replay_episode.sh YOUR_HF_USER/hs-so101-cube-sort 0
```

## Pose teaching (named poses)

Record named joint poses, then replay them as a tiny choreography. Both commands
require `--port` (and should use the calibrated `--id`):

```bash
python -m soarm101_workshop.pose_recorder --port /dev/so101/rig01_follower --id hs_rig01_follower
python -m soarm101_workshop.replay_poses  --port /dev/so101/rig01_follower --id hs_rig01_follower
```

Note: `pose_recorder` reads the follower's own joint angles, so to hand-teach a
pose you must first disable follower torque (otherwise you only capture the
current, stiff position). For robust dataset-based playback prefer the official
`lerobot-replay` path (see "Replay an episode").

## Camera-only color demo

This demo is intentionally independent of the arm. It is great when you want the students to understand the sensing part before letting the robot move.

```bash
python scripts/06_color_sort_cv.py --camera 0
```

Press `q` to quit.

## Safety defaults

- Use foam cubes, sponge blocks, LEGO-sized blocks, or candy wrappers.
- Tape a printed workspace mat to the table.
- Tape the bins/zones down.
- Run slow and low.
- Keep one adult near the power plug or emergency stop.
- Keep students' hands outside the follower workspace while it moves.
- If using leader-following/follower-tracking mode, do not let a student hold the leader handle while the leader is being driven by software.

## Repository philosophy

This repo is a teaching wrapper around LeRobot, not a fork of LeRobot. Keep the magic thin and visible.

See `CREDITS.md` for references and code reuse policy.
