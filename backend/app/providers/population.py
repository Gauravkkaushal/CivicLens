"""Population (WorldPop) and travel-time catchments (openrouteservice)."""
from __future__ import annotations

import asyncio
import json
import re
import time
from datetime import timedelta

import httpx
import numpy as np

from ..config import get_settings
from .http import Cache, ProviderError, cache_key, client, is_down, mark_down
from .registry import provenance


_JSON_START = re.compile(r'\{\s*"(status|error|taskid)"')


def _json_tail(text: str) -> dict:
    """WorldPop sometimes prefixes its JSON with PHP deprecation notices (HTML). Parse the JSON object at the end."""
    try:
        return json.loads(text)
    except ValueError:
        pass
    dec = json.JSONDecoder()
    for m in _JSON_START.finditer(text):
        try:
            obj, _ = dec.raw_decode(text, m.start())  # tolerate warnings before *and* after the JSON
            return obj
        except ValueError:
            continue
    raise ProviderError("worldpop", f"unparseable response ({len(text)} bytes): {text[:100]!r}")


def _round_ring(ring: list[list[float]]) -> list[list[float]]:
    return [[round(x, 5), round(y, 5)] for x, y in ring]


async def _worldpop_stats(dataset: str, polygon: list[list[list[float]]], cache: Cache | None, ttl_days: int = 60) -> tuple[dict, object, bool]:
    s = get_settings()
    fc = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": [_round_ring(r) for r in polygon]}}]}
    gj = json.dumps(fc, separators=(",", ":"))
    params = {"dataset": dataset, "year": s.worldpop_year, "geojson": gj, "runasync": "true"}
    key = cache_key(f"worldpop:{dataset}", {"year": s.worldpop_year, "g": gj})
    if cache and (hit := await cache.aget(key)):
        return hit[0], hit[1], True
    if is_down("worldpop"):
        raise ProviderError("worldpop", "skipped (timed out recently)")
    try:
        body = None
        for attempt in range(2):
            try:
                r = await client().get(f"{s.worldpop_url}/services/stats", params=params, timeout=httpx.Timeout(40.0, connect=15.0))
                r.raise_for_status()
                body = _json_tail(r.text)
                break
            except httpx.TimeoutException:
                if attempt == 1:
                    raise
                await asyncio.sleep(2)
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:  # asynchronous task: poll until finished
            if body.get("error"):
                raise ProviderError("worldpop", str(body.get("error_message")))
            if body.get("status") == "finished" and body.get("data"):
                break
            tid = body.get("taskid")
            if not tid:
                raise ProviderError("worldpop", f"unexpected response: {str(body)[:200]}")
            await asyncio.sleep(2)
            r = await client().get(f"{s.worldpop_url}/tasks/{tid}", timeout=httpx.Timeout(20.0, connect=10.0))
            r.raise_for_status()
            body = _json_tail(r.text)
        if body.get("status") != "finished":
            raise ProviderError("worldpop", f"{dataset} task did not finish in time")
        data = body["data"]
    except (httpx.HTTPError, KeyError, ValueError, TypeError) as e:
        mark_down("worldpop")
        raise ProviderError("worldpop", f"{dataset} query failed: {type(e).__name__} {e}".strip()) from e
    if cache:
        await cache.aput(key, f"worldpop:{dataset}", data, timedelta(days=ttl_days))
    from datetime import datetime, timezone
    return data, datetime.now(timezone.utc), False


def _in_ring(x: np.ndarray, y: np.ndarray, ring: list[list[float]]) -> np.ndarray:
    """Vectorised even-odd point-in-polygon test; ring is [[lng, lat], ...]."""
    inside = np.zeros(x.shape, bool)
    r = np.asarray(ring, float)
    for (x1, y1), (x2, y2) in zip(r, np.roll(r, -1, axis=0)):
        cross = (y1 > y) != (y2 > y)
        with np.errstate(divide="ignore", invalid="ignore"):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
        inside ^= cross & (x < xi)
    return inside


def grid_population(polygon: list[list[list[float]]], samples: int = 40_000) -> float | None:
    """Population inside the polygon from the bundled WorldPop 1 km grid (zoom-14 tiles), area-weighted by sampling.

    None when the grid is missing or the polygon falls outside it (e.g. not in India)."""
    from ..engine.economics.income import _grid, _tile_xy
    g = _grid()
    if g is None or not polygon or len(polygon[0]) < 3:
        return None
    ring = polygon[0]
    lngs, lats = [p[0] for p in ring], [p[1] for p in ring]
    lng0, lng1, lat0, lat1 = min(lngs), max(lngs), min(lats), max(lats)
    lat_c = (lat0 + lat1) / 2
    w_km, h_km = (lng1 - lng0) * 111.32 * np.cos(np.radians(lat_c)), (lat1 - lat0) * 110.57
    step_km = max(np.sqrt(max(w_km * h_km, 1e-6) / samples), 0.02)
    xs = np.arange(lng0, lng1, step_km / (111.32 * np.cos(np.radians(lat_c)))) if w_km > 0 else np.array([lng0])
    ys = np.arange(lat0, lat1, step_km / 110.57) if h_km > 0 else np.array([lat0])
    X, Y = np.meshgrid(xs, ys)
    X, Y = X.ravel(), Y.ravel()
    m = _in_ring(X, Y, ring)
    X, Y = X[m], Y[m]
    if not len(X):
        return None
    tx, ty = _tile_xy(Y, X, g["zoom"])
    k = tx * (1 << g["zoom"]) + ty
    i = np.clip(np.searchsorted(g["key"], k), 0, len(g["key"]) - 1)
    hit = g["key"][i] == k
    if not hit.any():
        return None
    tile_km = 40075.016 * np.cos(np.radians(Y)) / (1 << g["zoom"])
    density = np.where(hit, g["pop"][i], 0.0) / (tile_km ** 2)  # persons per km² of each sample's tile
    return float(density.sum() * step_km ** 2)


async def worldpop_total(polygon: list[list[list[float]]], cache: Cache | None = None,
                         api_wait_s: float = 4.0) -> tuple[float, dict]:
    """Total modelled population inside a GeoJSON polygon (WorldPop, fixed reference year).

    The live API (100 m data) gets api_wait_s; it is often slow, so past that the bundled 1 km grid answers instead.
    The grid is coarser: small catchments next to denser areas can read high."""
    s = get_settings()
    try:
        data, fetched, cached = await asyncio.wait_for(_worldpop_stats("wpgppop", polygon, cache), api_wait_s)
        total = float(data["total_population"])
    except (ProviderError, asyncio.TimeoutError, KeyError, TypeError, ValueError) as e:
        if isinstance(e, asyncio.TimeoutError):
            mark_down("worldpop")
        local = await asyncio.to_thread(grid_population, polygon)
        if local is None:
            if isinstance(e, ProviderError):
                raise
            raise ProviderError("worldpop", f"population query failed: {type(e).__name__}") from e
        return local, provenance("worldpop", source_updated_at="2020 reference year",
                                 detail="Total population inside the catchment from the bundled WorldPop 1 km grid "
                                        "(live WorldPop API slow or unavailable; coarser for small catchments)")
    return total, provenance("worldpop", retrieved_at=fetched, cached=cached, source_updated_at=f"{s.worldpop_year} reference year",
                             detail="Total population inside the catchment")


def parse_age_sex(data: dict) -> dict:
    """WorldPop wpgpas -> 17 five-year bands (0-4 … 80+) with male/female counts."""
    rows = data.get("agesexpyramid") or []
    bands = []
    for r in sorted(rows, key=lambda x: int(x.get("class", 0))):
        bands.append({"age": str(r.get("age")), "male": float(r.get("male") or 0), "female": float(r.get("female") or 0)})
    if len(bands) == 18:
        # WorldPop splits the first five-year band into infants (0-1) and 1-4: merge them back into 0-4.
        a, b = bands[0], bands[1]
        bands = [{"age": "0 to 5", "male": a["male"] + b["male"], "female": a["female"] + b["female"]}] + bands[2:]
    if len(bands) != 17:
        raise ProviderError("worldpop", f"age-sex pyramid has {len(bands)} bands, expected 17")
    return {"bands": bands}


async def worldpop_age_sex(polygon: list[list[list[float]]], cache: Cache | None = None, wait_s: float = 4.0) -> tuple[dict, dict]:
    s = get_settings()
    try:
        data, fetched, cached = await asyncio.wait_for(_worldpop_stats("wpgpas", polygon, cache), wait_s)
    except asyncio.TimeoutError as e:
        mark_down("worldpop")
        raise ProviderError("worldpop", f"age-sex query: no response within {int(wait_s)} s") from e
    return parse_age_sex(data), provenance("worldpop", retrieved_at=fetched, cached=cached, source_updated_at=f"{s.worldpop_year} reference year",
                                           detail="Age and sex structure inside the catchment (17 five-year bands)")


async def ors_isochrone(lat: float, lng: float, minutes: int, profile: str = "foot-walking", cache: Cache | None = None) -> tuple[list[list[list[float]]], dict]:
    s = get_settings()
    if not s.ors_api_key:
        raise ProviderError("openrouteservice", "ORS_API_KEY not configured")
    if profile not in {"foot-walking", "driving-car", "cycling-regular"}:
        raise ProviderError("openrouteservice", f"unsupported profile {profile}")
    body = {"locations": [[round(lng, 6), round(lat, 6)]], "range": [int(minutes) * 60], "range_type": "time"}
    key = cache_key("ors_iso", {"p": profile, **body})
    if cache and (hit := await cache.aget(key)):
        return hit[0]["polygon"], provenance("openrouteservice", retrieved_at=hit[1], cached=True, detail=f"{minutes} min {profile}")
    try:
        r = await client().post(f"{s.ors_url}/v2/isochrones/{profile}", json=body,
                                headers={"Authorization": s.ors_api_key, "Content-Type": "application/json"})
        r.raise_for_status()
        geom = r.json()["features"][0]["geometry"]
        poly = geom["coordinates"] if geom["type"] == "Polygon" else max(geom["coordinates"], key=lambda p: len(p[0]))
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as e:
        raise ProviderError("openrouteservice", f"isochrone failed: {e}") from e
    if cache:
        await cache.aput(key, "ors_iso", {"polygon": poly}, timedelta(days=30))
    return poly, provenance("openrouteservice", detail=f"{minutes} min {profile} travel-time area")
