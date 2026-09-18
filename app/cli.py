import argparse
from app.workflow import run
from app.radio import generate_test_radio

def main():
    p = argparse.ArgumentParser(prog="aw")
    p.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=["collect", "rank", "youtube-match", "playlist", "radio-test", "run"],
    )
    args = p.parse_args()

    if args.command == "radio-test":
        print(generate_test_radio())
        return

    result = run(args.command)
    if args.command == "run":
        result["radio_test"] = generate_test_radio()
    print(result)
