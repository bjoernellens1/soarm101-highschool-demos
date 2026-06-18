from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for

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
        selected = request.args.get("rig") or (rigs[0].name if rigs else "rig01")
        rig = get_rig(selected, cfg)
        hf_user = os.environ.get("HF_USER", "local")
        dataset_name = os.environ.get("DATASET_NAME", f"hs-so101-{rig.name}-cube-sort")
        cmds = {
            "calibrate follower": shell_join(build_calibrate_follower(rig)),
            "calibrate leader": shell_join(build_calibrate_leader(rig)),
            "teleop": shell_join(build_teleop(rig, check_cameras=False)),
            "record local": shell_join(build_record(rig, hf_user=hf_user, dataset_name=dataset_name, check_cameras=False)),
        }
        return render_template(
            "index.html",
            rigs=rigs,
            rig=rig,
            selected=selected,
            status=status(),
            hf_user=hf_user,
            dataset_name=dataset_name,
            cmds=cmds,
        )

    @app.post("/start/<action>")
    def start(action: str):
        cfg = app.config["ARMS_CONFIG"]
        rig_name = request.form.get("rig", "rig01")
        rig = get_rig(rig_name, cfg)
        key = f"{rig.name}/{action}"
        if action == "teleop":
            cmd = build_teleop(rig)
        elif action == "calibrate_follower":
            cmd = build_calibrate_follower(rig)
        elif action == "calibrate_leader":
            cmd = build_calibrate_leader(rig)
        elif action == "record":
            cmd = build_record(
                rig,
                hf_user=request.form.get("hf_user") or "local",
                dataset_name=request.form.get("dataset_name") or None,
                episodes=int(request.form.get("episodes") or 5),
                episode_time_s=int(request.form.get("episode_time_s") or 20),
                reset_time_s=int(request.form.get("reset_time_s") or 10),
                push_to_hub=request.form.get("push_to_hub") == "on",
                resume=request.form.get("resume") == "on",
            )
        elif action == "replay":
            repo_id = request.form.get("repo_id") or f"local/hs-so101-{rig.name}-cube-sort"
            episode = int(request.form.get("episode") or 0)
            cmd = build_replay(rig, repo_id, episode)
        else:
            raise ValueError(action)
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
    print(f"Open http://{host}:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
