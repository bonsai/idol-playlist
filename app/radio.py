"""Generate a single playable radio MP3 from the saved talk script."""

from pathlib import Path
import json
import os
import re
import subprocess
import tempfile
import urllib.request
import wave

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "data/programs/test/talk-script-60s.md"
OUTPUT_DIR = ROOT / "data/audio"
OUTPUT = OUTPUT_DIR / "test-60s.mp3"

TTS_URL = os.environ.get(
    "VOICEVOX_API_URL", "https://api.ai.sakura.ad.jp/v1/audio/speech"
)
TTS_MODEL = os.environ.get("VOICEVOX_MODEL", "zundamon")
TTS_VOICE = os.environ.get("VOICEVOX_VOICE", "normal")
TTS_MAX_CHARS = int(os.environ.get("VOICEVOX_MAX_CHARS", "800"))


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


def _split_text(text: str, max_length: int = TTS_MAX_CHARS) -> list[str]:
    parts = [p for p in re.split(r"(?<=[。！？\n])", text) if p.strip()]
    chunks: list[str] = []
    current = ""
    for part in parts:
        if len(current) + len(part) <= max_length:
            current += part
        else:
            if current:
                chunks.append(current)
            current = part
    if current:
        chunks.append(current)
    return chunks


def _synthesize(text: str) -> bytes:
    api_key = os.environ.get("SAKURA_API_KEY")
    if not api_key:
        raise RuntimeError("SAKURA_API_KEY is not set")
    payload = json.dumps(
        {"model": TTS_MODEL, "input": text, "voice": TTS_VOICE, "response_format": "wav"},
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        TTS_URL,
        data=payload,
        headers={
            "Accept": "audio/wav",
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as res:
        return res.read()


def _concatenate_wav(chunks: list[bytes], output: Path) -> None:
    with wave.open(str(output), "wb") as out_wav:
        for i, data in enumerate(chunks):
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                tf.write(data)
                tmp = tf.name
            try:
                with wave.open(tmp, "rb") as in_wav:
                    if i == 0:
                        out_wav.setparams(in_wav.getparams())
                    out_wav.writeframes(in_wav.readframes(in_wav.getnframes()))
            finally:
                os.remove(tmp)


def generate_test_radio() -> str:
    if not SCRIPT.exists():
        raise FileNotFoundError(f"talk script not found: {SCRIPT}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    wavs = [_synthesize(chunk) for chunk in _split_text(_script_to_text(SCRIPT))]

    with tempfile.TemporaryDirectory() as tmp:
        merged = Path(tmp) / "merged.wav"
        _concatenate_wav(wavs, merged)
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(merged), "-c:a", "libmp3lame", "-b:a", "128k", str(OUTPUT)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return str(OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    print(generate_test_radio())
