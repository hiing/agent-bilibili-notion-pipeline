from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

NOTION_VERSION = "2022-06-28"


def page_url(page_id: str) -> str:
    return f"https://www.notion.so/{page_id.replace('-', '')}"


def notion_headers(api_key: str) -> Dict[str, str]:
    if not api_key:
        raise RuntimeError("NOTION_API_KEY is required")
    return {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def create_or_update_page(
    api_key: str,
    title: str,
    video_url: str,
    download_url: Optional[str],
    page_id: Optional[str],
    database_id: str,
) -> Dict[str, Any]:
    headers = notion_headers(api_key)
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

    if not database_id:
        raise RuntimeError("NOTION_DATABASE_ID is required when creating a new page")

    resp = requests.post(
        "https://api.notion.com/v1/pages",
        headers=headers,
        json={"parent": {"database_id": database_id}, "properties": props},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def list_children(api_key: str, block_id: str) -> List[Dict[str, Any]]:
    headers = notion_headers(api_key)
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


def get_page(api_key: str, page_id: str) -> Dict[str, Any]:
    headers = notion_headers(api_key)
    resp = requests.get(f"https://api.notion.com/v1/pages/{page_id}", headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()


def archive_all_children(api_key: str, page_id: str) -> None:
    headers = notion_headers(api_key)
    for child in list_children(api_key, page_id):
        requests.patch(
            f"https://api.notion.com/v1/blocks/{child['id']}",
            headers=headers,
            json={"archived": True},
            timeout=60,
        ).raise_for_status()


def append_blocks(api_key: str, page_id: str, blocks: List[Dict[str, Any]]) -> List[str]:
    headers = notion_headers(api_key)
    appended_ids: List[str] = []
    for i in range(0, len(blocks), 100):
        chunk = blocks[i:i + 100]
        resp = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=headers,
            json={"children": chunk},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("results", []):
            if item.get("id"):
                appended_ids.append(item["id"])
    return appended_ids


def archive_blocks(api_key: str, block_ids: List[str]) -> Dict[str, Any]:
    headers = notion_headers(api_key)
    archived: List[str] = []
    failed: List[Dict[str, str]] = []
    for block_id in block_ids:
        try:
            requests.patch(
                f"https://api.notion.com/v1/blocks/{block_id}",
                headers=headers,
                json={"archived": True},
                timeout=60,
            ).raise_for_status()
            archived.append(block_id)
        except Exception as e:
            failed.append({"id": block_id, "error": str(e)})
    return {"archived": archived, "failed": failed, "ok": not failed}
