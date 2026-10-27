"""Render the latest PUBLIC stats.fm stream; no credentials required."""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
USERNAME = "falkorq"


def get_latest():
    request = Request(
        f"https://api.stats.fm/api/v1/users/{USERNAME}/streams/recent?limit=1",
        headers={"Accept": "application/json", "User-Agent": "Falkorq-profile/1.0"},
    )
    with urlopen(request, timeout=25) as response:
        payload = json.load(response)
    streams = payload.get("items") or []
    if not streams:
        raise ValueError("No public recent streams; keeping the previous card.")
    stream = max(streams, key=lambda item: item.get("endTime", ""))
    track = stream["track"]
    return {
        "title": track["name"],
        "artist": ", ".join(artist["name"] for artist in track.get("artists", [])),
        "album": next(iter(track.get("albums", [])), {}).get("name", ""),
    }


def shorten(value, length):
    return value if len(value) <= length else value[: length - 1].rstrip() + "…"


def render(track):
    title = escape(shorten(track["title"], 29))
    artist = escape(shorten(track["artist"], 36))
    album = escape(shorten(track["album"], 45))
    description = escape(f'{track["title"]} by {track["artist"]}. Last played on stats.fm.')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="170" viewBox="0 0 600 170" role="img" aria-labelledby="title desc">
  <title id="title">Last played · {title} — {artist}</title>
  <desc id="desc">{description} Updated periodically, not a live playback indicator.</desc>
  <style>
    :root {{ --surface:#E8EDF6; --disc:#D5E3FF; --ink:#191C20; --muted:#43474E; --primary:#315E97; }}
    @media (prefers-color-scheme:dark) {{ :root {{ --surface:#20262F; --disc:#1B467D; --ink:#DFE2EB; --muted:#C3C6CF; --primary:#A5C8FF; }} }}
    text {{ font-family:Segoe UI,Arial,sans-serif; }}
  </style>
  <defs><clipPath id="copy"><rect x="163" y="50" width="411" height="95"/></clipPath></defs>
  <rect width="600" height="170" rx="28" fill="var(--surface)"/>
  <rect x="22" y="25" width="120" height="120" rx="28" fill="var(--disc)"/>
  <circle cx="82" cy="85" r="39" stroke="var(--primary)" stroke-width="2" fill="none"/>
  <circle cx="82" cy="85" r="27" stroke="var(--primary)" stroke-width="1" opacity=".4" fill="none"/>
  <circle cx="82" cy="85" r="9" fill="var(--primary)"/>
  <text x="168" y="40" fill="var(--primary)" font-size="14">Last played on stats.fm</text>
  <g clip-path="url(#copy)">
  <text x="168" y="78" fill="var(--ink)" font-size="27" font-weight="600">{title}</text>
  <text x="168" y="107" fill="var(--muted)" font-size="21">{artist}</text>
  <text x="168" y="134" fill="var(--muted)" font-size="16">{album}</text>
  </g>
  <path d="M551 27h16v16m0-16-20 20" stroke="var(--primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
</svg>
'''


def main():
    output = ROOT / "assets" / "last-track.svg"
    try:
        content = render(get_latest())
    except Exception as error:
        print(f"Music refresh failed: {type(error).__name__}. Existing card preserved.")
        raise SystemExit(1) from error
    output.parent.mkdir(parents=True, exist_ok=True)
    if not output.exists() or output.read_text(encoding="utf-8") != content:
        temp = output.with_suffix(".tmp")
        temp.write_text(content, encoding="utf-8", newline="\n")
        os.replace(temp, output)
        print("Music card updated.")
    else:
        print("Track unchanged.")


if __name__ == "__main__":
    main()
