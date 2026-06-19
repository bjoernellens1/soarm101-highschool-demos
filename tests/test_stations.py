from soarm101_workshop.config import get_rig, list_rigs, resolve_rig_name


def test_station_alias_mapping():
    assert resolve_rig_name("station_1") == "rig01"
    assert resolve_rig_name("station_5") == "rig05"
    assert resolve_rig_name("rig01") == "rig01"
    assert resolve_rig_name("anything") == "anything"


def test_five_stations_configured():
    rigs = list_rigs()
    for n in range(1, 6):
        assert f"rig0{n}" in rigs


def test_get_rig_accepts_station_alias():
    assert get_rig("station_1").name == "rig01"
    assert get_rig("station_1").follower.id == "hs_rig01_follower"
