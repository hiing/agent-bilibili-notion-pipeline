#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests
from yt_dlp import YoutubeDL

try:
    from opencc import OpenCC
except Exception:  # pragma: no cover
    OpenCC = None

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REPO_ROOT = SKILL_DIR.parent.parent.parent
DATA_DIR = Path(os.getenv("PIPELINE_DATA_DIR", REPO_ROOT / "data"))
DOWNLOAD_DIR = Path(os.getenv("BILI_DOWNLOAD_DIR", DATA_DIR / "downloads" / "bilibili"))
TEMP_DIR = Path(os.getenv("BILI_TEMP_DIR", DATA_DIR / "bili_temp"))
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")
UPLOAD_URL = os.getenv("UPLOAD_URL", "")
UPLOAD_TOKEN = os.getenv("UPLOAD_TOKEN", "")
BILI_COOKIES_FILE = os.getenv("BILI_COOKIES_FILE", "")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "zh")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "auto")

sys.path.insert(0, str(SCRIPT_DIR))
from notion_markdown import markdown_to_blocks  # noqa: E402


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def slug_title(text: str, max_len: int = 120) -> str:
    text = re.sub(r"[\\/:*?\"<>|]+", "_", text).strip()
    return text[:max_len].rstrip(" ._") or "video"


def run(cmd: List[str]) -> None:
    subprocess.run(cmd, check=True)


def extract_bvid(value: str) -> str:
    m = re.search(r"(BV[0-9A-Za-z]+)", value)
    if not m:
        raise ValueError(f"Cannot extract BVID from: {value}")
    return m.group(1)


def flatten_info(info: Dict[str, Any]) -> Dict[str, Any]:
    if info.get("entries"):
        for item in info["entries"]:
            if item:
                return item
    return info


def ydl_common_opts() -> Dict[str, Any]:
    opts: Dict[str, Any] = {
        "merge_output_format": "mp4",
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.bilibili.com/",
        },
        "quiet": False,
        "noplaylist": True,
    }
    if BILI_COOKIES_FILE:
        opts["cookiefile"] = BILI_COOKIES_FILE
    return opts


def fetch_video_info(url: str) -> Dict[str, Any]:
    with YoutubeDL(ydl_common_opts()) as ydl:
        info = flatten_info(ydl.extract_info(url, download=False))
    return info


def download_video(url: str, title: str, bvid: str) -> Path:
    ensure_dir(DOWNLOAD_DIR)
    out_base = DOWNLOAD_DIR / f"{slug_title(title)} - {bvid}.%(ext)s"
    opts = ydl_common_opts()
    opts["outtmpl"] = str(out_base)
    with YoutubeDL(opts) as ydl:
        ydl.download([url])
    expected = DOWNLOAD_DIR / f"{slug_title(title)} - {bvid}.mp4"
    if expected.exists():
        return expected
    candidates = sorted(DOWNLOAD_DIR.glob(f"*{bvid}*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"Downloaded mp4 not found for {bvid}")
    return candidates[0]


def extract_audio(video_path: Path, bvid: str) -> Path:
    ensure_dir(TEMP_DIR)
    wav_path = TEMP_DIR / f"{bvid}.wav"
    run([
        "ffmpeg", "-y", "-i", str(video_path),
        "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", str(wav_path),
    ])
    return wav_path


def normalize_transcript(text: str) -> str:
    text = text.replace("\r", "\n")
    if OpenCC is not None:
        try:
            text = OpenCC("t2s").convert(text)
        except Exception:
            pass
    text = re.sub(r"[ \t]+", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    pieces = re.split(r"(?<=[。！？!?])", text)
    paras: List[str] = []
    current = ""
    for piece in pieces:
        s = piece.strip()
        if not s:
            continue
        if len(current) + len(s) > 220:
            if current:
                paras.append(current)
            current = s
        else:
            current += s
    if current:
        paras.append(current)
    return "\n\n".join(paras)


def transcribe_audio(wav_path: Path, bvid: str) -> Path:
    ensure_dir(TEMP_DIR)
    txt_path = TEMP_DIR / f"{bvid}.txt"

    try:
        from faster_whisper import WhisperModel  # type: ignore

        model = WhisperModel(WHISPER_MODEL, compute_type=WHISPER_COMPUTE_TYPE)
        segments, _info = model.transcribe(str(wav_path), language=WHISPER_LANGUAGE, vad_filter=True)
        text = "".join(seg.text for seg in segments)
    except Exception:
        whisper_bin = shutil.which("whisper")
        if not whisper_bin:
            raise RuntimeError("Neither faster-whisper nor whisper CLI is available")
        run([
            whisper_bin,
            str(wav_path),
            "--model", WHISPER_MODEL,
            "--language", WHISPER_LANGUAGE,
            "--output_dir", str(TEMP_DIR),
            "--output_format", "txt",
        ])
        raw_txt = TEMP_DIR / f"{wav_path.stem}.txt"
        text = raw_txt.read_text(encoding="utf-8")

    txt_path.write_text(normalize_transcript(text), encoding="utf-8")
    return txt_path


def upload_video(video_path: Path) -> Optional[str]:
    if not UPLOAD_URL or not UPLOAD_TOKEN:
        return None
    with video_path.open("rb") as fh:
        resp = requests.post(
            UPLOAD_URL,
            headers={"Authorization": f"Bearer {UPLOAD_TOKEN}"},
            files={"file": (video_path.name, fh, "video/mp4")},
            timeout=120,
        )
    resp.raise_for_status()
    payload = resp.json()
    if isinstance(payload, list) and payload:
        item = payload[0]
        src = item.get("src") or item.get("url")
        if src:
            if src.startswith("http"):
                return src
            base = re.match(r"^(https?://[^/]+)", UPLOAD_URL)
            if base:
                return base.group(1) + src
    if isinstance(payload, dict):
        for key in ("url", "src", "download_url"):
            if payload.get(key):
                return payload[key]
    raise RuntimeError(f"Upload succeeded but no public URL found: {payload}")


def notion_headers() -> Dict[str, str]:
    if not NOTION_API_KEY:
        raise RuntimeError("NOTION_API_KEY is required")
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def rt(text: str) -> List[Dict[str, Any]]:
    return [{"type": "text", "text": {"content": text[:2000]}}]


def page_url(page_id: str) -> str:
    return f"https://www.notion.so/{page_id.replace('-', '')}"


def notion_create_or_update_page(title: str, video_url: str, download_url: Optional[str], page_id: Optional[str]) -> Dict[str, Any]:
    headers = notion_headers()
    props: Dict[str, Any] = {
        "title": {"title": [{"text": {"content": f"{title} - 整理字幕"}}]},
        "URL": {"url": video_url},
    }
    if download_url:
        props["download_url"] = {"url": download_url}

    if page_id:
        resp = requests.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=headers,
            json={"properties": props},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        data.setdefault("url", page_url(page_id))
        return data

    if not NOTION_DATABASE_ID:
        raise RuntimeError("NOTION_DATABASE_ID is required when creating a new page")

    resp = requests.post(
        "https://api.notion.com/v1/pages",
        headers=headers,
        json={"parent": {"database_id": NOTION_DATABASE_ID}, "properties": props},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def notion_list_children(block_id: str) -> List[Dict[str, Any]]:
    headers = notion_headers()
    items: List[Dict[str, Any]] = []
    cursor: Optional[str] = None
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        resp = requests.get(
            f"https://api.notion.com/v1/blocks/{block_id}/children",
            headers=headers,
            params=params,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        items.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return items


def notion_archive_all_children(page_id: str) -> None:
    headers = notion_headers()
    for child in notion_list_children(page_id):
        requests.patch(
            f"https://api.notion.com/v1/blocks/{child['id']}",
            headers=headers,
            json={"archived": True},
            timeout=60,
        ).raise_for_status()


def notion_append_blocks(page_id: str, blocks: List[Dict[str, Any]]) -> None:
    headers = notion_headers()
    for i in range(0, len(blocks), 100):
        chunk = blocks[i:i + 100]
        resp = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=headers,
            json={"children": chunk},
            timeout=60,
        )
        resp.raise_for_status()


def transcript_blocks(video_url: str, download_url: Optional[str], transcript_text: str) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = [
        {"object": "block", "type": "heading_1", "heading_1": {"rich_text": rt("整理字幕")}},
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": rt("说明：基于音频转录自动生成，可能存在少量识别误差。"),
                "icon": {"type": "emoji", "emoji": "📝"},
                "color": "gray_background",
            },
        },
        {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": rt(f"视频链接：{video_url}")}},
    ]
    if download_url:
        blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": rt(f"下载链接：{download_url}")}})
    blocks.append({"object": "block", "type": "heading_2", "heading_2": {"rich_text": rt("正文")}})
    for para in transcript_text.split("\n\n"):
        p = para.strip()
        if not p:
            continue
        blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": rt(p)}})
    return blocks


def save_metadata(payload: Dict[str, Any], bvid: str) -> Path:
    ensure_dir(TEMP_DIR)
    meta_path = TEMP_DIR / f"{bvid}.metadata.json"
    meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return meta_path


def cmd_prepare(args: argparse.Namespace) -> None:
    info = fetch_video_info(args.url)
    title = info.get("title") or args.url
    video_url = info.get("webpage_url") or args.url
    bvid = extract_bvid(video_url if "BV" in video_url else args.url)
    local_file = download_video(args.url, title, bvid)
    wav_path = extract_audio(local_file, bvid)
    transcript_path = transcribe_audio(wav_path, bvid)
    download_url = upload_video(local_file)

    page = notion_create_or_update_page(title, video_url, download_url, args.page_id)
    pid = page["id"]
    if args.replace_children:
        notion_archive_all_children(pid)
    transcript_text = transcript_path.read_text(encoding="utf-8")
    notion_append_blocks(pid, transcript_blocks(video_url, download_url, transcript_text))

    payload = {
        "bvid": bvid,
        "title": title,
        "video_url": video_url,
        "local_file": str(local_file),
        "wav_path": str(wav_path),
        "transcript_path": str(transcript_path),
        "page_id": pid,
        "notion_url": page.get("url") or page_url(pid),
        "download_url": download_url,
    }
    metadata_path = save_metadata(payload, bvid)
    payload["metadata_path"] = str(metadata_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_append_summary(args: argparse.Namespace) -> None:
    page_id = args.page_id
    if args.metadata and not page_id:
        page_id = json.loads(Path(args.metadata).read_text(encoding="utf-8"))["page_id"]
    if not page_id:
        raise RuntimeError("page_id is required")

    if args.markdown_file:
        markdown = Path(args.markdown_file).read_text(encoding="utf-8")
    elif args.text:
        markdown = args.text
    else:
        raise RuntimeError("Provide --markdown-file or --text")

    blocks = markdown_to_blocks(markdown)
    notion_append_blocks(page_id, blocks)
    print(json.dumps({"page_id": page_id, "appended_blocks": len(blocks)}, ensure_ascii=False, indent=2))


def cmd_cleanup(args: argparse.Namespace) -> None:
    meta = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
    deleted: List[str] = []
    kept: List[str] = []

    for key in ("wav_path", "transcript_path"):
        path = Path(meta[key])
        if path.exists():
            path.unlink()
            deleted.append(str(path))

    video_path = Path(meta["local_file"])
    if args.delete_video and video_path.exists():
        video_path.unlink()
        deleted.append(str(video_path))
    elif video_path.exists():
        kept.append(str(video_path))

    kept.extend([meta.get("notion_url", ""), meta.get("download_url", "")])
    print(json.dumps({"deleted": deleted, "kept": [x for x in kept if x]}, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bilibili -> Notion pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prepare", help="download, transcribe, upload, create/update Notion page")
    p.add_argument("--url", required=True, help="Bilibili or b23 URL")
    p.add_argument("--page-id", help="Existing Notion page id")
    p.add_argument("--replace-children", action="store_true", help="Archive existing top-level children before writing transcript")
    p.set_defaults(func=cmd_prepare)

    p = sub.add_parser("append-summary", help="append markdown summary to Notion")
    p.add_argument("--page-id", help="Notion page id")
    p.add_argument("--metadata", help="metadata json from prepare")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--markdown-file", help="Path to markdown file")
    group.add_argument("--text", help="Raw markdown text")
    p.set_defaults(func=cmd_append_summary)

    p = sub.add_parser("cleanup", help="delete temp artifacts")
    p.add_argument("--metadata", required=True, help="metadata json from prepare")
    p.add_argument("--delete-video", action="store_true", help="also delete the local mp4")
    p.set_defaults(func=cmd_cleanup)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
