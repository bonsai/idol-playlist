"""YouTube Data API v3 push: playlist create/sync + Short video upload.

Credential sources (repo に秘密情報を置かない):
- GitHub Actions: YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN env
- Local: ~/secrets/yt-upload/client_secret.json + token.json (reuse yt-upload skill)
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "youtube" / "playlist.json"
PLAYLIST_ID_FILE = ROOT / "data" / "youtube" / "playlist_id.txt"
AUDIO = ROOT / "data" / "audio" / "test-60s.mp3"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

PLAYLIST_TITLE = "地下アイドル｜聞かれる曲 TOP100"
PLAYLIST_DESC = "地下アイドル「聞かれる曲ランキング」上位の公式/適切なYouTube動画を自動収集。idol-playlist が自動生成。"


def _credentials() -> Credentials:
    """Build OAuth2 credentials from env (CI) or local secret files."""
    env_id, env_secret, env_refresh = (
        os.getenv("YT_CLIENT_ID"),
        os.getenv("YT_CLIENT_SECRET"),
        os.getenv("YT_REFRESH_TOKEN"),
    )
    if env_id and env_secret and env_refresh:
        creds = Credentials(
            token=None,
            refresh_token=env_refresh,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=env_id,
            client_secret=env_secret,
            scopes=SCOPES,
        )
    else:
        secret_file = Path.home() / "secrets" / "yt-upload" / "client_secret.json"
        token_file = Path.home() / "secrets" / "yt-upload" / "token.json"
        if not secret_file.exists() or not token_file.exists():
            raise RuntimeError(
                "No YouTube credentials. Set YT_CLIENT_ID/YT_CLIENT_SECRET/YT_REFRESH_TOKEN "
                "or provide ~/secrets/yt-upload/client_secret.json + token.json"
            )
        secret = json.loads(secret_file.read_text(encoding="utf-8"))
        token = json.loads(token_file.read_text(encoding="utf-8"))
        creds = Credentials(
            token=token.get("token"),
            refresh_token=token.get("refresh_token"),
            token_uri=token.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=secret["installed"]["client_id"],
            client_secret=secret["installed"]["client_secret"],
            scopes=token.get("scopes", SCOPES),
        )
    if not creds.valid:
        creds.refresh(Request())
    return creds


def _load_manifest() -> list[str]:
    if not MANIFEST.exists():
        raise FileNotFoundError(f"manifest not found: {MANIFEST} (run: aw run)")
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    video_ids = [
        item["youtube_video_id"]
        for item in payload.get("items", [])
        if item.get("youtube_video_id")
    ]
    # 重複防止: 同一動画を一本だけ追加
    return list(dict.fromkeys(video_ids))


FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/mnt/c/Windows/Fonts/NotoSansJP-VF.ttf",
    "/mnt/c/Windows/Fonts/msgothic.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _japanese_font(size: int) -> ImageFont.FreeTypeFont:
    """日本語を描画できるフォントを環境依存で探す。"""
    for fp in FONT_CANDIDATES:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except OSError:
                continue
    raise RuntimeError(
        "no CJK font found; install fonts-noto-cjk or set YT_JP_FONT"
    )


def _build_thumbnail() -> Path:
    """TOP10 ランキングを 1080x1920 (9:16) の Short サムネ PNG に描画。"""
    if not MANIFEST.exists():
        raise FileNotFoundError(f"manifest not found: {MANIFEST} (run: aw run)")
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    items = sorted(
        [it for it in payload.get("items", []) if it.get("title")],
        key=lambda it: it.get("rank", 999),
    )[:10]

    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), (16, 18, 28))
    draw = ImageDraw.Draw(img)

    # グラデーション背景
    for y in range(H):
        t = y / H
        r = int(16 + (70 - 16) * t)
        g = int(18 + (18 - 18) * t)
        b = int(28 + (58 - 28) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # アクセント帯
    draw.rectangle([0, 0, W, 14], fill=(150, 90, 220))
    draw.rectangle([0, H - 14, W, H], fill=(150, 90, 220))

    title_font = _japanese_font(76)
    sub_font = _japanese_font(52)
    rank_font = _japanese_font(58)
    song_font = _japanese_font(54)
    artist_font = _japanese_font(40)
    foot_font = _japanese_font(40)

    draw.text((60, 70), "地下アイドル", font=title_font, fill=(255, 255, 255))
    draw.text((64, 170), "聞かれる曲 TOP10", font=sub_font, fill=(220, 200, 255))

    y = 340
    for i, it in enumerate(items, start=1):
        draw.text((48, y), f"{i:02d}", font=rank_font, fill=(150, 90, 220))
        title = it["title"]
        artist = it.get("artist", "")
        if draw.textlength(title, font=song_font) > 760:
            while title and draw.textlength(title + "…", font=song_font) > 760:
                title = title[:-1]
            title += "…"
        draw.text((140, y - 4), title, font=song_font, fill=(255, 255, 255))
        if artist:
            draw.text((144, y + 66), artist, font=artist_font, fill=(170, 175, 195))
        y += 152

    draw.text((60, H - 130), "#Shorts｜idol-playlist 自動生成", font=foot_font, fill=(130, 135, 155))

    out = ROOT / "data" / "youtube" / "thumbnail.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def playlist_create() -> dict:
    """新規プレイリスト作成（初回のみ）。ID は playlist_id.txt に保存。"""
    if PLAYLIST_ID_FILE.exists():
        return {"playlist_id": PLAYLIST_ID_FILE.read_text().strip(), "created": False}

    youtube = build("youtube", "v3", credentials=_credentials())
    body = {
        "snippet": {"title": PLAYLIST_TITLE, "description": PLAYLIST_DESC},
        "status": {"privacyStatus": "private"},
    }
    resp = youtube.playlists().insert(part="snippet,status", body=body).execute()

    PLAYLIST_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PLAYLIST_ID_FILE.write_text(resp["id"], encoding="utf-8")
    return {"playlist_id": resp["id"], "url": f"https://www.youtube.com/playlist?list={resp['id']}", "created": True}


def playlist_sync() -> dict:
    """manifest の動画をプレイリストへ差分追加（重複防止）。"""
    playlist_id = PLAYLIST_ID_FILE.read_text().strip() if PLAYLIST_ID_FILE.exists() else None
    if not playlist_id:
        res = playlist_create()
        playlist_id = res["playlist_id"]

    video_ids = _load_manifest()
    youtube = build("youtube", "v3", credentials=_credentials())

    existing: set[str] = set()
    request = youtube.playlistItems().list(
        part="contentDetails", playlistId=playlist_id, maxResults=50
    )
    while request is not None:
        resp = request.execute()
        for item in resp.get("items", []):
            existing.add(item["contentDetails"]["videoId"])
        request = youtube.playlistItems().list_next(request, resp)

    added = []
    for video_id in video_ids:
        if video_id in existing:
            continue
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id},
                }
            },
        ).execute()
        added.append(video_id)

    return {
        "playlist_id": playlist_id,
        "target": len(video_ids),
        "existing": len(existing),
        "added": added,
    }


def _build_short_video(audio: Path, thumbnail: Path | None = None) -> str:
    """60s MP3 + サムネ PNG 背景 → 縦 9:16 Short 動画を一時ファイルに生成。"""
    if not audio.exists():
        raise FileNotFoundError(f"audio not found: {audio} (run: aw radio-test)")
    if not Path("/usr/bin/ffmpeg").exists() and not shutil_which_ffmpeg():
        raise RuntimeError("ffmpeg is required for Short video generation")

    thumb = thumbnail or _build_thumbnail()
    tmp = Path(tempfile.mkdtemp(prefix="yt-short-"))
    out = tmp / "short.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", "30", "-i", str(thumb),
            "-i", str(audio),
            "-shortest",
            "-vf", "scale=1080:1920,format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(out),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return str(out)


def short_push(title: str | None = None) -> dict:
    """60s ラジオ音声を縦 Short 動画としてアップロード（private）。"""
    thumbnail = _build_thumbnail()
    video_path = _build_short_video(AUDIO, thumbnail)
    youtube = build("youtube", "v3", credentials=_credentials())

    body = {
        "snippet": {
            "title": title or "地下アイドル｜聞かれる曲 TOP100 60秒ダイジェスト #Shorts",
            "description": "idol-playlist が自動生成する地下アイドル「聞かれる曲」ランキングの60秒ダイジェスト。#Shorts",
            "tags": ["地下アイドル", "アイドル", "ランキング", "Shorts"],
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": "private",
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()

    video_id = response["id"]

    thumbnail_set = False
    try:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(str(thumbnail)),
        ).execute()
        thumbnail_set = True
    except Exception as exc:  # noqa: BLE001
        thumbnail_set = str(exc)

    return {
        "video_id": video_id,
        "url": f"https://youtu.be/{video_id}",
        "thumbnail": str(thumbnail.relative_to(ROOT)),
        "thumbnail_set": thumbnail_set,
    }


def push() -> dict:
    """yt-push: playlist create(初回) → sync → short push を一気に。"""
    result: dict = {}
    result["playlist_create"] = playlist_create()
    result["playlist_sync"] = playlist_sync()
    result["short_push"] = short_push()
    return result


def shutil_which_ffmpeg() -> bool:
    import shutil
    return shutil.which("ffmpeg") is not None