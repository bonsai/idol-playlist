import json
from pathlib import Path

from django.shortcuts import render

ROOT = Path(__file__).resolve().parents[1]


def dashboard(request):
    path = ROOT / "data" / "youtube" / "playlist.json"
    playlist = {"playlist_title": "地下アイドル｜聞かれる曲 TOP100", "items": []}
    if path.exists():
        playlist = json.loads(path.read_text(encoding="utf-8"))
    return render(request, "catalog/dashboard.html", {"playlist": playlist})
