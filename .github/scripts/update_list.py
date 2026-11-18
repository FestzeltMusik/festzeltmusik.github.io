"""Liest die YouTube-Playlist ohne API-Schlüssel und schreibt videos.json.

1. Versuch: yt-dlp (ganze Liste)
2. Versuch: RSS-Feed von YouTube (nur die neuesten ~15)
Wenn beides fehlschlägt, bleibt die alte videos.json unverändert.
"""
import json
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET

PLAYLIST = sys.argv[1]
OUT = "videos.json"


def from_ytdlp():
    r = subprocess.run(
        ["yt-dlp", "--flat-playlist", "-J",
         f"https://www.youtube.com/playlist?list={PLAYLIST}"],
        capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print("yt-dlp Fehler:", r.stderr[-500:])
        return None
    data = json.loads(r.stdout)
    vids = []
    for e in data.get("entries") or []:
        vid, title = e.get("id"), e.get("title")
        if not vid or not title or title in ("[Private video]", "[Deleted video]"):
            continue
        vids.append({"id": vid, "title": title})
    return vids or None


def from_rss():
    url = f"https://www.youtube.com/feeds/videos.xml?playlist_id={PLAYLIST}"
    try:
        with urllib.request.urlopen(url, timeout=30) as f:
            root = ET.fromstring(f.read())
    except Exception as ex:
        print("RSS Fehler:", ex)
        return None
    ns = {"a": "http://www.w3.org/2005/Atom",
          "yt": "http://www.youtube.com/xml/schemas/2015"}
    vids = [{"id": e.find("yt:videoId", ns).text, "title": e.find("a:title", ns).text}
            for e in root.findall("a:entry", ns)]
    return vids or None


vids = from_ytdlp() or from_rss()
if not vids:
    print("Keine Videos gefunden – alte Liste bleibt.")
    sys.exit(0)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(vids, f, ensure_ascii=False, indent=1)
print(f"{len(vids)} Videos gespeichert.")
