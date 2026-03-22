---
name: agent-bilibili-notion-pipeline
description: Process a Bilibili/b23 link into a Notion transcript page: download the video, transcribe audio, upload the mp4, create or update a Notion page, write transcript blocks, then append an agent-written Markdown summary. Use when the user wants B站内容整理进 Notion、字幕入库、文后总结追加、下载链接回写等流程。
---

# Agent Bilibili → Notion Pipeline

这个 skill 把工作拆成两类：

1. **脚本负责稳定执行**
   - 下载视频
   - 抽音频
   - 转写文本
   - 上传视频
   - 创建/更新 Notion 页面
   - 写入正文 blocks
   - 清理临时文件

2. **agent 负责判断与总结**
   - 页面是新建还是更新
   - 是否替换旧正文
   - 文后总结怎么写
   - 需要给用户回报哪些进度
   - 出错时如何切换兜底路径

## 什么时候用

当用户提出类似请求时触发：

- “把这个 B 站视频整理进 Notion”
- “下载、转写、上传并写 Notion”
- “给这篇整理字幕页补结构梳理和核心观点”
- “把视频内容做成正文 + 文后总结”

## 标准流程

### 1）执行 `prepare`

```bash
python skill/agent-bilibili-notion-pipeline/scripts/pipeline.py prepare --url "<b23或BV链接>"
```

如果用户明确给了已有 Notion 页面：

```bash
python skill/agent-bilibili-notion-pipeline/scripts/pipeline.py prepare \
  --url "<链接>" \
  --page-id "<notion_page_id>" \
  --replace-children
```

`prepare` 会输出 JSON，记下：

- `page_id`
- `notion_url`
- `transcript_path`
- `metadata_path`
- `download_url`

### 2）阅读转写正文

用 `read` 读取 `transcript_path`，判断：

- 主题是否跑偏
- 识别质量是否可接受
- 文后总结应该如何组织

### 3）按固定风格写文后总结

默认建议最少包含：

- `## 结构梳理`
- `## 核心观点`
- `## 关键概念`

风格要求：

- 中文
- 简洁
- 好读
- 不空话
- 不复述一整遍原文

可参考：

- `references/summary-template.md`
- `references/workflow.md`

### 4）把总结追加到 Notion

先把 Markdown 写到临时文件，再追加：

```bash
python skill/agent-bilibili-notion-pipeline/scripts/pipeline.py append-summary \
  --page-id "<page_id>" \
  --markdown-file "/tmp/summary.md"
```

### 5）按需清理

默认建议删除：

- wav
- transcript txt

本地 mp4 是否删除，由用户决定：

```bash
python skill/agent-bilibili-notion-pipeline/scripts/pipeline.py cleanup \
  --metadata "<metadata_path>"
```

如果用户明确不要保留视频：

```bash
python skill/agent-bilibili-notion-pipeline/scripts/pipeline.py cleanup \
  --metadata "<metadata_path>" \
  --delete-video
```

## 进度回报要求

长任务不要静默卡住。

至少在这些节点主动回报：

1. 已解析视频 / 已开始下载
2. 已开始转写
3. 已上传并拿到 `download_url`
4. 已写入 Notion 正文
5. 已补文后总结
6. 已清理 / 保留了哪些本地文件

## 注意事项

- 不要把真实 token、cookies、profile、日志提交到仓库
- 官方字幕不可靠，默认准备 ASR 兜底
- 如果转写质量明显跑偏，不要硬写总结，先告知用户
- 更新已有页面时，只有在用户明确要求替换旧正文时才用 `--replace-children`
