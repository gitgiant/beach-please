# 🐾 Beach, Please — *Low Tide, Good Boy*

A tiny, locally-hosted web app that shows a week of tide charts for **Oceanside, CA**
and highlights the best times to walk the dog (Bart, a black labradoodle 🐩) on the beach.

A day's noon→last-light window is highlighted yellow — and earns a **🐾 Bart approved**
badge — when a **low tide** falls in the afternoon before last light, at or below a
configurable height cutoff.

## Features

- **7-day tide charts** from NOAA CO-OPS predictions (station **9410230 — La Jolla /
  Scripps Pier**, the nearest official prediction station to Oceanside). Datum MLLW, feet.
- **Configurable low-tide cutoff** (default **1 ft**) — only lows at or below it count.
- **Good-walk window** = noon → *last light* (end of civil twilight, sun −6°),
  computed locally for Oceanside's coordinates.
- **Hourly wind & swell** (Open-Meteo) shown for each qualifying low tide — speed,
  direction, gusts, swell height/direction/period — sampled at the low-tide hour.
- No build step, no API keys, no external services beyond NOAA + Open-Meteo.

## Run it

Requires Python 3 (standard library only).

```bash
python3 server.py
# then open http://localhost:8765
```

The server proxies the NOAA and Open-Meteo APIs and serves the single-page UI.
An internet connection is needed to fetch live predictions.

## Files

- `server.py` — stdlib HTTP server + NOAA/Open-Meteo proxy.
- `index.html` — the entire UI (Chart.js via CDN, local sun-time math).

## Notes

Tide predictions are estimates — always check real conditions before heading out.
La Jolla reads slightly lower at low tide than Oceanside Harbor; a subordinate-station
offset could be applied for literal Oceanside Harbor heights.
