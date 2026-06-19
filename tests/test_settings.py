from soarm101_workshop.api.settings import Settings


def test_defaults(monkeypatch):
    monkeypatch.delenv("SOARM_API_TOKEN", raising=False)
    monkeypatch.delenv("SOARM_PORT", raising=False)
    s = Settings(_env_file=None)
    assert s.host == "127.0.0.1"
    assert s.port == 7860
    assert s.config_path == "configs/arms.yaml"
    assert s.allow_localhost_no_auth is False


def test_env_override(monkeypatch):
    monkeypatch.setenv("SOARM_API_TOKEN", "secret")
    monkeypatch.setenv("SOARM_PORT", "9000")
    s = Settings(_env_file=None)
    assert s.token == "secret"
    assert s.port == 9000
