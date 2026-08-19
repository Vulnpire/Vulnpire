#!/usr/bin/env python3
"""Update the local Spotify profile card without exposing credentials."""

from __future__ import annotations

import base64
import html
import json
import os
import pathlib
import urllib.error
import urllib.parse
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "spotify-now-playing.svg"
PROFILE_URL = "https://open.spotify.com/user/31kzny65nrpye2e6hcio4v27ik7e"


def request_json(url: str, *, method: str = "GET", data: bytes | None = None, headers: dict[str, str] | None = None) -> dict:
    request = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"Spotify request failed with HTTP {error.code}") from None
    except urllib.error.URLError:
        raise RuntimeError("Spotify request could not be reached") from None


def required(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def access_token() -> str:
    client_id = required("SPOTIFY_CLIENT_ID")
    client_secret = required("SPOTIFY_CLIENT_SECRET")
    refresh_token = required("SPOTIFY_REFRESH_TOKEN")
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    payload = urllib.parse.urlencode(
        {"grant_type": "refresh_token", "refresh_token": refresh_token}
    ).encode()
    response = request_json(
        "https://accounts.spotify.com/api/token",
        method="POST",
        data=payload,
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    token = response.get("access_token")
    if not isinstance(token, str) or not token:
        raise RuntimeError("Spotify did not return an access token")
    return token


def card(title: str, artist: str, played_at: str, url: str) -> str:
    escape = lambda value: html.escape(value, quote=True)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 150" role="img" aria-labelledby="title desc">
  <title id="title">V Spotify listening panel</title>
  <desc id="desc">The latest published Spotify listening signal.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#071b18"/><stop offset="1" stop-color="#0b1220"/></linearGradient>
    <style>.mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }} .small {{ font-size: 13px; letter-spacing: 1.3px; }} .main {{ font-size: 22px; font-weight: 700; letter-spacing: 1px; }}</style>
  </defs>
  <rect width="1200" height="150" rx="18" fill="url(#bg)"/>
  <rect x="1.5" y="1.5" width="1197" height="147" rx="16.5" fill="none" stroke="#1ed760" stroke-opacity=".7" stroke-width="3"/>
  <circle cx="75" cy="75" r="42" fill="#1ed760"/>
  <path d="M51 61C67 56 84 58 99 65M54 75C68 71 82 72 94 78M58 88C69 85 80 86 89 91" fill="none" stroke="#071b18" stroke-width="6" stroke-linecap="round"/>
  <text x="145" y="45" class="mono small" fill="#1ed760">NOW IN V'S SIGNAL</text>
  <text x="145" y="78" class="mono main" fill="#e5fff0">{escape(title)}</text>
  <text x="145" y="107" class="mono small" fill="#91bca5">{escape(artist)} · played {escape(played_at)}</text>
  <text x="1145" y="83" text-anchor="end" class="mono small" fill="#1ed760">↗ SPOTIFY</text>
  <a href="{escape(url)}"><rect x="1040" y="20" width="125" height="110" fill="transparent"/></a>
</svg>
'''


def main() -> None:
    token = access_token()
    response = request_json(
        "https://api.spotify.com/v1/me/player/recently-played?limit=1",
        headers={"Authorization": f"Bearer {token}"},
    )
    items = response.get("items") or []
    if not items:
        raise RuntimeError("Spotify returned no recently played tracks")
    item = items[0]
    track = item.get("track") or {}
    title = str(track.get("name") or "Unknown track")
    artists = ", ".join(str(artist.get("name") or "Unknown artist") for artist in track.get("artists") or [])
    played_at = str(item.get("played_at") or "recently").replace("T", " ").replace("Z", " UTC")
    track_url = str((track.get("external_urls") or {}).get("spotify") or PROFILE_URL)
    rendered = card(title, artists or "Unknown artist", played_at, track_url)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".svg.tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(OUTPUT)


if __name__ == "__main__":
    main()
