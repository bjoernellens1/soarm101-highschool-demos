# Robot Puppet Mode (Teleop)

**Was passiert?** Leader bewegen, Follower spiegelt live. Drei farbige Punkte anfahren.

## Kommandos

```bash
./scripts/start_teleop.sh station_1
./scripts/stop_all.sh
```

**Didaktischer Punkt:** Teleoperation, Gelenke, Kalibrierung. Arme vorher per /dev/serial/by-id den Stationen zuordnen.

_Voraussetzung: API laeuft (`soarm-api`), `SOARM_API_TOKEN` gesetzt. station_N -> rig0N._
