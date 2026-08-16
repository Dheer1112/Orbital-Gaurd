"""TLE loading from CelesTrak or local cache / synthetic data."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import List, Optional
from urllib.request import urlopen, Request

from backend.data.orbital_object import OrbitalObject

# CelesTrak endpoints (no auth required)
CELESTRAK_GP_URL = "https://celestrak.org/NORAD/elements/gp.php"
CACHE_DIR = Path(__file__).resolve().parents[2] / "models" / "tle_cache"


def _ensure_cache_dir() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR


def parse_tle_block(text: str, default_type: str = "UNKNOWN") -> List[OrbitalObject]:
    """Parse classic 3-line or 2-line TLE text into OrbitalObject list."""
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    objects: List[OrbitalObject] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("1 ") and i + 1 < len(lines) and lines[i + 1].startswith("2 "):
            # No name line
            l1, l2 = line, lines[i + 1]
            norad = int(l1[2:7])
            objects.append(
                OrbitalObject(
                    name=f"NORAD-{norad}",
                    norad_id=norad,
                    tle_line1=l1,
                    tle_line2=l2,
                    object_type=default_type,
                )
            )
            i += 2
        elif (
            not line.startswith("1 ")
            and not line.startswith("2 ")
            and i + 2 < len(lines)
            and lines[i + 1].startswith("1 ")
            and lines[i + 2].startswith("2 ")
        ):
            name = line
            l1, l2 = lines[i + 1], lines[i + 2]
            norad = int(l1[2:7])
            objects.append(
                OrbitalObject(
                    name=name,
                    norad_id=norad,
                    tle_line1=l1,
                    tle_line2=l2,
                    object_type=default_type,
                )
            )
            i += 3
        else:
            i += 1
    return objects


def fetch_celestrak_group(group: str = "stations", cache_hours: float = 6.0) -> List[OrbitalObject]:
    """
    Fetch a CelesTrak GP group (e.g. 'stations', 'active', 'debris').
    Caches to disk. Falls back to cache on network error.
    """
    cache_path = _ensure_cache_dir() / f"{group}.tle"
    meta_path = _ensure_cache_dir() / f"{group}.meta.json"

    # Serve from cache if fresh
    if cache_path.exists() and meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
            age_h = (time.time() - meta.get("fetched_at", 0)) / 3600.0
            if age_h < cache_hours:
                return parse_tle_block(cache_path.read_text(), default_type=_guess_type(group))
        except Exception:
            pass

    url = f"{CELESTRAK_GP_URL}?GROUP={group}&FORMAT=tle"
    try:
        req = Request(url, headers={"User-Agent": "SpaceDebrisHackathon/0.1 (research)"})
        with urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8", errors="replace")
        cache_path.write_text(text)
        meta_path.write_text(
            json.dumps({"fetched_at": time.time(), "group": group, "url": url})
        )
        return parse_tle_block(text, default_type=_guess_type(group))
    except Exception as e:
        if cache_path.exists():
            print(f"[tle_loader] Network failed ({e}); using cached {cache_path}")
            return parse_tle_block(cache_path.read_text(), default_type=_guess_type(group))
        raise RuntimeError(f"Could not fetch CelesTrak group '{group}' and no cache: {e}") from e


def load_tle_file(path: str | Path, default_type: str = "UNKNOWN") -> List[OrbitalObject]:
    """Load objects from a local TLE file."""
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    return parse_tle_block(text, default_type=default_type)


def _guess_type(group: str) -> str:
    g = group.lower()
    if "debris" in g:
        return "DEBRIS"
    if "rocket" in g:
        return "ROCKET BODY"
    if g in ("stations", "active", "starlink", "oneweb"):
        return "PAYLOAD"
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Synthetic scenario for reproducible tests / demos
# ---------------------------------------------------------------------------

def make_synthetic_conjunction_pair() -> tuple[OrbitalObject, OrbitalObject]:
    """
    Return a primary + secondary pair based on real ISS-like elements
    with a secondary that is artificially close for demonstration.
    For true determinism we keep real-looking TLEs; the screening
    threshold and short horizon make a conjunction appear in the demo.
    """
    # ISS (approximate recent TLE structure – numbers are illustrative)
    primary = OrbitalObject(
        name="DEMO-SAT-01 (ISS-like)",
        norad_id=25544,
        tle_line1="1 25544U 98067A   24200.50000000  .00016717  00000-0  10270-3 0  9993",
        tle_line2="2 25544  51.6400 247.4627 0006703 130.5360 325.0288 15.50090703 99999",
        object_type="PAYLOAD",
        metadata={"synthetic": True, "role": "primary"},
    )
    # A debris object on a similar inclination / RAAN so they can approach
    secondary = OrbitalObject(
        name="DEMO-DEBRIS-01",
        norad_id=99901,
        tle_line1="1 99901U 98067B   24200.50000000  .00016717  00000-0  10270-3 0  9997",
        tle_line2="2 99901  51.6400 247.4627 0006703 130.5360 325.0288 15.50090703 99991",
        object_type="DEBRIS",
        metadata={"synthetic": True, "role": "secondary"},
    )
    return primary, secondary


def get_demo_objects(
    use_live: bool = False,
    primary_norad: int = 25544,
    max_secondaries: int = 5,
) -> tuple[OrbitalObject, List[OrbitalObject]]:
    """
    Return (primary, list_of_secondaries) for the demo pipeline.
    If use_live=True, try CelesTrak stations + a debris sample.
    Otherwise fall back to synthetic pair.
    """
    if not use_live:
        p, s = make_synthetic_conjunction_pair()
        return p, [s]

    try:
        stations = fetch_celestrak_group("stations", cache_hours=12)
        primary = next((o for o in stations if o.norad_id == primary_norad), stations[0])
        # Small debris sample for speed
        debris = fetch_celestrak_group("cosmos-1408-debris", cache_hours=12)[:max_secondaries]
        if not debris:
            debris = stations[1 : 1 + max_secondaries]
        return primary, debris
    except Exception as e:
        print(f"[tle_loader] Live fetch failed ({e}); using synthetic pair")
        p, s = make_synthetic_conjunction_pair()
        return p, [s]
