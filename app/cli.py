import argparse
from app.workflow import run
from app.radio import generate_test_radio
from app import youtube

YT_COMMANDS = {
    "yt-playlist-create": youtube.playlist_create,
    "yt-playlist-sync": youtube.playlist_sync,
    "yt-short-push": youtube.short_push,
    "yt-push": youtube.push,
}

def main():
    p = argparse.ArgumentParser(prog="aw")
    p.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=[
            "collect", "rank", "youtube-match", "playlist", "radio-test", "run",
            *YT_COMMANDS.keys(),
        ],
    )
    args = p.parse_args()

    if args.command == "radio-test":
        print(generate_test_radio())
        return

    if args.command in YT_COMMANDS:
        print(YT_COMMANDS[args.command]())
        return

    result = run(args.command)
    if args.command == "run":
        result["radio_test"] = generate_test_radio()
    print(result)
