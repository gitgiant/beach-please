#!/usr/bin/env python3
"""
Tide Dog — a tiny local web app showing a week of tides for Oceanside, CA.

It serves index.html and proxies the NOAA CO-OPS tide prediction API so the
browser never has to worry about CORS or API quirks.

Run:  python3 server.py
Then open http://localhost:8765
"""

import json
import urllib.request
import urllib.error
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os

PORT = 8765

# NOAA CO-OPS harmonic station. 9410230 = La Jolla (Scripps Pier), the nearest
# official NOAA tide-prediction station to Oceanside, CA.
STATION = "9410230"
STATION_NAME = "La Jolla (Scripps Pier) — NOAA's nearest prediction station to Oceanside"

NOAA = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"

HERE = os.path.dirname(os.path.abspath(__file__))


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "tide-dog/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_marine(lat, lng):
    """Hourly swell (Open-Meteo Marine) + wind (Open-Meteo Forecast), keyed by
    local hour timestamp 'YYYY-MM-DDTHH:00'."""
    tz = "America%2FLos_Angeles"
    marine = fetch_json(
        "https://marine-api.open-meteo.com/v1/marine?"
        f"latitude={lat}&longitude={lng}&timezone={tz}&forecast_days=7"
        "&hourly=swell_wave_height,swell_wave_direction,swell_wave_period"
    )["hourly"]
    wind = fetch_json(
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lng}&timezone={tz}&forecast_days=7&wind_speed_unit=mph"
        "&hourly=wind_speed_10m,wind_direction_10m,wind_gusts_10m"
    )["hourly"]

    out = {}
    for i, t in enumerate(marine["time"]):
        sh_m = marine["swell_wave_height"][i]
        out[t] = {
            "swellHeightFt": round(sh_m * 3.28084, 1) if sh_m is not None else None,
            "swellDir": marine["swell_wave_direction"][i],
            "swellPeriod": marine["swell_wave_period"][i],
        }
    for i, t in enumerate(wind["time"]):
        rec = out.setdefault(t, {})
        rec["windMph"] = wind["wind_speed_10m"][i]
        rec["windDir"] = wind["wind_direction_10m"][i]
        rec["gustMph"] = wind["wind_gusts_10m"][i]
    return out


def noaa_fetch(begin, end, interval):
    """Fetch predictions from NOAA. interval='hilo' for highs/lows, 'h' for hourly curve."""
    params = (
        f"?product=predictions&application=tide-dog"
        f"&begin_date={begin}&end_date={end}"
        f"&datum=MLLW&station={STATION}"
        f"&time_zone=lst_ldt&units=english&interval={interval}&format=json"
    )
    url = NOAA + params
    req = urllib.request.Request(url, headers={"User-Agent": "tide-dog/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("predictions", [])


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # quiet

    def _send(self, code, body, content_type):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
            return

        if self.path.startswith("/api/tides"):
            try:
                today = date.today()
                begin = today.strftime("%Y%m%d")
                end = (today + timedelta(days=6)).strftime("%Y%m%d")
                hilo = noaa_fetch(begin, end, "hilo")
                curve = noaa_fetch(begin, end, "h")
                try:
                    marine = fetch_marine(33.1959, -117.3795)
                except Exception:
                    marine = {}  # tides still work even if marine feed is down
                payload = {
                    "station": STATION,
                    "stationName": STATION_NAME,
                    "lat": 33.1959,
                    "lng": -117.3795,
                    "units": "ft",
                    "datum": "MLLW",
                    "begin": begin,
                    "end": end,
                    "hilo": hilo,
                    "curve": curve,
                    "marine": marine,
                }
                self._send(200, json.dumps(payload).encode("utf-8"),
                           "application/json")
            except urllib.error.URLError as e:
                self._send(502, json.dumps({"error": f"NOAA fetch failed: {e}"}).encode(),
                           "application/json")
            except Exception as e:  # noqa
                self._send(500, json.dumps({"error": str(e)}).encode(),
                           "application/json")
            return

        self._send(404, b"not found", "text/plain")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"🐕  Tide Dog running at  http://localhost:{PORT}")
    print("    (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nbye!")
