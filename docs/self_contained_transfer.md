# Self-contained transfer plan

Goal: one folder can be copied to another workshop PC and brought back online
with minimal guesswork.

## What lives inside this repo

- workshop launcher source code
- shell convenience scripts
- hardware registry: `configs/arms.yaml`
- optional single-rig env: `configs/arms.env`
- task definitions: `configs/tasks.yaml`
- calibration backup archives: `calibration_backups/`
- logs: `logs/`
- printed workspace mat assets

## What does not live inside this repo by default

- the Python virtual environment `.venv/`
- LeRobot cache files, except when backed up as tar.gz
- large recorded datasets
- Hugging Face credentials/tokens

## Transfer to a new PC

```bash
unzip soarm101-highschool-demos.zip
cd soarm101-highschool-demos
bash scripts/10_install_linux_uv.sh
bash scripts/21_restore_calibration.sh calibration_backups/<backup>.tar.gz --dry-run
bash scripts/21_restore_calibration.sh calibration_backups/<backup>.tar.gz
bash scripts/12_snapshot_devices.sh
soarm-workshop rigs
soarm-web
```

## Before every workshop

```bash
bash scripts/12_snapshot_devices.sh > logs/device_snapshot_before_workshop.txt
bash scripts/20_backup_calibration.sh --note "before school workshop"
```

Put the latest backup archive on a USB stick or in a private Nextcloud folder.
