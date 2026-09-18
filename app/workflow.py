import json
import os
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "music" / "2026" / "candidates.jsonl"


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
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def collect(state: State):
    songs = state.get("songs")
    if songs is None:
        songs = _read_jsonl(CANDIDATES)
    return {"songs": songs}


def should_use_llm(state: State) -> str:
    return "llm" if state.get("llm_enabled", False) else "skip"


def llm_review(state: State):
    # LLM integration point. Keep this branch dependency-free so AW works
    # locally without an API key or model service.
    reviews = []
    for song in state.get("songs", []):
        reviews.append({
            "song_id": song.get("song_id"),
            "status": "pending",
            "reason": "LLM provider not configured",
        })
    return {"llm_review": reviews}


def rank(state: State):
    songs = state.get("songs", [])
    ranked = sorted(
        songs,
        key=lambda x: (
            x.get("score", 0),
            x.get("ask_count", 0),
            x.get("lyrics_view", 0),
            x.get("youtube_view", 0),
        ),
        reverse=True,
    )
    return {"rankings": [{**song, "rank": i + 1} for i, song in enumerate(ranked)]}


def youtube_match(state: State):
    return {
        "youtube": [
            {**song, "youtube_video_id": song.get("youtube_video_id")}
            for song in state.get("rankings", [])
        ]
    }


def playlist(state: State):
    return {"playlist": state.get("youtube", [])}


def build_workflow():
    graph = StateGraph(State)
    graph.add_node("collect", collect)
    graph.add_node("llm_review", llm_review)
    graph.add_node("rank", rank)
    graph.add_node("youtube_match", youtube_match)
    graph.add_node("playlist", playlist)

    graph.add_edge(START, "collect")
    graph.add_conditional_edges(
        "collect",
        should_use_llm,
        {"llm": "llm_review", "skip": "rank"},
    )
    graph.add_edge("llm_review", "rank")
    graph.add_edge("rank", "youtube_match")
    graph.add_edge("youtube_match", "playlist")
    graph.add_edge("playlist", END)
    return graph.compile()


workflow = build_workflow()


def run(command="run", llm_enabled=None):
    if llm_enabled is None:
        llm_enabled = os.getenv("IDOL_PLAYLIST_LLM", "0").lower() in {
            "1", "true", "yes", "on"
        }

    initial: State = {
        "command": command,
        "llm_enabled": llm_enabled,
    }
    return workflow.invoke(initial)
