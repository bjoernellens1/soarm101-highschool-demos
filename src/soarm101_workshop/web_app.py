from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, url_for

from .commands import (
    build_calibrate_follower,
    build_calibrate_leader,
    build_record,
    build_replay,
    build_teleop,
    clear_process,
    shell_join,
    start_process,
    status,
    stop_process,
)
from .config import get_rig, list_rigs

VALID_ACTIONS = {"teleop", "calibrate_follower", "calibrate_leader", "record", "replay"}


def _form_int(name: str, default: int, *, lo: int, hi: int) -> int:
    """Parse a bounded int from form input, falling back to default on garbage.

    Without this an empty or non-numeric field raises and Flask returns a 500.
    """
    raw = request.form.get(name)
    if raw is None or raw == "":
        return default
    try:
        return max(lo, min(hi, int(raw)))
    except (TypeError, ValueError):
        return default


def _selected_rig(cfg: str, source: str):
    """Resolve a rig name from the request, returning 400 instead of 500 if unknown."""
    name = (request.values.get("rig") if source == "values" else request.form.get("rig")) or "rig01"
    try:
        return get_rig(name, cfg)
    except KeyError:
        abort(400, f"Unknown rig: {name!r}")


def create_app() -> Flask:
    here = Path(__file__).parent
    app = Flask(
        __name__,
        template_folder=str(here / "web" / "templates"),
        static_folder=str(here / "web" / "static"),
    )
    app.config["ARMS_CONFIG"] = os.environ.get("ARMS_CONFIG", "configs/arms.yaml")

    @app.get("/")
    def index():
        cfg = app.config["ARMS_CONFIG"]
        rigs = [get_rig(name, cfg) for name in list_rigs(cfg)]
        requested = request.args.get("rig")
        names = {r.name for r in rigs}
        selected = requested if requested in names else (rigs[0].name if rigs else "rig01")
        rig = get_rig(selected, cfg)
        hf_user = os.environ.get("HF_USER", "local")
        dataset_name = os.environ.get("DATASET_NAME", f"hs-so101-{rig.name}-cube-sort")
        cmds = {
            "calibrate follower": shell_join(build_calibrate_follower(rig)),
            "calibrate leader": shell_join(build_calibrate_leader(rig)),
            "teleop": shell_join(build_teleop(rig, check_cameras=False)),
            "record local": shell_join(build_record(rig, hf_user=hf_user, dataset_name=dataset_name, check_cameras=False)),
        }
        st = status()
        return render_template(
            "index.html",
            rigs=rigs,
            rig=rig,
            selected=selected,
            status=st,
            any_alive=any(item["alive"] for item in st.values()),
            hf_user=hf_user,
            dataset_name=dataset_name,
            cmds=cmds,
        )

    @app.post("/start/<action>")
    def start(action: str):
        if action not in VALID_ACTIONS:
            abort(400, f"Unknown action: {action}")
        cfg = app.config["ARMS_CONFIG"]
        rig = _selected_rig(cfg, "form")
        display_data = request.form.get("display_data") == "on"
        key = f"{rig.name}/{action}"
        if action == "teleop":
            cmd = build_teleop(rig, display_data=display_data)
        elif action == "calibrate_follower":
            cmd = build_calibrate_follower(rig)
        elif action == "calibrate_leader":
            cmd = build_calibrate_leader(rig)
        elif action == "record":
            cmd = build_record(
                rig,
                hf_user=request.form.get("hf_user") or "local",
                dataset_name=request.form.get("dataset_name") or None,
                episodes=_form_int("episodes", 5, lo=1, hi=20),
                episode_time_s=_form_int("episode_time_s", 20, lo=5, hi=120),
                reset_time_s=_form_int("reset_time_s", 10, lo=3, hi=60),
                push_to_hub=request.form.get("push_to_hub") == "on",
                resume=request.form.get("resume") == "on",
                display_data=display_data,
            )
        else:  # replay
            repo_id = request.form.get("repo_id") or f"local/hs-so101-{rig.name}-cube-sort"
            episode = _form_int("episode", 0, lo=0, hi=10_000)
            cmd = build_replay(rig, repo_id, episode)
        start_process(key, cmd)
        return redirect(url_for("index", rig=rig.name))

    @app.post("/stop")
    def stop():
        key = request.form.get("key", "")
        stop_process(key)
        rig_name = key.split("/", 1)[0] if "/" in key else request.form.get("rig", "rig01")
        return redirect(url_for("index", rig=rig_name))

    @app.post("/stop_all")
    def stop_all():
        for key in list(status().keys()):
            stop_process(key)
        return redirect(url_for("index"))
    @app.post("/clear")
    def clear():
        key = request.form.get("key", "")
        clear_process(key)
        rig_name = key.split("/", 1)[0] if "/" in key else request.form.get("rig", "rig01")
        return redirect(url_for("index", rig=rig_name))

    return app


def main() -> None:
    app = create_app()
    host = os.environ.get("SOARM_WEB_HOST", "127.0.0.1")
    port = int(os.environ.get("SOARM_WEB_PORT", "7860"))
    # This launcher has no authentication and can start/stop real arm motion.
    # It is intended to bind to localhost only. Warn loudly if exposed.
    if host not in ("127.0.0.1", "localhost", "::1"):
        print(
            f"WARNING: binding to {host} exposes unauthenticated robot control on "
            "the network. Use 127.0.0.1 unless you trust every device on the LAN."
        )
    print(f"Open http://{host}:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
