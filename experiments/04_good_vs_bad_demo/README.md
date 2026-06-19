# Good Demo vs Bad Demo

**Was passiert?** Eine saubere und eine absichtlich schlechte Demo aufnehmen und vergleichen.

## Kommandos

```bash
./scripts/record_episode.sh station_1 good_demo_01
./scripts/record_episode.sh station_1 bad_demo_01
./scripts/analyze_episode.py local/good_demo_01 local/bad_demo_01
```

**Didaktischer Punkt:** Datenqualitaet ist entscheidend. Schlechte Demos erzeugen schlechte Robotik.

_Voraussetzung: API laeuft (`soarm-api`), `SOARM_API_TOKEN` gesetzt. station_N -> rig0N._
