import pytest
from pydantic import ValidationError

from soarm101_workshop.api.models import RecordParams, ReplayParams


def test_record_defaults():
    p = RecordParams()
    assert p.episodes == 5 and p.resume is False and p.display_data is False


def test_record_bounds():
    with pytest.raises(ValidationError):
        RecordParams(episodes=0)
    with pytest.raises(ValidationError):
        RecordParams(episode_time_s=10_000)


def test_replay_requires_repo_id():
    with pytest.raises(ValidationError):
        ReplayParams()
    assert ReplayParams(repo_id="local/x").episode == 0
