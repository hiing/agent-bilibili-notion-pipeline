# bilibili-notion-pipeline

[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-7c3aed)](https://github.com/hiing/agent-bilibili-notion-pipeline)
[![Skill First](https://img.shields.io/badge/position-skill--first-10b981)](https://github.com/hiing/agent-bilibili-notion-pipeline)
[![Bilibili to Notion](https://img.shields.io/badge/pipeline-Bilibili%20%E2%86%92%20Notion-0ea5e9)](https://github.com/hiing/agent-bilibili-notion-pipeline)
[![License: MIT](https://img.shields.io/badge/license-MIT-black)](./LICENSE)

[English README](./README.en.md)

> 给一条 B 站链接，
> 让它穿过下载、转写、上传、入库与整理，
> 最后安静地落在 Notion 的一页纸上。

`bilibili-notion-pipeline` 现在明确定位为：

> **一个 skill-first、agent-enhanced 的 B 站 → Notion 流水线技能仓库。**

也就是说：

- **Skill 是第一身份**：它首先是一套可复用、可调用、可稳定执行的 OpenClaw Skill
- **Agent 是增强层**：在需要总结、判断、补救、回报时，再让 agent 出手

它不追求“什么都能干”，只想把一件事做好：

> **把视频内容从 Bilibili 搬进 Notion，并整理成可读、可存、可续写的知识页。**

---

## 它能实现什么

有些功能像工具，有些功能更像习惯；这套仓库把两者都留了下来。

### 1. 入口解析
- 接收 `b23.tv` 短链或标准 Bilibili 链接
- 解析视频标题、BV 号、原始视频 URL
- 为后续写入建立统一元数据

### 2. 视频落地
- 下载视频到本地
- 统一命名，便于重跑、续跑与排错
- 保留原始 mp4，直到你决定是否清理

### 3. 音频提取与转写
- 用 `ffmpeg` 抽出 wav
- 优先走本地 ASR（`faster-whisper` / `whisper`）
- 转写后做轻量清洗：繁转简、断句、分段

### 4. 上传并生成公开地址
- 上传 mp4 到存储服务
- 获取公开 `download_url`
- 回写到 Notion 页面属性中

### 5. Notion 页面创建 / 更新
- 新建页面，或更新已有页面
- 写入页面属性：
  - `title`
  - `URL`
  - `download_url`
- 把字幕正文写成标准 blocks

### 6. 文后总结追加
- 将 Markdown 总结追加到正文后
- 适合补：
  - 结构梳理
  - 核心观点
  - 关键概念
- 这一步既可以人工提供，也可以交给 agent 生成

### 7. 清理策略
- 默认删除中间文件：`wav`、转写文本
- 可选删除本地 mp4
- 远端 `download_url` 与 Notion 页面默认保留

### 8. 适合被谁调用
- 适合人工手动调用
- 适合被 OpenClaw 作为 **Skill** 调用
- 也适合被更大的 workflow / agent 当作“稳定执行层”调用

---

## 出发前，要准备几把钥匙

如果你想让这条流水线真正跑起来，需要先准备几样东西。

### 必备参数

| 名称 | 环境变量 | 说明 |
|---|---|---|
| Notion API Key | `NOTION_API_KEY` | 用于创建/更新页面与写入 blocks |
| Notion 数据库 ID | `NOTION_DATABASE_ID` | 新页面默认创建到这里 |
| 上传地址 | `UPLOAD_URL` | mp4 上传入口 |
| 上传令牌 | `UPLOAD_TOKEN` | 上传服务鉴权 |

### 强烈建议准备

| 名称 | 环境变量 | 说明 |
|---|---|---|
| B站 cookies 文件 | `BILI_COOKIES_FILE` | 降低 412 / 403 / 限制概率 |
| 下载目录 | `BILI_DOWNLOAD_DIR` | 本地 mp4 保存路径 |
| 临时目录 | `BILI_TEMP_DIR` | wav、txt、metadata 等中间产物路径 |
| Whisper 模型 | `WHISPER_MODEL` | 如 `small` / `medium` |
| Whisper 语言 | `WHISPER_LANGUAGE` | 通常是 `zh` |
| Whisper 计算类型 | `WHISPER_COMPUTE_TYPE` | 如 `float16` / `int8`，留空或 `auto` 表示自动 |
| ASR 分段阈值 | `ASR_AUTO_SEGMENT_MINUTES` | 超过多少分钟自动启用分段转写 |
| ASR 分段时长 | `ASR_SEGMENT_SECONDS` | 每段多少秒，默认 600 |

### 推荐安装的运行依赖

- Python 3.10+
- `ffmpeg`
- `pip install -r requirements.txt`
- 推荐：`faster-whisper`
- 兜底：`whisper` CLI

---

## 仓库结构

```text
bilibili-notion-pipeline/
├── README.md                  # 中文默认说明
├── README.en.md               # 英文独立说明
├── LICENSE
├── .gitignore
├── .env.example
├── requirements.txt
├── data/
│   ├── downloads/bilibili/    # 本地视频落地目录（运行期）
│   └── bili_temp/             # wav / txt / metadata（运行期）
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

## 快速开始

### 1）复制环境变量模板

```bash
cp .env.example .env
```

然后把真实参数填进去。

---

### 2）一键执行 `run`

最推荐直接用：

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py run \
  --url "https://b23.tv/xxxxx" \
  --cleanup-mode temp
```

如果你已经准备好了总结 Markdown：

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py run \
  --url "https://b23.tv/xxxxx" \
  --markdown-file /path/to/summary.md \
  --require-summary \
  --cleanup-mode temp
```

这一步会串起来：
- 下载视频
- 抽音频
- 转写
- 上传 mp4
- 创建/更新 Notion 页面
- 写入“整理字幕”正文
- 可选追加总结
- 回读校验
- 清理中间文件

输出会给你一份完整 JSON，通常包含：

- `bvid`
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

### 3）分步执行 `prepare`

如果你想在正文写入后，人工再补总结：

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py prepare \
  --url "https://b23.tv/xxxxx"
```

如果用户明确给了已有 Notion 页面：

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py prepare \
  --url "<链接>" \
  --page-id "<notion_page_id>" \
  --replace-children
```

---

### 4）查看状态 `state`

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py state \
  --metadata /path/to/BVxxxx.metadata.json
```

适合查看：
- 当前停在哪一步
- 本地 mp4 / wav / transcript 是否还在
- 是否已经追加总结
- 最近一次校验结果是什么

---

### 5）补总结并回写 Notion

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py append-summary \
  --page-id "NOTION_PAGE_ID" \
  --markdown-file /path/to/summary.md
```

如果你已经有 `metadata_path`，也可以后续自己从 metadata 里取 `page_id`。

---

### 6）回读校验 `verify`

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py verify \
  --metadata /path/to/BVxxxx.metadata.json \
  --require-summary
```

它会检查：
- 是否存在“整理字幕”标题
- 是否存在“正文”标题
- 是否有正文段落
- 是否存在总结区（开启 `--require-summary` 时）

校验不通过会非 0 退出。

---

### 7）断点续跑 `resume`

如果长任务中断、转写完成但还没写回、或写了一半后要继续：

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py resume \
  --metadata /path/to/BVxxxx.metadata.json \
  --cleanup-mode temp
```

如果这次恢复时顺便补总结：

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py resume \
  --metadata /path/to/BVxxxx.metadata.json \
  --markdown-file /path/to/summary.md \
  --require-summary \
  --cleanup-mode temp
```

---

### 8）清理临时文件 `cleanup`

只删 wav / txt：

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py cleanup \
  --metadata /path/to/BVxxxx.metadata.json \
  --mode temp
```

连本地 mp4 一起删：

```bash
python skill/bilibili-notion-pipeline/scripts/pipeline.py cleanup \
  --metadata /path/to/BVxxxx.metadata.json \
  --mode all
```

---

## 典型工作流

可以把它理解成一条顺流而下的线：

```text
B站链接
  ↓
解析元数据
  ↓
下载 mp4
  ↓
抽 wav + ASR
  ↓
上传视频 → 获得 download_url
  ↓
创建 / 更新 Notion 页面
  ↓
写入“整理字幕”正文
  ↓
人工或 agent 生成 Markdown 总结
  ↓
追加到正文后
  ↓
清理临时文件
```

---

## 为什么现在主打 skill-first？

因为这套流程的大部分步骤，都是典型的 **低自由度、可重复、可脚本化** 工作：

- 下载
- 抽音频
- 转写
- 上传
- 写 Notion
- 清理

这些更适合被封装成 **Skill + scripts**，而不是硬包装成一个独立的“全能 agent 产品”。

### Skill 是主体
- 可复用
- 可调用
- 可组合
- 可被别的 agent / workflow 引用

### Agent 是增强层
agent 更适合处理这些不那么确定的部分：
- 该新建页还是更新页
- 旧正文该替换还是追加
- 总结怎么写才自然
- 长任务如何主动汇报
- 转写质量差时是否暂停并请人确认

所以这套仓库现在最准确的定位是：

> **Skill-first，agent-enhanced。**

---

## 它还算不算 agent？

算，但不必把“agent”当成唯一身份。

更准确地说，它是：

> **一个以 Skill 为主体、以 Agent 为增强层的垂直 workflow 仓库。**

这比单纯叫“agent 项目”更稳，也更适合公开发布。

---

## 已知限制

- B站可能返回 `412 / 403`
- 官方字幕并不可靠，常常要走本地 ASR
- 长视频转写很慢
- Notion 写入稳定，但总结质量取决于正文质量
- 这套仓库只覆盖 **B站 → Notion** 这条链，不覆盖其他平台登录/风控系统

---

## 安全边界

这个仓库是为 **公开发布** 整理的，因此：

### 不应该提交的东西
- `.env`
- Notion token
- 上传 token
- B站 cookies
- 浏览器 profile
- 本地下载视频
- wav / txt / logs / 临时 metadata

### 应该保留的东西
- 结构化脚本
- Skill 定义
- 模板与说明文档
- 环境变量模板

---

## 下一步适合怎么扩展

你可以继续把它往三种方向推进：

### 1. 更像产品
- 增加 CLI 参数
- 增加批量模式
- 增加错误码和更清晰的日志

### 2. 更像 Skill
- 让 OpenClaw 自动触发
- 统一总结风格
- 固定进度回报协议
- 增加更清晰的 references / examples

### 3. 更像 Agent 增强层
- 自动判断“替换正文 / 追加正文”
- 自动验收总结质量
- 自动清理策略分级
- 自动重试与断点恢复

---

## License

MIT
