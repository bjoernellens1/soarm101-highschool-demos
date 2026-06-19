# Optional: Vision Hint / Farberkennung

**Was passiert?** Kamera erkennt grob ein farbiges Objekt und gibt nur einen Hinweis aus.

## Kommandos

```bash
./scripts/detect_color.py --camera 0
./scripts/vision_hint.py --station station_1
```

**Didaktischer Punkt:** Computer Vision zeigen, ohne autonome Greifplanung debuggen zu muessen.

_Voraussetzung: API laeuft (`soarm-api`), `SOARM_API_TOKEN` gesetzt. station_N -> rig0N._
