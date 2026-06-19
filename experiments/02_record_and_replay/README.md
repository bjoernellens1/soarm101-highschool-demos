# Record & Replay

**Was passiert?** Kurze Pick-and-Place-Bewegung aufnehmen und exakt wiedergeben.

## Kommandos

```bash
./scripts/record_episode.sh station_1 pick_place_01
./scripts/replay_episode.sh station_1 pick_place_01
```

**Didaktischer Punkt:** Erster Schritt zu Robot Learning: Demonstrationsdaten sammeln.

_Voraussetzung: API laeuft (`soarm-api`), `SOARM_API_TOKEN` gesetzt. station_N -> rig0N._
