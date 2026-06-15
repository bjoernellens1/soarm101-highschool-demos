"""Compatibility imports for LeRobot SO-101 API changes.

LeRobot has changed import paths across versions. These helpers try the current
public paths first, then fall back to older documented paths.
"""
from __future__ import annotations


def import_so101_follower():
    candidates = [
        ("lerobot.robots.so_follower", "SO101FollowerConfig", "SO101Follower"),
        ("lerobot.common.robots.so101_follower", "SO101FollowerConfig", "SO101Follower"),
        ("lerobot.robots.so101_follower", "SO101FollowerConfig", "SO101Follower"),
        ("lerobot.robots.so101_follower.config_so101_follower", "SO101FollowerConfig", None),
    ]
    last_error: Exception | None = None
    for module_name, cfg_name, cls_name in candidates:
        try:
            module = __import__(module_name, fromlist=[cfg_name] + ([cls_name] if cls_name else []))
            cfg = getattr(module, cfg_name)
            if cls_name:
                cls = getattr(module, cls_name)
            else:
                cls_module = __import__(
                    "lerobot.robots.so101_follower.so101_follower", fromlist=["SO101Follower"]
                )
                cls = getattr(cls_module, "SO101Follower")
            return cfg, cls
        except Exception as exc:  # pragma: no cover - depends on installed version
            last_error = exc
    raise ImportError("Could not import SO101Follower from installed LeRobot") from last_error


def import_so101_leader():
    candidates = [
        ("lerobot.teleoperators.so_leader", "SO101LeaderConfig", "SO101Leader"),
        ("lerobot.common.teleoperators.so101_leader", "SO101LeaderConfig", "SO101Leader"),
        ("lerobot.teleoperators.so101_leader", "SO101LeaderConfig", "SO101Leader"),
    ]
    last_error: Exception | None = None
    for module_name, cfg_name, cls_name in candidates:
        try:
            module = __import__(module_name, fromlist=[cfg_name, cls_name])
            return getattr(module, cfg_name), getattr(module, cls_name)
        except Exception as exc:  # pragma: no cover
            last_error = exc
    raise ImportError("Could not import SO101Leader from installed LeRobot") from last_error
