import json
import os
from datetime import date
from pathlib import Path
from typing import TypedDict

import django
from langgraph.graph import END, START, StateGraph

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "music" / "2026" / "candidates.jsonl"
RANKINGS_DIR = ROOT / "data" / "rankings"
YOUTUBE_DIR = ROOT / "data" / "youtube"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
django.setup()

from catalog.models import Ranking, Song


class State(TypedDict, total=False):
    command: str
    songs: list[dict]
    rankings: list[dict]
    youtube: list[dict]
    playlist: list[dict]
    llm_enabled: bool
    llm_review: list[dict]


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL: {path}:{line_number}: {exc.msg}") from exc
    return rows


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def collect(state: State):
    return {"songs": state.get("songs") or _read_jsonl(CANDIDATES)}


def should_use_llm(state: State) -> str:
    return "llm" if state.get("llm_enabled", False) else "skip"


def llm_review(state: State):
    return {"llm_review": [{"song_id": s.get("track_id"), "status": "pending", "reason": "LLM provider not configured"} for s in state.get("songs", [])]}


def rank(state: State):
    songs = state.get("songs", [])
    ranked = sorted(songs, key=lambda x: (x.get("score", 0), x.get("ask_count", 0), x.get("lyrics_view", 0), x.get("youtube_view", 0)), reverse=True)
    rankings = [{**song, "rank": i + 1} for i, song in enumerate(ranked)]
    _write_jsonl(RANKINGS_DIR / f"{date.today().isoformat()}.jsonl", rankings)
    return {"rankings": rankings}


def persist(state: State):
    for song in state.get("songs", []):
        Song.objects.update_or_create(
            song_id=song.get("track_id"),
            defaults={
                "song": song.get("title", song.get("song", "")),
                "idol": song.get("artist", song.get("idol", "")),
                "ask_count": song.get("ask_count", 0),
                "lyrics_view": song.get("lyrics_view", 0),
                "youtube_view": song.get("youtube_view", 0),
                "score": song.get("score", 0),
                "youtube_video_id": song.get("youtube_video_id", ""),
            },
        )
    Ranking.objects.all().delete()
    for item in state.get("rankings", []):
        song = Song.objects.get(song_id=item.get("track_id"))
        Ranking.objects.create(song=song, rank=item["rank"], score=item.get("score", 0))
    return {}


def youtube_match(state: State):
    matches = [{**song, "youtube_video_id": song.get("youtube_video_id"), "youtube_match_status": "matched" if song.get("youtube_video_id") else "unmatched"} for song in state.get("rankings", [])]
    _write_json(YOUTUBE_DIR / "playlist.json", {"playlist_title": "地下アイドル｜聞かれる曲 TOP100", "generated_at": date.today().isoformat(), "items": matches})
    return {"youtube": matches}


def playlist(state: State):
    return {"playlist": state.get("youtube", [])}


def build_workflow():
    graph = StateGraph(State)
    for name, fn in [("collect", collect), ("llm_review", llm_review), ("rank", rank), ("persist", persist), ("youtube_match", youtube_match), ("playlist", playlist)]:
        graph.add_node(name, fn)
    graph.add_edge(START, "collect")
    graph.add_conditional_edges("collect", should_use_llm, {"llm": "llm_review", "skip": "rank"})
    graph.add_edge("llm_review", "rank")
    graph.add_edge("rank", "persist")
    graph.add_edge("persist", "youtube_match")
    graph.add_edge("youtube_match", "playlist")
    graph.add_edge("playlist", END)
    return graph.compile()


workflow = build_workflow()


def run(command="run", llm_enabled=None):
    if llm_enabled is None:
        llm_enabled = os.getenv("IDOL_PLAYLIST_LLM", "0").lower() in {"1", "true", "yes", "on"}
    return workflow.invoke({"command": command, "llm_enabled": llm_enabled})
