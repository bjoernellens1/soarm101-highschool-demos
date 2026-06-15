# Calibration backup and restore

LeRobot stores calibration/configuration data outside this repository. The exact
cache location may differ by LeRobot version, so the backup tool includes all
common paths it can find:

- `~/.cache/huggingface/lerobot/calibration`
- `~/.cache/lerobot/calibration`
- `~/.cache/calibration`
- local workshop config files under `configs/`

## Backup

```bash
bash scripts/20_backup_calibration.sh --note "after calibrating rig01 and rig02"
```

This creates:

```text
calibration_backups/so101-calibration-backup-YYYYMMDD-HHMMSS.tar.gz
```

The archive includes a `METADATA.json` with host info, serial symlink snapshots,
LeRobot version if available, and included paths.

## Inspect archive

```bash
python tools/calibration_store.py list calibration_backups/<backup>.tar.gz
```

## Restore safely

Always dry-run first:

```bash
bash scripts/21_restore_calibration.sh calibration_backups/<backup>.tar.gz --dry-run
```

Then restore:

```bash
bash scripts/21_restore_calibration.sh calibration_backups/<backup>.tar.gz
```

Existing files are copied to `calibration_backups/pre_restore/<timestamp>/`
before being overwritten.

## Important rule

After restore, use the same robot/teleop IDs that were used when calibration was
created. If the IDs change, LeRobot may not find the calibration data.
