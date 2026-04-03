#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

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
VIDEO_COOKIES_FILE = os.getenv("VIDEO_COOKIES_FILE", os.getenv("BILI_COOKIES_FILE", ""))
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "zh")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "auto")
ASR_SEGMENT_SECONDS = int(os.getenv("ASR_SEGMENT_SECONDS", "600"))
ASR_AUTO_SEGMENT_MINUTES = int(os.getenv("ASR_AUTO_SEGMENT_MINUTES", "20"))

sys.path.insert(0, str(SCRIPT_DIR))
from notion_markdown import markdown_to_blocks  # noqa: E402


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class PipelineError(Exception):
    code: str
    stage: str
    message: str
    retryable: bool = False
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "code": self.code,
            "stage": self.stage,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.details:
            payload["details"] = self.details
        return payload

    def __str__(self) -> str:
        return f"[{self.stage}:{self.code}] {self.message}"


def progress(message: str) -> None:
    print(f"[pipeline] {message}", file=sys.stderr, flush=True)


def slug_title(text: str, max_len: int = 120) -> str:
    text = re.sub(r"[\\/:*?\"<>|]+", "_", text).strip()
    return text[:max_len].rstrip(" ._") or "video"


def run(cmd: List[str], stage: str = "command") -> None:
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise PipelineError(
            code=f"{stage.upper()}_FAILED",
            stage=stage,
            message=f"Command failed: {' '.join(cmd)}",
            retryable=False,
            details={"returncode": e.returncode},
        ) from e


def extract_bvid(value: str, info: Optional[Dict[str, Any]] = None) -> str:
    m = re.search(r"(BV[0-9A-Za-z]+)", value)
    if m:
        return m.group(1)
    if info:
        for key in ("id", "display_id"):
            raw = info.get(key)
            if raw:
                return slug_title(str(raw), 80)
    m = re.search(r"(?:v=|/)([A-Za-z0-9_-]{6,})", value)
    if m:
        return slug_title(m.group(1), 80)
    return slug_title(value, 80)


def detect_platform(url: str, info: Optional[Dict[str, Any]] = None) -> str:
    extractor = str((info or {}).get("extractor_key") or "").lower()
    if "bili" in extractor:
        return "bilibili"
    if "youtube" in extractor:
        return "youtube"

    host = urlparse(url).netloc.lower()
    if "bilibili.com" in host or host.endswith("b23.tv"):
        return "bilibili"
    if "youtube.com" in host or host.endswith("youtu.be"):
        return "youtube"
    if "vimeo.com" in host:
        return "vimeo"
    if "twitch.tv" in host:
        return "twitch"
    if "douyin.com" in host or "iesdouyin.com" in host:
        return "douyin"
    return "generic"


def flatten_info(info: Dict[str, Any]) -> Dict[str, Any]:
    if info.get("entries"):
        for item in info["entries"]:
            if item:
                return item
    return info


def ydl_common_opts(url: Optional[str] = None) -> Dict[str, Any]:
    headers: Dict[str, str] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
    }
    if url and detect_platform(url) == "bilibili":
        headers["Referer"] = "https://www.bilibili.com/"

    opts: Dict[str, Any] = {
        "merge_output_format": "mp4",
        "http_headers": headers,
        "quiet": False,
        "noplaylist": True,
    }
    if VIDEO_COOKIES_FILE:
        opts["cookiefile"] = VIDEO_COOKIES_FILE
    return opts


def fetch_video_info(url: str) -> Dict[str, Any]:
    with YoutubeDL(ydl_common_opts(url)) as ydl:
        info = flatten_info(ydl.extract_info(url, download=False))
    return info


def download_video(url: str, title: str, bvid: str) -> Path:
    ensure_dir(DOWNLOAD_DIR)
    out_base = DOWNLOAD_DIR / f"{slug_title(title)} - {bvid}.%(ext)s"
    opts = ydl_common_opts(url)
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
    ], stage="extract_audio")
    return wav_path


def audio_duration_seconds(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip() or 0)


def split_audio_segments(wav_path: Path, bvid: str, segment_seconds: int) -> List[Path]:
    ensure_dir(TEMP_DIR)
    segment_pattern = TEMP_DIR / f"{bvid}_seg_%03d.wav"
    run([
        "ffmpeg", "-y", "-i", str(wav_path),
        "-f", "segment", "-segment_time", str(segment_seconds),
        "-c", "copy", str(segment_pattern),
    ], stage="split_audio")
    return sorted(TEMP_DIR.glob(f"{bvid}_seg_*.wav"))


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
    duration = audio_duration_seconds(wav_path)
    use_segments = duration >= ASR_AUTO_SEGMENT_MINUTES * 60

    if use_segments:
        progress(f"长音频检测：{duration/60:.1f} 分钟，启用分段转写")
        segment_paths = split_audio_segments(wav_path, bvid, ASR_SEGMENT_SECONDS)
    else:
        segment_paths = [wav_path]

    text_parts: List[str] = []

    try:
        from faster_whisper import WhisperModel  # type: ignore

        model = WhisperModel(WHISPER_MODEL, compute_type=WHISPER_COMPUTE_TYPE)
        for seg_path in segment_paths:
            segments, _info = model.transcribe(str(seg_path), language=WHISPER_LANGUAGE, vad_filter=True)
            text_parts.append("".join(seg.text for seg in segments))
    except Exception:
        whisper_bin = shutil.which("whisper")
        if not whisper_bin:
            raise RuntimeError("Neither faster-whisper nor whisper CLI is available")
        for seg_path in segment_paths:
            run([
                whisper_bin,
                str(seg_path),
                "--model", WHISPER_MODEL,
                "--language", WHISPER_LANGUAGE,
                "--output_dir", str(TEMP_DIR),
                "--output_format", "txt",
            ], stage="transcribe")
            raw_txt = TEMP_DIR / f"{seg_path.stem}.txt"
            text_parts.append(raw_txt.read_text(encoding="utf-8"))

    text = "\n".join(text_parts)
    txt_path.write_text(normalize_transcript(text), encoding="utf-8")

    if use_segments:
        for seg_path in segment_paths:
            try:
                seg_path.unlink(missing_ok=True)
            except Exception:
                pass
            seg_txt = TEMP_DIR / f"{seg_path.stem}.txt"
            if seg_txt.exists():
                seg_txt.unlink()

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
    parts: List[Dict[str, Any]] = []
    remaining = text
    while remaining:
        chunk = remaining[:1900]
        parts.append({"type": "text", "text": {"content": chunk}})
        remaining = remaining[1900:]
    return parts or [{"type": "text", "text": {"content": ""}}]


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


def metadata_path_for_bvid(bvid: str) -> Path:
    ensure_dir(TEMP_DIR)
    return TEMP_DIR / f"{bvid}.metadata.json"


def save_metadata(payload: Dict[str, Any], bvid: str, meta_path: Optional[Path] = None) -> Path:
    target = meta_path or metadata_path_for_bvid(bvid)
    payload.setdefault("schema_version", 1)
    payload.setdefault("created_at", now_iso())
    payload["updated_at"] = now_iso()
    payload["metadata_path"] = str(target)
    write_json(target, payload)
    return target


def rich_text_plain(items: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for item in items or []:
        if item.get("plain_text"):
            parts.append(item["plain_text"])
        elif item.get("text", {}).get("content"):
            parts.append(item["text"]["content"])
    return "".join(parts)


def block_plain_text(block: Dict[str, Any]) -> str:
    block_type = block.get("type")
    payload = block.get(block_type or "", {})
    if isinstance(payload, dict) and payload.get("rich_text"):
        return rich_text_plain(payload.get("rich_text", []))
    return ""


def verify_page(page_id: str, require_summary: bool = False) -> Dict[str, Any]:
    children = notion_list_children(page_id)
    texts = [block_plain_text(block).strip() for block in children]
    headings = [
        text for block, text in zip(children, texts)
        if block.get("type") in {"heading_1", "heading_2", "heading_3"} and text
    ]

    def has_any(keywords: List[str]) -> bool:
        return any(any(keyword in text for keyword in keywords) for text in texts)

    report = {
        "page_id": page_id,
        "block_count": len(children),
        "paragraph_count": sum(1 for block in children if block.get("type") == "paragraph"),
        "headings": headings,
        "has_title_heading": has_any(["整理字幕"]),
        "has_body_heading": has_any(["正文"]),
        "has_structure_section": has_any(["结构梳理", "文章结构整理", "精要观点"]),
        "has_core_section": has_any(["核心观点"]),
        "has_concepts_section": has_any(["关键概念", "概念速查"]),
    }
    report["has_summary_section"] = any([
        report["has_structure_section"],
        report["has_core_section"],
        report["has_concepts_section"],
    ])
    report["ok"] = (
        report["has_title_heading"]
        and report["has_body_heading"]
        and report["paragraph_count"] > 0
        and (not require_summary or report["has_summary_section"])
    )
    return report


def load_metadata(path: Path) -> Dict[str, Any]:
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta.setdefault("schema_version", 1)
    return meta


def existing_path(meta: Dict[str, Any], key: str) -> Optional[Path]:
    value = meta.get(key)
    if not value:
        return None
    path = Path(value)
    return path if path.exists() else None


def state_report(meta: Dict[str, Any]) -> Dict[str, Any]:
    local_file_exists = bool(existing_path(meta, "local_file"))
    wav_exists = bool(existing_path(meta, "wav_path"))
    transcript_exists = bool(existing_path(meta, "transcript_path"))
    has_summary = bool(meta.get("summary_appended_blocks"))
    verification = meta.get("verification")
    cleanup = meta.get("cleanup")

    content_id = meta.get("content_id") or meta.get("bvid")

    if not content_id:
        next_action = "resolve_info"
    elif not local_file_exists:
        next_action = "download_video"
    elif not wav_exists and not transcript_exists:
        next_action = "extract_audio"
    elif not transcript_exists:
        next_action = "transcribe_audio"
    elif not meta.get("download_url"):
        next_action = "upload_video"
    elif not meta.get("page_id"):
        next_action = "create_or_update_notion_page"
    elif not meta.get("written_transcript_blocks"):
        next_action = "write_transcript_blocks"
    elif not has_summary:
        next_action = "append_summary_optional"
    elif not verification:
        next_action = "verify_page"
    elif cleanup is None:
        next_action = "cleanup_optional"
    elif verification and verification.get("ok"):
        next_action = "done"
    else:
        next_action = "inspect_verification_failure"

    return {
        "state": meta.get("state"),
        "platform": meta.get("platform"),
        "content_id": content_id,
        "bvid": meta.get("bvid"),
        "title": meta.get("title"),
        "page_id": meta.get("page_id"),
        "notion_url": meta.get("notion_url"),
        "download_url": meta.get("download_url"),
        "local_file_exists": local_file_exists,
        "wav_exists": wav_exists,
        "transcript_exists": transcript_exists,
        "has_summary": has_summary,
        "verification": verification,
        "cleanup": cleanup,
        "resume_ready": bool(meta.get("source_url") or meta.get("video_url")),
        "next_action": next_action,
        "metadata_path": meta.get("metadata_path"),
    }


def set_stage(meta: Dict[str, Any], state: str, last_success_stage: str) -> None:
    meta["state"] = state
    meta["last_success_stage"] = last_success_stage
    meta["last_error_code"] = None


def record_error(meta: Dict[str, Any], error: PipelineError) -> None:
    meta["last_error_code"] = error.code
    meta["last_error_stage"] = error.stage
    meta["last_error_message"] = error.message


def preflight_page_check(page_id: str, expected_url: Optional[str], dry_run: bool = False) -> Dict[str, Any]:
    headers = notion_headers()
    resp = requests.get(f"https://api.notion.com/v1/pages/{page_id}", headers=headers, timeout=60)
    resp.raise_for_status()
    page = resp.json()
    props = page.get("properties", {})
    actual_url = None
    if isinstance(props.get("URL"), dict):
        actual_url = props.get("URL", {}).get("url")
    report = {
        "page_id": page_id,
        "actual_url": actual_url,
        "expected_url": expected_url,
        "ok": True,
        "warnings": [],
    }
    if expected_url and actual_url and actual_url != expected_url:
        report["ok"] = False
        report["warnings"].append("URL mismatch between target page and current source url")
    if dry_run:
        report["mode"] = "dry-run"
    return report


def append_summary_to_notion(page_id: str, markdown: str, dry_run: bool = False) -> Dict[str, Any]:
    progress("追加 Markdown 总结到 Notion")
    blocks = markdown_to_blocks(markdown)
    if dry_run:
        return {"page_id": page_id, "appended_blocks": len(blocks), "mode": "dry-run"}
    notion_append_blocks(page_id, blocks)
    return {"page_id": page_id, "appended_blocks": len(blocks)}


def cleanup_from_meta(meta: Dict[str, Any], mode: str = "temp") -> Dict[str, Any]:
    deleted: List[str] = []
    kept: List[str] = []

    for key in ("wav_path", "transcript_path"):
        path_value = meta.get(key)
        if not path_value:
            continue
        path = Path(path_value)
        if mode in {"temp", "all"} and path.exists():
            path.unlink()
            deleted.append(str(path))
        elif path.exists():
            kept.append(str(path))

    video_value = meta.get("local_file")
    if video_value:
        video_path = Path(video_value)
        if mode == "all" and video_path.exists():
            video_path.unlink()
            deleted.append(str(video_path))
        elif video_path.exists():
            kept.append(str(video_path))

    for key in ("metadata_path", "notion_url", "download_url"):
        value = meta.get(key)
        if value:
            kept.append(str(value))

    return {"mode": mode, "deleted": deleted, "kept": kept}


def prepare_pipeline(
    url: str,
    page_id: Optional[str],
    replace_children: bool,
    meta_path: Optional[Path] = None,
    existing: Optional[Dict[str, Any]] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    meta: Dict[str, Any] = dict(existing or {})
    meta["source_url"] = url
    meta["replace_children"] = replace_children
    if page_id:
        meta["requested_page_id"] = page_id

    if not (meta.get("content_id") or meta.get("bvid")) or not meta.get("title") or not meta.get("video_url"):
        progress("解析视频信息")
        info = fetch_video_info(url)
        title = info.get("title") or url
        video_url = info.get("webpage_url") or url
        bvid = extract_bvid(video_url if "BV" in video_url else url, info)
        platform = detect_platform(video_url or url, info)
        meta.update({
            "platform": platform,
            "content_id": bvid,
            "bvid": bvid if str(bvid).startswith("BV") else meta.get("bvid"),
            "title": title,
            "video_url": video_url,
        })
        set_stage(meta, "info_resolved", "resolve")
        meta_path = save_metadata(meta, bvid, meta_path)
    else:
        bvid = meta.get("content_id") or meta["bvid"]
        title = meta["title"]
        video_url = meta["video_url"]
        meta_path = meta_path or Path(meta["metadata_path"]) if meta.get("metadata_path") else metadata_path_for_bvid(bvid)
        meta["metadata_path"] = str(meta_path)

    local_file = existing_path(meta, "local_file")
    if not local_file:
        progress("下载视频")
        local_file = download_video(url, title, bvid)
        meta.update({"local_file": str(local_file)})
        set_stage(meta, "downloaded", "download")
        save_metadata(meta, bvid, meta_path)

    wav_path = existing_path(meta, "wav_path")
    if not wav_path:
        progress("抽取音频")
        wav_path = extract_audio(local_file, bvid)
        meta.update({"wav_path": str(wav_path)})
        set_stage(meta, "audio_extracted", "extract_audio")
        save_metadata(meta, bvid, meta_path)

    transcript_path = existing_path(meta, "transcript_path")
    if not transcript_path:
        progress("转写音频")
        transcript_path = transcribe_audio(wav_path, bvid)
        meta.update({"transcript_path": str(transcript_path)})
        set_stage(meta, "transcribed", "transcribe")
        save_metadata(meta, bvid, meta_path)

    if not meta.get("download_url"):
        progress("上传视频")
        meta["download_url"] = upload_video(local_file)
        set_stage(meta, "uploaded", "upload")
        save_metadata(meta, bvid, meta_path)

    target_page_id = page_id or meta.get("page_id")
    if target_page_id:
        meta["preflight"] = preflight_page_check(target_page_id, expected_url=video_url, dry_run=dry_run)
        if not meta["preflight"].get("ok"):
            raise PipelineError(
                code="NOTION_PAGE_PREFLIGHT_FAILED",
                stage="notion_write",
                message="Target Notion page failed preflight checks",
                retryable=False,
                details=meta["preflight"],
            )
        if dry_run:
            save_metadata(meta, bvid, meta_path)
            return load_metadata(meta_path)

    if not meta.get("page_id"):
        progress("创建或更新 Notion 页面")
        if dry_run:
            meta.update({
                "state": "page_ready",
                "requested_page_id": target_page_id,
                "dry_run": True,
            })
            save_metadata(meta, bvid, meta_path)
            return load_metadata(meta_path)
        page = notion_create_or_update_page(title, video_url, meta.get("download_url"), target_page_id)
        meta.update({
            "page_id": page["id"],
            "notion_url": page.get("url") or page_url(page["id"]),
        })
        set_stage(meta, "page_ready", "notion_page")
        save_metadata(meta, bvid, meta_path)
    else:
        target_page_id = meta["page_id"]

    if replace_children and not meta.get("children_archived"):
        progress("归档旧页面 children")
        notion_archive_all_children(target_page_id)
        meta.update({"children_archived": True})
        set_stage(meta, "children_archived", "notion_archive")
        save_metadata(meta, bvid, meta_path)

    if not meta.get("written_transcript_blocks"):
        progress("写入字幕正文 blocks")
        transcript_text = transcript_path.read_text(encoding="utf-8")
        blocks = transcript_blocks(video_url, meta.get("download_url"), transcript_text)
        if dry_run:
            meta.update({"dry_run": True, "planned_transcript_blocks": len(blocks)})
            save_metadata(meta, bvid, meta_path)
            return load_metadata(meta_path)
        notion_append_blocks(target_page_id, blocks)
        meta.update({"written_transcript_blocks": len(blocks)})
        set_stage(meta, "prepared", "write_transcript_blocks")
        save_metadata(meta, bvid, meta_path)

    return load_metadata(meta_path)


def resolve_page_id(page_id: Optional[str], metadata: Optional[str]) -> str:
    if page_id:
        return page_id
    if metadata:
        return load_metadata(Path(metadata))["page_id"]
    raise RuntimeError("page_id is required")


def maybe_append_summary(meta: Dict[str, Any], markdown: Optional[str], dry_run: bool = False) -> Dict[str, Any]:
    if not markdown:
        return meta
    if meta.get("summary_appended_blocks"):
        return meta
    result = append_summary_to_notion(meta["page_id"], markdown, dry_run=dry_run)
    meta["summary"] = result
    meta["summary_appended_blocks"] = result["appended_blocks"]
    if not dry_run:
        set_stage(meta, "summary_appended", "append_summary")
    else:
        meta["dry_run"] = True
    save_metadata(meta, meta.get("content_id") or meta.get("bvid", "metadata"), Path(meta["metadata_path"]))
    return meta


def finalize_pipeline(meta: Dict[str, Any], require_summary: bool, cleanup_mode: str) -> Dict[str, Any]:
    progress("回读校验 Notion 页面")
    verification = verify_page(meta["page_id"], require_summary=require_summary)
    meta["verification"] = verification

    if cleanup_mode != "none":
        progress(f"清理本地文件 ({cleanup_mode})")
        meta["cleanup"] = cleanup_from_meta(meta, cleanup_mode)

    if verification["ok"]:
        set_stage(meta, "completed", "verify")
    else:
        meta["state"] = "verification_failed"
        meta["last_error_code"] = "VERIFY_FAILED"
    save_metadata(meta, meta["bvid"], Path(meta["metadata_path"]))
    return meta


def cmd_prepare(args: argparse.Namespace) -> None:
    payload = prepare_pipeline(args.url, args.page_id, args.replace_children, dry_run=args.dry_run)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_append_summary(args: argparse.Namespace) -> None:
    page_id = resolve_page_id(args.page_id, args.metadata)
    if args.markdown_file:
        markdown = Path(args.markdown_file).read_text(encoding="utf-8")
    elif args.text:
        markdown = args.text
    else:
        raise RuntimeError("Provide --markdown-file or --text")
    result = append_summary_to_notion(page_id, markdown, dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_verify(args: argparse.Namespace) -> None:
    page_id = resolve_page_id(args.page_id, args.metadata)
    report = verify_page(page_id, require_summary=args.require_summary)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(2)


def cmd_cleanup(args: argparse.Namespace) -> None:
    meta = load_metadata(Path(args.metadata))
    mode = "all" if args.delete_video else args.mode
    result = cleanup_from_meta(meta, mode)
    meta["cleanup"] = result
    meta["state"] = "cleaned" if mode != "none" else meta.get("state", "prepared")
    save_metadata(meta, meta.get("content_id") or meta.get("bvid", "metadata"), Path(meta["metadata_path"]))
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_state(args: argparse.Namespace) -> None:
    meta = load_metadata(Path(args.metadata))
    print(json.dumps(state_report(meta), ensure_ascii=False, indent=2))


def cmd_resume(args: argparse.Namespace) -> None:
    meta_path = Path(args.metadata)
    existing = load_metadata(meta_path)
    source_url = existing.get("source_url") or existing.get("video_url")
    if not source_url:
        raise RuntimeError("Metadata is missing source_url/video_url; cannot resume")
    meta = prepare_pipeline(
        source_url,
        args.page_id or existing.get("requested_page_id") or existing.get("page_id"),
        args.replace_children or bool(existing.get("replace_children")),
        meta_path=meta_path,
        existing=existing,
        dry_run=args.dry_run,
    )

    summary_markdown: Optional[str] = None
    if args.markdown_file:
        summary_markdown = Path(args.markdown_file).read_text(encoding="utf-8")
    elif args.text:
        summary_markdown = args.text
    meta = maybe_append_summary(meta, summary_markdown, dry_run=args.dry_run)
    if args.dry_run:
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        return
    meta = finalize_pipeline(meta, require_summary=bool(summary_markdown) or args.require_summary, cleanup_mode=args.cleanup_mode)
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    if not meta["verification"]["ok"]:
        raise SystemExit(2)


def cmd_run(args: argparse.Namespace) -> None:
    meta = prepare_pipeline(args.url, args.page_id, args.replace_children, dry_run=args.dry_run)

    summary_markdown: Optional[str] = None
    if args.markdown_file:
        summary_markdown = Path(args.markdown_file).read_text(encoding="utf-8")
    elif args.text:
        summary_markdown = args.text

    meta = maybe_append_summary(meta, summary_markdown, dry_run=args.dry_run)
    if args.dry_run:
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        return
    meta = finalize_pipeline(meta, require_summary=bool(summary_markdown) or args.require_summary, cleanup_mode=args.cleanup_mode)
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    if not meta["verification"]["ok"]:
        raise SystemExit(2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Video -> Notion pipeline (Bilibili-first, yt-dlp-backed)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prepare", help="download, transcribe, upload, create/update Notion page")
    p.add_argument("--url", required=True, help="Video URL (Bilibili/b23 primary; also usable with YouTube and other yt-dlp-supported sites)")
    p.add_argument("--page-id", help="Existing Notion page id")
    p.add_argument("--replace-children", action="store_true", help="Archive existing top-level children before writing transcript")
    p.add_argument("--dry-run", action="store_true", help="Preview actions and preflight checks without writing to Notion")
    p.set_defaults(func=cmd_prepare)

    p = sub.add_parser("append-summary", help="append markdown summary to Notion")
    p.add_argument("--page-id", help="Notion page id")
    p.add_argument("--metadata", help="metadata json from prepare")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--markdown-file", help="Path to markdown file")
    group.add_argument("--text", help="Raw markdown text")
    p.add_argument("--dry-run", action="store_true", help="Preview summary append without writing")
    p.set_defaults(func=cmd_append_summary)

    p = sub.add_parser("verify", help="read back and verify Notion page structure")
    p.add_argument("--page-id", help="Notion page id")
    p.add_argument("--metadata", help="metadata json from prepare/run")
    p.add_argument("--require-summary", action="store_true", help="Require summary-related sections to be present")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("cleanup", help="delete temp artifacts")
    p.add_argument("--metadata", required=True, help="metadata json from prepare/run")
    p.add_argument("--mode", choices=["none", "temp", "all"], default="temp", help="Cleanup mode: temp=delete wav/txt, all=also delete video")
    p.add_argument("--delete-video", action="store_true", help="Backward-compatible alias for --mode all")
    p.set_defaults(func=cmd_cleanup)

    p = sub.add_parser("state", help="show saved pipeline state from metadata")
    p.add_argument("--metadata", required=True, help="metadata json from prepare/run")
    p.set_defaults(func=cmd_state)

    p = sub.add_parser("resume", help="resume from metadata, then optional summary/verify/cleanup")
    p.add_argument("--metadata", required=True, help="metadata json from prepare/run")
    p.add_argument("--page-id", help="Optional override Notion page id")
    p.add_argument("--replace-children", action="store_true", help="Archive existing top-level children before writing transcript")
    group = p.add_mutually_exclusive_group(required=False)
    group.add_argument("--markdown-file", help="Optional markdown summary file to append")
    group.add_argument("--text", help="Optional raw markdown summary text to append")
    p.add_argument("--require-summary", action="store_true", help="Require summary-related sections during verification")
    p.add_argument("--cleanup-mode", choices=["none", "temp", "all"], default="temp", help="Cleanup mode after verification")
    p.add_argument("--dry-run", action="store_true", help="Preview resume actions without writing/cleanup")
    p.set_defaults(func=cmd_resume)

    p = sub.add_parser("run", help="one-shot pipeline: prepare -> optional summary -> verify -> cleanup")
    p.add_argument("--url", required=True, help="Video URL (Bilibili/b23 primary; also usable with YouTube and other yt-dlp-supported sites)")
    p.add_argument("--page-id", help="Existing Notion page id")
    p.add_argument("--replace-children", action="store_true", help="Archive existing top-level children before writing transcript")
    group = p.add_mutually_exclusive_group(required=False)
    group.add_argument("--markdown-file", help="Optional markdown summary file to append")
    group.add_argument("--text", help="Optional raw markdown summary text to append")
    p.add_argument("--require-summary", action="store_true", help="Require summary-related sections during verification")
    p.add_argument("--cleanup-mode", choices=["none", "temp", "all"], default="temp", help="Cleanup mode after verification")
    p.add_argument("--dry-run", action="store_true", help="Preview full pipeline actions without writing/cleanup")
    p.set_defaults(func=cmd_run)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except PipelineError as e:
        payload = {"ok": False, "error": e.to_dict()}
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
