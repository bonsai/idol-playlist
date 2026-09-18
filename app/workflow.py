from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict, total=False):
    command: str
    songs: list[dict]
    rankings: list[dict]
    youtube: list[dict]
    playlist: list[dict]

def collect(state):
    return {"songs": state.get("songs", [])}

def rank(state):
    songs = state.get("songs", [])
    ranked = sorted(songs, key=lambda x: x.get("score", 0), reverse=True)
    return {"rankings": [{**s, "rank": i + 1} for i, s in enumerate(ranked)]}

def youtube_match(state):
    return {"youtube": [{**s, "youtube_video_id": s.get("youtube_video_id")}
                        for s in state.get("rankings", [])]}

def playlist(state):
    return {"playlist": state.get("youtube", [])}

graph = StateGraph(State)
graph.add_node("collect", collect)
graph.add_node("rank", rank)
graph.add_node("youtube_match", youtube_match)
graph.add_node("playlist", playlist)
graph.add_edge(START, "collect")
graph.add_edge("collect", "rank")
graph.add_edge("rank", "youtube_match")
graph.add_edge("youtube_match", "playlist")
graph.add_edge("playlist", END)
workflow = graph.compile()

def run(command="run"):
    return workflow.invoke({"command": command})
