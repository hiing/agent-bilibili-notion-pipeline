# 0.1.1 — Stability release

## Summary
This release upgrades the project from a runnable prototype to a more repeatable workflow.

Core goals:
- one-shot execution
- post-write verification
- explicit cleanup policy
- clearer progress output

## Added
- `run` command for one-shot execution
- `verify` command for Notion read-back validation
- `cleanup --mode {none,temp,all}` for explicit cleanup policy
- structured progress output on stderr during execution

## Changed
- `cleanup --delete-video` kept as backward-compatible alias for `--mode all`
- `run` can optionally append a Markdown summary and require summary presence during verification
- metadata now stores final workflow state and cleanup information

## Intended user impact
Before `0.1.1`, the pipeline could finish writing but still leave ambiguity about:
- whether the page structure was complete
- whether the summary was present
- what local artifacts were kept or deleted

After `0.1.1`, the pipeline should be easier to:
- run in one shot
- validate automatically
- clean up consistently
- diagnose from command output and metadata files

## Suggested next priorities for 0.1.2+
- resumable state machine
- segmented transcription for long videos
- stronger Notion template enforcement
- create / update / upsert modes
- better progress callbacks for long-running agent execution
