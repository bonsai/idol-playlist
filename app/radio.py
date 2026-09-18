"""Generate playable radio artifacts from saved talk scripts."""

from pathlib import Path
import re

from gtts import gTTS

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "data/programs/test/talk-script-60s.md"
OUTPUT_DIR = ROOT / "data/audio"
OUTPUT = OUTPUT_DIR / "test-60s.mp3"


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


def generate_test_radio() -> str:
    if not SCRIPT.exists():
        raise FileNotFoundError(f"talk script not found: {SCRIPT}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    text = _script_to_text(SCRIPT)
    gTTS(text=text, lang="ja", slow=False).save(str(OUTPUT))
    return str(OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    print(generate_test_radio())
