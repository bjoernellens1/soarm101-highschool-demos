from __future__ import annotations

from pydantic import BaseModel, Field


class TeleopParams(BaseModel):
    display_data: bool = False
    no_cameras: bool = False


class RecordParams(BaseModel):
    hf_user: str = "local"
    dataset_name: str | None = None
    episodes: int = Field(5, ge=1, le=50)
    episode_time_s: int = Field(20, ge=5, le=600)
    reset_time_s: int = Field(10, ge=0, le=120)
    push_to_hub: bool = False
    resume: bool = False
    display_data: bool = False
    no_cameras: bool = False


class ReplayParams(BaseModel):
    repo_id: str
    episode: int = Field(0, ge=0)


class OrchestraParams(BaseModel):
    repo_id: str
    episode: int = Field(0, ge=0)
    stations: list[str] | None = None  # default: all configured rigs


class ArmInfo(BaseModel):
    role: str
    type: str
    id: str
    port: str


class RigInfo(BaseModel):
    name: str
    label: str
    task_text: str
    follower: ArmInfo
    leader: ArmInfo
    cameras: dict


class ProcessStatus(BaseModel):
    key: str
    alive: bool
    returncode: int | None
    started_at: float
    cmd: str
    log: str = ""


class ActionResult(BaseModel):
    key: str
    pid: int
    cmd: str


class HealthInfo(BaseModel):
    status: str = "ok"
    version: str


class PortInfo(BaseModel):
    devices: list[str]
