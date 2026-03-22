# bilibili-notion-pipeline

[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-7c3aed)](https://github.com/hiing/bilibili-notion-pipeline-skill)
[![Skill First](https://img.shields.io/badge/position-skill--first-10b981)](https://github.com/hiing/bilibili-notion-pipeline-skill)
[![Video to Notion](https://img.shields.io/badge/pipeline-Video%20%E2%86%92%20Notion-0ea5e9)](https://github.com/hiing/bilibili-notion-pipeline-skill)
[![License: MIT](https://img.shields.io/badge/license-MIT-black)](./LICENSE)
[![Clawhub](https://img.shields.io/badge/Clawhub-hiing%2Fbilibili--notion--pipeline-6d28d9)](https://clawhub.ai/hiing/bilibili-notion-pipeline)

[![Bilibili](https://img.shields.io/badge/Bilibili-00A1D6?logo=bilibili&logoColor=white)](https://www.bilibili.com/)
[![YouTube](https://img.shields.io/badge/YouTube-FF0000?logo=youtube&logoColor=white)](https://www.youtube.com/)
[![Notion](https://img.shields.io/badge/Notion-000000?logo=notion&logoColor=white)](https://www.notion.so/)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-007808?logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![Whisper](https://img.shields.io/badge/ASR-Whisper-412991?logo=openai&logoColor=white)](https://github.com/openai/whisper)
[![Telegram Storage](https://img.shields.io/badge/Telegram-backed%20storage-26A5E4?logo=telegram&logoColor=white)](https://telegram.org/)

[中文 README](./README.md)

> Also published on Clawhub: <https://clawhub.ai/hiing/bilibili-notion-pipeline>

> Give it a video link,
> let it pass through download, transcription, upload, storage, and structure,
> and let it finally settle into a Notion page.

`bilibili-notion-pipeline` is more accurately described as:

> **a Video → Notion workflow repository built around Skill + scripts first, with optional Agent integration when needed (Bilibili-first in maturity).**

Which means:

- **The default execution path is Skill + scripts**: download, transcribe, upload, write to Notion, and cleanup can already run as a complete chain on their own
- **Agent is not a prerequisite**: it only becomes useful when you want more natural summary writing, page-level judgment, exception handling, or progress narration

It is not trying to be a universal AI product.
It is trying to do one thing well:

> **move video knowledge into Notion — Bilibili first, but extensible to YouTube and other yt-dlp-supported sites — then shape it into a page that is readable, storable, and extendable.**

## 🎯 What this skill directly does

If reduced to one sentence, this skill turns:

> **video link (Bilibili first, also extendable to YouTube and other mainstream video sites) → Whisper / ASR subtitle body → storage upload → Notion archiving → outline summary placed below the subtitle body**

into a real executable chain.

More concretely, it directly helps you:

- take a video link and actually execute parsing, download, audio extraction, Whisper / ASR transcription, upload, and Notion writing; Bilibili is the most mature path today, while YouTube and other yt-dlp-supported sites are also within scope
- save the original video into your chosen cloud drive, storage backend, or self-hosted upload service instead of leaving it as a temporary OpenClaw artifact only
- turn Whisper / ASR output into a durable, editable **subtitle body** inside a Notion page
- append structured summary, outline, core thesis, and key concepts **below that subtitle body**
- report stage-based progress during long runs instead of staying silent
- clean up most process junk at the end while preserving the knowledge trace and necessary metadata

---

## ✨ What it can do

### 1. Link resolution
- Accepts `b23.tv` short links, standard Bilibili URLs, and can also take YouTube / other yt-dlp-supported video URLs
- Extracts title, platform content ID (which is often the BV id in Bilibili flows), and canonical video URL
- Produces normalized metadata for downstream steps

### 2. Original video retention and portable archiving
- Downloads the original video to local storage
- Uses consistent naming so reruns, resume flows, and debugging stay manageable
- The original video is not treated as disposable: it can stay locally for a while, or be pushed onward to your own cloud drive, self-hosted storage, or any designated backend
- What remains is not just an execution trace, but a replayable, movable media asset that can be processed again later

### 3. Audio extraction, Whisper transcription, and subtitle-body writing
- Extracts wav with `ffmpeg`
- Uses local ASR (`faster-whisper` / `whisper`) as the default fallback path
- Turns Whisper / ASR output into a more readable **subtitle body**, not just a raw transcript dump
- Normalizes transcript text with light cleanup: simplified Chinese conversion, sentence splitting, paragraphing
- Can switch to segmented transcription for longer audio so very long runs are less fragile

### 4. Upload to your own cloud drive or designated storage
- Uploads the mp4 to the storage service you specify, instead of trapping media inside the OpenClaw workspace
- Retrieves a public `download_url`
- Writes that URL back into the Notion page properties
- The current self-hosted instance is `https://stor.pull.eu.org/`
- If you have your own backend, WebDAV-backed layer, or object storage bridge, the upload target can be replaced with yours

### 5. Notion page creation / update
- Creates a new page or updates an existing one
- Writes page properties:
  - `title`
  - `URL`
  - `download_url`
- Writes the Whisper / ASR **subtitle body** into the page as structured blocks
- Lets the page serve as a **text archive layer** first, before extra analysis is appended
- When needed, can replace stale body content instead of blindly stacking more text underneath it

### 6. Summary and outline placed below the subtitle body
- Writes the Whisper / ASR subtitle body into Notion as searchable, copyable, reusable text records
- Appends a Markdown summary below that subtitle body, creating a two-layer page structure: subtitles first, outline second
- Useful for:
  - structure outline
  - core thesis
  - key concepts
  - summary outline
- The summary can be written manually or generated by an agent
- This keeps both the raw material and the reading-friendly structured interpretation

### 7. Leave knowledge traces, not process junk
- Deletes intermediate artifacts by default: `wav`, transcript txt
- Optionally deletes the local mp4 as well
- Keeps the remote `download_url` and Notion page by default
- Also keeps metadata for resume, verification, and audit purposes
- In other words: **the knowledge trace stays in Notion and metadata, while process clutter is minimized inside the OpenClaw workspace**

### 8. Progress reporting (skill-native, optionally relayed by an agent)
- The script emits stage-based progress messages: resolve, download, extract audio, transcribe, upload, write Notion, verify, cleanup
- Those updates can already serve as the skill's own stage reporting
- If you plug in an agent, it can relay those stage states in a more conversational way — but that is optional, not required
- This is especially useful when ASR is slow, uploads are large, or Notion writing involves many blocks
- If the run starts drifting or failing, it becomes easier to pause mid-way and confirm, instead of discovering the problem only at the end

### 9. Intended usage
- Can be run manually
- Can be used directly as an OpenClaw skill
- Can also serve as the deterministic execution layer inside a larger workflow / automation system
- When needed, an agent can be added on top for summary polish, judgment, or richer user-facing progress updates

---

## 🗝️ What you need before it can run

There are a few keys and paths that must be prepared before the pipeline becomes real.

As for OpenClaw memory / LCM usage later on, that belongs to the host environment itself; this project is compatible with it, but does not try to explain it in detail here.

## 🧰 What you must prepare before this skill can run

This is not a prompt-only skill. It depends on a real execution environment. At minimum, you should prepare the following:

### Runtime environment
- Python 3.10+
- `ffmpeg`
- Required Python dependencies (see `requirements.txt`)
- Preferably `faster-whisper`; otherwise at least a working `whisper` CLI fallback

### Whisper / ASR conditions
- This pipeline supports **CPU transcription** by default; GPU is not strictly required
- But on CPU-only setups, longer videos will become noticeably slower
- For shorter videos, CPU-only execution may be acceptable; for longer ones, it is better to:
  - use a faster machine
  - choose a smaller model
  - or enable segmented transcription to reduce single-run fragility
- In other words: **it can run without GPU, but CPU performance directly shapes the user experience**

### Notion requirements
- You must provide a working `NOTION_API_KEY`
- You must provide the target `NOTION_DATABASE_ID`
- The Notion Integration must already be granted write access to the target database / page
- If Notion permissions are wrong, the earlier stages may succeed but the run will still fail at the final write layer

### Storage / cloud-drive requirements
- You must provide a working upload endpoint (`UPLOAD_URL`)
- You must provide the corresponding upload auth (`UPLOAD_TOKEN`)
- That upload endpoint may be:
  - your own cloud-drive bridge layer
  - a self-hosted storage service
  - a WebDAV / object-storage-backed upload API
  - or the self-hosted backend used in the README examples
- Without this layer, the video can still be downloaded and transcribed, but you will not get a stable `download_url`

### Video-platform access conditions (especially important for Bilibili)
- `VIDEO_COOKIES_FILE` is strongly recommended (the old `BILI_COOKIES_FILE` alias is still accepted)
- Without it, some videos may run into:
  - 412
  - 403
  - limited download quality
  - metadata extraction failure

So the best-fit setup for this skill is:

> **a machine that can run ffmpeg + whisper,
> a writable Notion Integration,
> and an upload / cloud-storage backend you control.**

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
| Video-site cookies file | `VIDEO_COOKIES_FILE` | Reduces 412 / 403 / access issues; especially important for Bilibili, with backward-compatible support for `BILI_COOKIES_FILE` |
| Download directory | `BILI_DOWNLOAD_DIR` | Where local mp4 files are stored |
| Temp directory | `BILI_TEMP_DIR` | Where wav/txt/metadata artifacts live |
| Whisper model | `WHISPER_MODEL` | e.g. `small`, `medium` |
| Whisper language | `WHISPER_LANGUAGE` | usually `zh` |
| Whisper compute type | `WHISPER_COMPUTE_TYPE` | e.g. `float16`, `int8`, or `auto` |
| ASR segment threshold | `ASR_AUTO_SEGMENT_MINUTES` | Auto-enable segmented transcription above this duration |
| ASR segment length | `ASR_SEGMENT_SECONDS` | Segment duration in seconds, default `600` |

### About the current self-hosted upload backend

This repository treats the upload backend as a **replaceable component**, but the instance currently used in practice is:

- `https://stor.pull.eu.org/`

This capability was not built entirely from scratch. It clearly **benefits from** the ideas, implementation foundation, and already well-shaped upload interface provided by:

- `https://github.com/MarSeventh/CloudFlare-ImgBed`
- Upload API docs: `https://cfbed.sanyue.de/api/upload.html`

What matters here is not just “an image bed / public file link”, but several practical properties behind it.

#### 1) WebDAV is a real advantage
For this pipeline, WebDAV matters because it makes the storage layer more useful than a bare upload endpoint:

- it provides a more stable remote landing place for generated files
- it makes manual organization, migration, and backup much easier
- it can serve this pipeline and also other automation flows

So in practice, it behaves less like “just an upload API” and more like a **lightweight file layer**.

#### 2) The built-in Upload API is also a strong integration surface
According to its public upload API docs, the program itself exposes something more useful than a hidden form endpoint behind a web panel — it already provides a fairly practical programmable upload layer:

- standard `POST /upload` + `multipart/form-data`, easy to call from almost any language or script
- supports both `authCode` and `API Token`, which makes third-party automation and agent-side integration cleaner
- supports `uploadChannel` and `channelName` for explicit routing across multiple backends
- supports `autoRetry` so failed uploads can automatically retry on another channel
- supports `uploadFolder`, `uploadNameType`, and `returnFormat`, making naming, directory structure, and return shape controllable
- is not limited to image-oriented use cases; it can also cleanly support this kind of “upload video first, then write download_url into Notion” workflow

That matters because for a pipeline like this, the real value is not merely “there is a UI that can upload files”, but:

> **the upload action has already been abstracted into a programmable API layer.**

That means the upload stage can be:
- called directly from Python scripts
- orchestrated by agent workflows
- reused by future automation tasks

So it behaves more like an **embeddable upload backend**, not just a dashboard product.

#### 3) Telegram-group-based “effectively huge” storage is powerful — but risky
One of the strongest attractions of this kind of setup is the ability to lean on **Telegram groups / channels** as the file-bearing layer, which creates a very cheap and capacity-friendly storage experience.

But this must be stated clearly:

> This is not the same thing as a conventional object storage service with formal SLA guarantees.
> It is a highly practical engineering shortcut, but it comes with platform risk.

So the README should frame it honestly:

- it can be used as a **very cost-effective storage layer**
- but it should not be treated as an **absolutely durable, absolutely safe, never-fails foundation**
- you should assume the possibility of **account bans, rate limits, deleted content, and broken links**

If you depend on it long-term, you should still keep:

- local backups of original files
- local retention of metadata / transcripts
- an escape plan for switching upload backends later

#### 4) Chunked upload is one of its most practical strengths
For video workflows, chunked upload is not cosmetic — it is operationally important.

According to the API docs, chunked upload is explicitly split into:
- initialization via `initChunked=true`
- chunk upload via `chunked=true`
- final merge via `merge=true`

That means:

- large files become more robust to upload
- unstable networks hurt less
- long videos and larger mp4 files become much more manageable
- retries become cheaper after interruption
- upload logic can be resumed explicitly instead of always falling back to full re-upload

For this video → Notion pipeline, the value is simple (with Bilibili currently the most mature path):

> **chunking makes the upload step less brittle.**

And that matters a lot, because in long workflows the fragile point is often not Notion writing, but:

- large upload failures
- network interruptions
- oversized single requests
- unstable remote processing

Chunked upload helps buffer all of those problems.

### Storage architecture / data flow

```text
Video link
   ↓
Resolve metadata (title / content_id / canonical url)
   ↓
Download mp4 to local
   ↓
Extract wav with ffmpeg
   ↓
ASR transcription
  ├─ short audio → direct transcription
  └─ long audio  → segmented transcription → merge transcript
   ↓
Upload mp4 to self-hosted backend
   ↓
Get public download_url
   ↓
Create / update Notion page
   ├─ write properties (title / URL / download_url)
   ├─ write transcript blocks
   └─ optionally append Markdown summary
   ↓
Verify page structure
   ↓
Cleanup temp artifacts
```

### Default storage shape in practice

```text
local mp4 / wav / txt
   ↓
upload to https://stor.pull.eu.org/
   ↓
backend capability benefits from the CloudFlare-ImgBed approach
   ↓
manage remote files through WebDAV
   ↓
expose public download_url
   ↓
Notion stores structured content + public download link
```

The point of this layer is not “formal perfection”, but:

- enough stability
- low cost
- portability
- better tolerance for long videos

So it is best understood as:

> **a practical engineered storage layer, not a zero-risk permanent archive system.**

### Runtime dependencies

- Python 3.10+
- `ffmpeg`
- `pip install -r requirements.txt`
- Recommended: `faster-whisper`
- Fallback: `whisper` CLI

---

## 🧱 Repository layout

```text
bilibili-notion-pipeline/
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
    └── bilibili-notion-pipeline/
        ├── SKILL.md
        ├── scripts/
        │   ├── pipeline.py
        │   └── notion_markdown.py
        └── references/
            ├── workflow.md
            └── summary-template.md
```

---

## 🚀 Quick start

### 1) Copy the environment template

```bash
cp .env.example .env
```

Then fill in your real values.

---

### 2) Run `run` as the default entrypoint

This is now the recommended path:

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py run \
  --url "https://b23.tv/xxxxx" \
  --cleanup-mode temp
```

If you already have a Markdown summary prepared:

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py run \
  --url "https://b23.tv/xxxxx" \
  --markdown-file /path/to/summary.md \
  --require-summary \
  --cleanup-mode temp
```

This executes the full common workflow:
- download video
- extract audio
- transcribe
- upload mp4
- create/update Notion page
- write transcript blocks
- optionally append summary
- verify page structure
- clean temporary files

The JSON output usually contains:

- `content_id` (generic content ID; in Bilibili flows this is usually the BV id)
- `bvid` (compatibility field; may be absent outside Bilibili)
- `title`
- `video_url`
- `local_file`
- `transcript_path`
- `page_id`
- `notion_url`
- `download_url`
- `metadata_path`
- `verification`
- `cleanup`

---

### 3) Use `prepare` for step-by-step mode

If you want to stop after transcript/body writing and add the summary manually later:

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py prepare \
  --url "https://b23.tv/xxxxx"
```

> Note: most command examples still use Bilibili links because that is the most mature path today;
> however, the underlying downloader is `yt-dlp`, so YouTube and other supported video sites are also reasonable targets.

If you already know the target Notion page:

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py prepare \
  --url "<link>" \
  --page-id "<notion_page_id>" \
  --replace-children
```

---

### 4) Inspect saved state with `state`

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py state \
  --metadata /path/to/<content-id>.metadata.json
```

Useful for checking:
- which step the workflow stopped at
- whether local mp4 / wav / transcript still exist
- whether a summary has already been appended
- what the latest verification result was
- what the next suggested action is

---

### 5) Append a summary to Notion

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py append-summary \
  --page-id "NOTION_PAGE_ID" \
  --markdown-file /path/to/summary.md
```

---

### 6) Verify the page with `verify`

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py verify \
  --metadata /path/to/<content-id>.metadata.json \
  --require-summary
```

It checks:
- transcript title heading exists
- body heading exists
- transcript paragraphs exist
- summary-related sections exist (when `--require-summary` is enabled)

The command exits non-zero when verification fails.

---

### 7) Resume an interrupted run with `resume`

If a long run was interrupted, or the transcript body exists but the later steps did not finish:

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py resume \
  --metadata /path/to/<content-id>.metadata.json \
  --cleanup-mode temp
```

If you want to resume and append a summary in the same step:

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py resume \
  --metadata /path/to/<content-id>.metadata.json \
  --markdown-file /path/to/summary.md \
  --require-summary \
  --cleanup-mode temp
```

---

### 8) Cleanup with explicit modes

Delete wav / transcript only:

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py cleanup \
  --metadata /path/to/<content-id>.metadata.json \
  --mode temp
```

Delete wav / transcript / local video:

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py cleanup \
  --metadata /path/to/<content-id>.metadata.json \
  --mode all
```

---

## Typical flow

```text
Video link
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
Manual or agent-generated Markdown summary
  ↓
Append summary below the body
  ↓
Cleanup temporary files
```

---

## Why is this repository written around Skill + scripts by default?

Because most of the workflow is naturally **low-freedom, repeatable, scriptable work**:

- download
- extract audio
- transcribe
- upload
- write to Notion
- cleanup

So it naturally makes sense as **Skill + scripts** first.

That is not about pretending agents do not matter.
It is simply closer to the real execution model:

- script what can be scripted
- bring in an agent only where judgment or wording helps

### Skill + scripts is the default path
- reusable
- callable
- composable
- can run end-to-end on its own
- easy to embed inside other workflows

### Agent is optional enhancement
An agent becomes useful when you want help with parts like:
- whether to create or update a page
- whether to replace or append old body content
- how to write a more natural summary
- how to narrate long-running progress to the user
- whether to pause when transcript quality looks wrong

So the most natural framing is:

> **run it as Skill + scripts by default, and only layer in an agent when that extra flexibility is useful.**

---

## So what is its relationship with agents?

It can absolutely work with agents,
but it does **not require an agent in order to make sense.**

A more accurate description is:

> **a Skill + scripts workflow that can run independently, while still being agent-friendly.**

If all you want is stable execution:
- Skill + scripts is enough

If you also want:
- more natural summaries
- smarter page-level decisions
- more assistant-like progress narration

then you can add an agent on top.

That is more honest than presenting it as if everything depends on agents from the start.

---

## Known limitations

- Bilibili is currently the most mature target path here, but it may still return `412 / 403`
- Other mainstream video sites can work through `yt-dlp`, but real-world success still depends on target-site accessibility and compatibility
- Official subtitles are unreliable, so local ASR is often required
- Long videos can be slow to transcribe
- Notion writing is stable, but summary quality depends on transcript quality
- This repo focuses on the **video → Notion** path; it does not try to cover unrelated platform login / anti-bot systems

---

## Security boundary

This repository is organized for **public release**, so the following should never be committed:

- `.env`
- Notion tokens
- upload tokens
- video-site cookies
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
- fixed progress-reporting protocol
- more structured references / examples

### 3. More agent-enhanced
- automatic choice between replace/append body
- automatic transcript quality checks
- smarter cleanup policy
- retry and resume logic

---

## License

MIT
