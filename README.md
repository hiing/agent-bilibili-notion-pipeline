# bilibili-notion-pipeline

[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-7c3aed)](https://github.com/hiing/bilibili-notion-pipeline-skill)
[![Skill First](https://img.shields.io/badge/position-skill--first-10b981)](https://github.com/hiing/bilibili-notion-pipeline-skill)
[![Bilibili to Notion](https://img.shields.io/badge/pipeline-Bilibili%20%E2%86%92%20Notion-0ea5e9)](https://github.com/hiing/bilibili-notion-pipeline-skill)
[![License: MIT](https://img.shields.io/badge/license-MIT-black)](./LICENSE)
[![Clawhub](https://img.shields.io/badge/Clawhub-hiing%2Fbilibili--notion--pipeline-6d28d9)](https://clawhub.ai/hiing/bilibili-notion-pipeline)

[![Bilibili](https://img.shields.io/badge/Bilibili-00A1D6?logo=bilibili&logoColor=white)](https://www.bilibili.com/)
[![Notion](https://img.shields.io/badge/Notion-000000?logo=notion&logoColor=white)](https://www.notion.so/)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-007808?logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![Whisper](https://img.shields.io/badge/ASR-Whisper-412991?logo=openai&logoColor=white)](https://github.com/openai/whisper)
[![Telegram Storage](https://img.shields.io/badge/Telegram-backed%20storage-26A5E4?logo=telegram&logoColor=white)](https://telegram.org/)

[English README](./README.en.md)

> 已发布到 Clawhub：<https://clawhub.ai/hiing/bilibili-notion-pipeline>

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

## 🎯 这个 Skill 会直接帮你做什么

如果只用一句话概括，这个 Skill 负责把：

> **B站链接 → 原视频落地 → 字幕转写 → 存储上传 → Notion 入库 → 大纲总结**

串成一条真正能跑的链路。

更具体地说，它会直接帮助你：

- 接一条 B 站链接，自动完成解析、下载、抽音频、转写、上传、写入 Notion
- 把原视频保存到你指定的网盘、存储后端或自建上传服务，而不是只在 OpenClaw 里临时落一下
- 把正文稳定写成可长期保存、可再次编辑的 Notion 页面
- 在正文后继续追加结构化总结、大纲、核心观点和关键概念
- 在长任务过程中做阶段性进度回报，而不是长时间静默
- 在收尾时清掉大多数过程垃圾文件，只保留知识痕迹与必要元数据

---

## ✨ 它能实现什么

有些功能像工具，有些功能更像习惯；这套仓库把两者都留了下来。

### 1. 入口解析
- 接收 `b23.tv` 短链或标准 Bilibili 链接
- 解析视频标题、BV 号、原始视频 URL
- 为后续写入建立统一元数据

### 2. 原视频落地与可迁移归档
- 下载原视频到本地
- 统一命名，便于重跑、续跑与排错
- 原视频不是一次性耗材：既可以暂存在本地，也可以继续上传到你自己的网盘、自建存储或指定后端
- 这样保留下来的不是一段“执行过程”，而是一份可回放、可迁移、可再次处理的媒体资产

### 3. 音频提取与转写
- 用 `ffmpeg` 抽出 wav
- 优先走本地 ASR（`faster-whisper` / `whisper`）
- 转写后做轻量清洗：繁转简、断句、分段
- 长音频可切换为分段转写，降低单次转写过慢或失败的风险

### 4. 上传到自己的网盘或指定存储
- 上传 mp4 到你指定的存储服务，而不是把文件锁死在 OpenClaw 工作目录里
- 获取公开 `download_url`
- 回写到 Notion 页面属性中
- 当前自用实例是 `https://stor.pull.eu.org/`
- 如果你有自己的后端、网盘桥接层或自建对象存储，也可以替换成自己的上传入口

### 5. Notion 页面创建 / 更新
- 新建页面，或更新已有页面
- 写入页面属性：
  - `title`
  - `URL`
  - `download_url`
- 把字幕正文写成标准 blocks
- 支持把页面作为“文字留档层”：先把原始内容稳定入库，再决定是否追加分析内容
- 如有需要，也可在更新时替换旧正文，而不是盲目叠加

### 6. 文字留档、分析与大纲汇总
- 将转写正文写入 Notion，形成可检索、可复制、可继续加工的文字档案
- 将 Markdown 总结追加到正文后，形成“原文在前、分析在后”的双层结构
- 适合补：
  - 结构梳理
  - 核心观点
  - 关键概念
  - 大纲汇总
- 这一步既可以人工提供，也可以交给 agent 生成
- 这样既保留原始材料，又保留面向阅读和复盘的结构化结果

### 7. 燕过留痕，但不留过程垃圾
- 默认删除中间文件：`wav`、转写文本
- 可选删除本地 mp4
- 远端 `download_url` 与 Notion 页面默认保留
- metadata 也会保留，用于断点续跑、回读校验和审计
- 换句话说：**知识痕迹留在 Notion 和元数据里，过程垃圾尽量不留在 OpenClaw 工作区里**

### 8. Skill / Agent 过程汇报
- 脚本本身会按阶段输出进度：解析、下载、抽音频、转写、上传、写 Notion、校验、清理
- Skill / agent 层可以直接转发这些阶段性进度，避免长任务“静默跑很久”
- 特别是 ASR 很慢、上传较大文件、Notion 写入较多 blocks 时，适合做主动汇报
- 如果出现异常，也更容易在中途停下确认，而不是等到最后才发现整条链路跑偏

### 9. 适合被谁调用
- 适合人工手动调用
- 适合被 OpenClaw 作为 **Skill** 调用
- 也适合被更大的 workflow / agent 当作“稳定执行层”调用
- 如果你想要的是一条稳定、可追踪、可回报、可清理的媒体入库链路，它比“纯聊天式临时操作”更可靠

---

## 🗝️ 出发前，要准备几把钥匙

如果你想让这条流水线真正跑起来，需要先准备几样东西。

## 🧰 这个 Skill 开跑前你必须准备什么

这个 Skill 不是纯提示词，它依赖一套真实运行环境。最少要准备下面几类条件：

### 运行环境
- Python 3.10+
- `ffmpeg`
- 对应 Python 依赖（见 `requirements.txt`）
- 推荐安装 `faster-whisper`；如果没有，则至少要有可用的 `whisper` CLI 兜底

### Whisper / ASR 条件
- 这条链路默认支持 **CPU 转写**，不要求必须有 GPU
- 但如果只跑 CPU，长视频会明显变慢；视频越长，等待时间越长
- 对于 10 分钟以内的内容，CPU 通常还能接受；到了更长视频，建议：
  - 使用更快的机器
  - 降低模型规模
  - 或启用分段转写来降低单次失败风险
- 换句话说：**没有 GPU 也能跑，但 CPU 会直接决定这条 skill 的体感速度**

### Notion 条件
- 你必须提供可用的 `NOTION_API_KEY`
- 你必须提供目标 `NOTION_DATABASE_ID`
- 对应的 Notion Integration 必须已经被授权写入目标数据库 / 页面
- 如果 Notion 权限没配好，前面步骤都成功了，最后也会卡在“写不进去”这一层

### 存储 / 网盘条件
- 你必须提供一个可用的上传入口（`UPLOAD_URL`）
- 你必须提供对应的上传鉴权（`UPLOAD_TOKEN`）
- 这个上传入口可以是：
  - 你自己的网盘桥接层
  - 自建存储服务
  - WebDAV / 对象存储封装后的上传 API
  - 或当前 README 里示例的自托管后端
- 如果没有这层，视频仍然可以先下载和转写，但拿不到稳定的 `download_url`

### Bilibili 访问条件
- 强烈建议准备 `BILI_COOKIES_FILE`
- 否则在部分视频上可能遇到：
  - 412
  - 403
  - 下载质量受限
  - 元数据抓取失败

也就是说，这个 Skill 最适合的运行前提是：

> **一台能跑 ffmpeg + whisper 的机器，
> 一个可写入的 Notion Integration，
> 再加一个你自己可控的上传 / 网盘后端。**

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

### 关于当前自用上传后端

这个仓库默认把上传后端视为**可替换组件**，但我当前自用的是：

- `https://stor.pull.eu.org/`

这套能力并不是从零写的，而是**受益于**下面这个项目提供的思路、实现基础，以及它本身已经整理得比较成熟的上传接口：

- `https://github.com/MarSeventh/CloudFlare-ImgBed`
- 上传 API 文档：`https://cfbed.sanyue.de/api/upload.html`

我这里实际看重的，不只是“图床/外链”本身，而是它背后的几件事：

#### 1）WebDAV 很关键
对这条流水线来说，WebDAV 的价值非常直接：

- 可以把远端存储当成更稳定的文件落点
- 方便后续手动整理、迁移、备份
- 不只服务这一个 pipeline，也能顺手接别的自动化流程

也就是说，它不只是一个“上传接口”，更像一个**轻量文件层**。

#### 2）程序自身提供的 Upload API，也非常适合集成
根据它公开的上传 API 说明，这套程序本身暴露出来的接口，不只是“网页上传按钮的后门”，而是一层已经比较实用的自动化能力：

- 标准 `POST /upload` + `multipart/form-data`，几乎任何语言和脚本都能直接接
- 支持 `authCode` 或 `API Token` 鉴权，适合把上传能力安全地交给第三方脚本或 agent
- 支持 `uploadChannel`、`channelName`，能在多存储渠道之间做显式路由
- 支持 `autoRetry`，失败时可自动切换渠道重试
- 支持 `uploadFolder`、`uploadNameType`、`returnFormat`，便于控制目录结构、命名方式与返回结果形态
- 不只是给图片用，也可以稳定承接这类“视频先上传、再写 Notion download_url”的工作流

这点很重要，因为对我这种流水线来说，真正有价值的不是“有个前端能传文件”，而是：

> **它已经把上传动作抽象成一层可编程 API。**

这样一来，上传环节就能被：
- Python 脚本直接调用
- agent workflow 直接编排
- 后续别的自动化任务复用

也就是说，它更像一个**可嵌入的上传后端**，而不只是一个面板产品。

#### 3）基于 Telegram 群组的“近似无限存储”能力
这类方案一个很吸引人的点，是可以借助 **Telegram 群组 / 频道** 去承接文件，形成一种成本极低、容量很松的存储体验。

但这里必须写清楚：

> 这不是传统意义上有 SLA 的正规对象存储，
> 更像是一种非常实用、但带平台风险的工程化取巧方案。

所以在 README 里我会明确建议：

- 可以把它当成**高性价比存储层**
- 但不要把它当成**绝对安全、绝对永久、绝对不会出事**的底层基础设施
- 必须预设：**有被封号、被限流、被删内容、链接失效**的可能

如果你要长期依赖它，最好同时准备：

- 本地原始文件备份
- metadata / transcript 的本地留存
- 将来切换上传后端的迁移预案

#### 4）分块上传是它非常现实的优势
对视频场景来说，分块上传不是锦上添花，而是很实用。

根据这套 API 文档，它把分块上传明确拆成了：
- 初始化 `initChunked=true`
- 分块上传 `chunked=true`
- 最终合并 `merge=true`

这意味着：

- 大文件更稳，不容易一次失败全盘重来
- 弱网 / 波动网络下更容易成功
- 对长视频、较大 mp4 更友好
- 中断后重试成本更低
- 上传逻辑可以显式恢复，而不是只能“整包重传”

对我这条 B站 → Notion 流水线来说，分块上传最大的意义就是：

> **它让“视频上传”这一步，没那么脆。**

这点非常重要，因为真正拖垮长流程的，往往不是 Notion 写入，而是：

- 大文件上传失败
- 网络中断
- 单次请求过大
- 远端处理不稳定

而分片机制对这些问题都有缓冲作用。

### 存储架构 / 数据流

```text
Bilibili Link
   ↓
Resolve metadata (title / bvid / canonical url)
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

### 当前默认存储形态（实践视角）

```text
本地 mp4 / wav / txt
   ↓
上传到 https://stor.pull.eu.org/
   ↓
后端能力受益于 CloudFlare-ImgBed 方案
   ↓
可通过 WebDAV 管理远端文件
   ↓
对外提供 download_url
   ↓
Notion 页面只保存结构化内容 + 公开下载链接
```

这一层设计的重点，不是追求“最正规”，而是追求：

- 足够稳
- 成本低
- 可迁移
- 对长视频友好

也因此，建议把它理解成：

> **一个实用的工程化存储层，而不是零风险的永久归档系统。**

### 运行依赖

- Python 3.10+
- `ffmpeg`
- `pip install -r requirements.txt`
- 推荐：`faster-whisper`
- 兜底：`whisper` CLI

---

## 🧱 仓库结构

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

## 🚀 快速开始

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
