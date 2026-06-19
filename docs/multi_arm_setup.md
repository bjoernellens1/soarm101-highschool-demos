# Multiple SO-ARM101 stations on one PC

> **⚠️ Status (2026-06-19): multi-arm / `rig02` is UNTESTED on real hardware.**
> The single-rig pipeline (calibration, teleop, record, replay, pose record/replay)
> has been validated end-to-end on `rig01`. The two-rig path
> (`scripts/33_parallel_teleop_two_rigs.sh`, `bimanual_demos`) has **not** been run
> because only one arm pair was attached. Treat `rig02` config below as a template,
> not a verified setup. Re-run the eval plan's Phase 7 once a second pair is connected.

The core rule is: never rely on `/dev/ttyACM0` and `/dev/ttyACM1` during a
workshop with multiple arms. USB enumeration order can change.

## Naming scheme

Use a station-based naming scheme:

```text
rig01_follower
rig01_leader
rig02_follower
rig02_leader
```

The LeRobot IDs should match the station role:

```yaml
rig01:
  follower:
    id: hs_rig01_follower
    port: /dev/so101/rig01_follower
  leader:
    id: hs_rig01_leader
    port: /dev/so101/rig01_leader
```

The ID matters because LeRobot stores calibration associated with the robot or
teleop ID. Use the same ID for calibration, teleoperation, recording, and replay.

## Setup procedure

1. Label every physical arm with tape: `rig01 follower`, `rig01 leader`, etc.
2. Plug in one device at a time.
3. Run:

```bash
bash scripts/12_snapshot_devices.sh
```

4. Copy the matching `/dev/serial/by-id` fragment into `serial_hint` in
   `configs/arms.yaml`.
5. Generate udev rules:

```bash
bash scripts/13_generate_udev_rules.sh
```

6. Review the generated file, then install:

```bash
sudo cp 99-so101-workshop.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

7. Unplug/replug devices and verify:

```bash
ls -l /dev/so101/
soarm-workshop rigs
```

## Running one selected station

```bash
soarm-workshop --rig rig01 teleop
soarm-workshop --rig rig02 teleop
```

## Running two stations in parallel

For a teacher-operated bimanual or two-table demo:

```bash
bash scripts/33_parallel_teleop_two_rigs.sh rig01 rig02
```

Keep the workspaces physically separated unless you are deliberately doing a
teacher-operated bimanual demo.
