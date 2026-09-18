"""Generate playable radio artifacts from saved talk scripts."""

from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from gtts import gTTS

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "data/programs/test/talk-script-60s.md"
OUTPUT_DIR = ROOT / "data/audio"
OUTPUT = OUTPUT_DIR / "test-60s.mp3"
SEGMENT_DIR = OUTPUT_DIR / "test-60s"


def _script_to_text(path: Path) -> str:
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("##"):
            continue
        line = re.sub(r"[*_]", "", line)
        line = re.sub(r"^[-–—]\s*", "", line)
        if line.startswith("「") and line.endswith("」"):
            line = line[1:-1]
        lines.append(line)
    return "\n".join(lines)


def _ensure_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required to generate 10-second radio segments")


def _split_into_10_second_segments(source: Path) -> None:
    _ensure_ffmpeg()
    SEGMENT_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        padded = Path(tmp) / "padded.mp3"
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(source),
                "-af", "apad=pad_dur=60", "-t", "60",
                "-c:a", "libmp3lame", "-b:a", "128k", str(padded),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for start in range(0, 60, 10):
            output = SEGMENT_DIR / f"{start:02d}-{start + 10:02d}.mp3"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-ss", str(start), "-i", str(padded),
                    "-t", "10", "-c:a", "libmp3lame", "-b:a", "128k",
                    str(output),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )


def generate_test_radio() -> str:
    if not SCRIPT.exists():
        raise FileNotFoundError(f"talk script not found: {SCRIPT}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    text = _script_to_text(SCRIPT)
    gTTS(text=text, lang="ja", slow=False).save(str(OUTPUT))
    _split_into_10_second_segments(OUTPUT)
    return str(OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    print(generate_test_radio())
