# agent-bilibili-notion-pipeline

[中文 README](./README.md)

> Give it a Bilibili link,
> let it pass through download, transcription, upload, storage, and structure,
> and let it finally settle into a Notion page.

`agent-bilibili-notion-pipeline` is a vertical **agent/workflow-oriented** repository for moving video knowledge from **Bilibili → Notion**.

- **Scripts** handle deterministic execution
- **The agent** handles judgment, outlining, fallback, and progress reporting

It is not trying to be a universal AI researcher.
It is trying to do one thing well:

> **turn a Bilibili video into a structured Notion knowledge page, with transcript, download link, and postscript summary.**

---

## What it can do

### 1. Link resolution
- Accepts both `b23.tv` short links and standard Bilibili URLs
- Extracts title, BVID, and canonical video URL
- Produces normalized metadata for downstream steps

### 2. Local video download
- Downloads the source video to local storage
- Uses consistent naming for reruns and debugging
- Keeps the original mp4 unless you explicitly delete it

### 3. Audio extraction & transcription
- Extracts wav with `ffmpeg`
- Uses local ASR (`faster-whisper` / `whisper`) as the default fallback path
- Normalizes transcript text with light cleanup: simplified Chinese conversion, sentence splitting, paragraphing

### 4. Upload & public `download_url`
- Uploads the mp4 to a storage endpoint
- Retrieves a public `download_url`
- Writes that URL back into the Notion page properties

### 5. Notion page creation / update
- Creates a new page or updates an existing one
- Writes page properties:
  - `title`
  - `URL`
  - `download_url`
- Writes transcript body blocks into the page

### 6. Postscript summary append
- Appends an agent-written Markdown summary after the transcript
- Works well for:
  - structure outline
  - core thesis
  - key concepts

### 7. Cleanup policy
- Deletes intermediate artifacts by default: `wav`, transcript txt
- Optionally deletes the local mp4 as well
- Keeps the remote `download_url` and Notion page by default

### 8. Intended usage
- Can be run manually
- Can be wrapped as an OpenClaw skill
- Can serve as the deterministic execution layer inside a larger agent workflow

---

## What you need before it can run

There are a few keys and paths that must be prepared before the pipeline becomes real.

### Required parameters

| Name | Environment Variable | Purpose |
|---|---|---|
| Notion API Key | `NOTION_API_KEY` | Create / update pages and write blocks |
| Notion database ID | `NOTION_DATABASE_ID` | Default parent database for newly created pages |
| Upload endpoint | `UPLOAD_URL` | Where mp4 files are uploaded |
| Upload token | `UPLOAD_TOKEN` | Auth for the upload service |

### Strongly recommended

| Name | Environment Variable | Purpose |
|---|---|---|
| Bilibili cookies file | `BILI_COOKIES_FILE` | Reduces 412 / 403 / access issues |
| Download directory | `BILI_DOWNLOAD_DIR` | Where local mp4 files are stored |
| Temp directory | `BILI_TEMP_DIR` | Where wav/txt/metadata artifacts live |
| Whisper model | `WHISPER_MODEL` | e.g. `small`, `medium` |
| Whisper language | `WHISPER_LANGUAGE` | usually `zh` |
| Whisper compute type | `WHISPER_COMPUTE_TYPE` | e.g. `float16`, `int8`, or `auto` |

### Runtime dependencies

- Python 3.10+
- `ffmpeg`
- `pip install -r requirements.txt`
- Recommended: `faster-whisper`
- Fallback: `whisper` CLI

---

## Repository layout

```text
agent-bilibili-notion-pipeline/
├── README.md
├── README.en.md
├── LICENSE
├── .gitignore
├── .env.example
├── requirements.txt
├── data/
│   ├── downloads/bilibili/
│   └── bili_temp/
└── skill/
    └── agent-bilibili-notion-pipeline/
        ├── SKILL.md
        ├── scripts/
        │   ├── pipeline.py
        │   └── notion_markdown.py
        └── references/
            ├── workflow.md
            └── summary-template.md
```

---

## Quick start

### 1) Copy the environment template

```bash
cp .env.example .env
```

Then fill in your real values.

---

### 2) Run `prepare`

```bash
python skill/agent-bilibili-notion-pipeline/scripts/pipeline.py prepare \
  --url "https://b23.tv/xxxxx"
```

This step tries to complete:
- video download
- audio extraction
- transcription
- mp4 upload
- Notion page creation/update
- transcript body writing

The command returns JSON with fields like:

- `bvid`
- `title`
- `video_url`
- `local_file`
- `wav_path`
- `transcript_path`
- `page_id`
- `notion_url`
- `download_url`
- `metadata_path`

---

### 3) Let the agent write a summary

Read `transcript_path`, then generate a Markdown summary.

Suggested structure:
- `## Structure`
- `## Core Thesis`
- `## Key Concepts`

Reference:
- `skill/agent-bilibili-notion-pipeline/references/summary-template.md`

---

### 4) Append the summary to Notion

```bash
python skill/agent-bilibili-notion-pipeline/scripts/pipeline.py append-summary \
  --page-id "NOTION_PAGE_ID" \
  --markdown-file /path/to/summary.md
```

---

### 5) Cleanup temporary files

Delete wav / transcript only:

```bash
python skill/agent-bilibili-notion-pipeline/scripts/pipeline.py cleanup \
  --metadata /path/to/BVxxxx.metadata.json
```

Delete wav / transcript / local video:

```bash
python skill/agent-bilibili-notion-pipeline/scripts/pipeline.py cleanup \
  --metadata /path/to/BVxxxx.metadata.json \
  --delete-video
```

---

## Typical flow

```text
Bilibili link
  ↓
Resolve metadata
  ↓
Download mp4
  ↓
Extract wav + run ASR
  ↓
Upload video → get download_url
  ↓
Create / update Notion page
  ↓
Write transcript body
  ↓
Agent generates Markdown summary
  ↓
Append summary below the body
  ↓
Cleanup temporary files
```

---

## Is this really an agent?

Yes — but more precisely, it is a:

> **specialized workflow agent**

### Why it has agent qualities
- It has a clear goal: organize video knowledge into Notion
- It has state: it knows which step it is in
- It has branches: subtitles vs ASR, new page vs existing page, cleanup vs keep
- It can report progress during long runs
- It can use fallback paths instead of failing immediately

### Why it is not a universal agent
- It still depends on external platform stability
- Some login / anti-bot flows still need human intervention
- Summary quality still depends on transcript quality

So the cleanest definition is:

> **let scripts do the certain parts; let the agent handle the uncertain parts.**

---

## Known limitations

- Bilibili may return `412 / 403`
- Official subtitles are unreliable, so local ASR is often required
- Long videos can be slow to transcribe
- Notion writing is stable, but summary quality depends on transcript quality
- This repo only covers the **Bilibili → Notion** path, not unrelated platform login / risk-control systems

---

## Security boundary

This repository is organized for **public release**, so the following should never be committed:

- `.env`
- Notion tokens
- upload tokens
- Bilibili cookies
- browser profiles
- downloaded videos
- wav / txt / logs / temporary metadata

What should remain in the repo:
- structured scripts
- skill definition
- reference templates
- environment variable examples

---

## Good next directions

You can evolve it in three ways:

### 1. More product-like
- more CLI arguments
- batch mode
- clearer error codes and logs

### 2. More skill-like
- automatic OpenClaw triggering
- unified summary style
- a fixed progress-reporting protocol

### 3. More agent-like
- automatic choice between replace/append body
- automatic transcript quality checks
- smarter cleanup policy
- retry and resume logic

---

## License

MIT
