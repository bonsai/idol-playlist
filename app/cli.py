import argparse
from app.workflow import run

def main():
    p = argparse.ArgumentParser(prog="aw")
    p.add_argument("command", nargs="?", default="run",
                   choices=["collect", "rank", "youtube-match", "playlist", "run"])
    args = p.parse_args()
    print(run(args.command))
