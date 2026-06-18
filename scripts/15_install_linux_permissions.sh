#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

TARGET_USER="${1:-${SUDO_USER:-${USER:-}}}"
if [ -z "$TARGET_USER" ] || [ "$TARGET_USER" = "root" ]; then
  echo "Usage: sudo bash scripts/15_install_linux_permissions.sh <login-user>" >&2
  exit 2
fi

if [ ! -f 99-so101-workshop.rules ]; then
  echo "Missing 99-so101-workshop.rules. Run bash scripts/14_setup_rig.sh first." >&2
  exit 1
fi

install -m 0644 99-so101-workshop.rules /etc/udev/rules.d/99-so101-workshop.rules
usermod -aG dialout "$TARGET_USER"
udevadm control --reload-rules
udevadm trigger

echo "Installed /etc/udev/rules.d/99-so101-workshop.rules"
echo "Added $TARGET_USER to dialout."
echo "Now unplug/replug both arms, then log out and back in so group membership refreshes."
