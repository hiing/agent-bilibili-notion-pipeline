# Roadmap Notes

This repository is already functionally useful. The next step is not feature sprawl, but making the pipeline safer, more resumable, and more maintainable.

## Current priority themes

### 1. Safer writes
- Add dry-run support for Notion-affecting commands
- Add preflight checks before writing into an existing page
- Record write intent and write results in metadata

### 2. Better state and failures
- Formalize metadata with `schema_version`
- Track `last_success_stage` and `last_error_code`
- Move toward structured stage-aware errors instead of ad hoc exceptions

### 3. Remove silent data loss
- Avoid silently truncating long text when converting transcript/markdown into Notion rich text

### 4. Next likely refactors
- Extract Notion operations into a dedicated module
- Extract metadata/state helpers into a dedicated module
- Introduce upload provider abstraction
- Add summary validation before append
