# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

个人技术文档库（Minke的技术文档库），基于 MkDocs + Material for MkDocs 构建，内容以中文为主，涵盖嵌入式开发、电机控制、AUTOSAR、游戏自动化等技术领域，以及社交/日记等个人内容。推送到 `main` 分支后由 GitHub Actions（`.github/workflows/deploy.yml`）自动构建并部署到 GitHub Pages（https://minkelxy.github.io/MinkeWiki/）。

## 常用命令

```bash
pip install -r requirements.txt   # 安装依赖（mkdocs、mkdocs-material 等）
mkdocs serve                      # 本地开发服务器，热重载，访问 http://localhost:8000
mkdocs build                      # 构建静态站点到 site/（gitignored）
cd chat-analyzer && python -m pytest tests/   # chat-analyzer 单元测试（测试 parser 等模块）
```

- `site/` 已 gitignore，构建产物无需提交。
- **`requirements.txt` 不完整**：`mkdocs.yml` 用到的三个插件均为全局安装、未列入 requirements。全新环境 build 报缺插件时逐个补装：
  ```bash
  pip install mkdocs-encryptcontent-plugin mkdocs-git-revision-date-localized-plugin mkdocs-redirects
  ```
- 部署自动触发，无需手动操作。每晚 23:47 cron 运行 `scripts/auto_backup.sh`：自动 git 提交（`auto: daily backup YYYY-MM-DD`）并尝试 push，周日额外生成 tar 快照到 `/home/minke/backup/`（保留最近 4 份）。

## 内容架构

- `docs/` 为站点内容源，按中文分类目录组织（`知识/`、`制作/`、`社交/`、`健身/`、`创业/`、`游戏/`、`音乐/`、`剧本/` 等）。
- **`mkdocs.yml` 的 `nav` 为手工维护**：新增/删除文档必须同步更新 nav 条目，否则不会出现在站点导航中。「社交 → AI评估 → 日记」下是每天一篇的列表，需逐条追加。
- 插件约定：`encryptcontent` 支持页面加密（加密页不进入明文搜索索引）；`blog` 插件管理 `blog/` 目录（文章在 `docs/blog/posts/`）；`tags` 插件依赖 `docs/tags.md` 标签页。
- 正文支持 mermaid 图（``` mermaid 代码块，由 unpkg 加载渲染）和 admonition 提示框。
- **`docs/社交/` 是目前最活跃、持续维护的部分**：
  - `第0段记录.md` — 长文日记（正在持续撰写，非 AI 生成）
  - `AI评估/日记/<YYYY-MM-DD>.md` — 每日 AI 生成的日记，配套 `AI评估/日记/index.md` 索引，以及评分总表、人物画像、待跟进、阶段分析等报告
  - 每日日记的完整写入/更新流程见 `.agents/skills/diary/SKILL.md`（新建文件 → 按格式撰写 → 追加 index.md → 更新 mkdocs.yml nav）

## 社交板块固定操作

`docs/社交/` 有固定的维护流程，按操作类型分四类：

### 1. 每日日记（`docs/社交/AI评估/日记/`）

每条 `docs/社交/AI评估/日记/<YYYY-MM-DD>.md` 格式固定（详见 `.agents/skills/diary/SKILL.md`）：
`# YYYY-MM-DD 日记` → `## 总结`（口语化、具体、有细节）→ `## 计划` → `## 待跟进`。

日记有两个来源，殊途同归：
- **chat-analyzer 自动生成**（从真实聊天记录分析，见下节）
- **`/diary` 技能手写**（用户口头叙述 → 按 diary SKILL 撰写）

**写入后固定三步**（新日期必做，缺一不可）：
1. 新建/更新 `docs/社交/AI评估/日记/<YYYY-MM-DD>.md`
2. 追加 `docs/社交/AI评估/日记/index.md`：`- [MM-DD](YYYY-MM-DD.md)`（按日期升序）
3. 追加 `mkdocs.yml`「社交 → AI评估 → 日记」列表：`- MM-DD: 社交/AI评估/日记/YYYY-MM-DD.md`

### 2. chat-analyzer 分析流水线（`chat-analyzer/`）

从聊天记录批量生成评估报告，命令在 `chat-analyzer/` 目录执行：

1. WeChatMsg 导出聊天记录 → `data/chat_logs/raw/<日期>.txt`（该目录 gitignored）
2. 全流程：`python main.py --date YYYY-MM-DD`（parse → summarize → evaluate → portrait，中间产物在 `output/`）
3. 发布到站点：`python main.py export`（默认写入 `../docs/社交/AI评估/`，覆盖 README/评分总表/人物画像/待跟进/阶段分析，并复制 `output/diary/` 到 `日记/`）
4. 常用变体：`--all` 批量所有日期（自动跳过已处理）、`--force` 强制重跑、`--dry` 预览不写、`report` 长期趋势、`stage` 阶段分析、`html` HTML 综合报告、`portrait-show` 查看画像、`dedup` 画像去重、`stats` 每日统计
5. 配置 `config.yaml` 内含 DeepSeek API key（gitignored），可用环境变量 `DEEPSEEK_API_KEY` 替代

> ⚠️ `export` 会用 `output/` 覆盖 `docs/社交/AI评估/` 下同名文件（含 `日记/`）；若站内有人工润色内容需先备份，或在 export 后重新应用。`export` 不会生成 `日记/index.md`（手工维护，见上）。

### 3. 长文日记（`docs/社交/第0段记录.md`）

人工撰写、持续追加，非 AI 生成，无固定格式约束。

### 4. 每次改动后

涉及社交板块的增删改，均需 `mkdocs build` 通过后再提交（nav 手工维护，新文件必须登记）。

## 持续内容补充工作流（content-supplement-loop）

文档库最常见的重复性任务：按轮次为某个栏目撰写原创内容并提交（git 历史中大量 `chore: 持续补充 <栏目>` commit 即此流程产出）。

- **轮转顺序**：制作项目 → 知识库 → 创业 → 游戏 → 音乐 → 剧本 → 健身 → 小屋装修。用 `git log --format=%s` 查最近一条 `chore: 持续补充` commit 判断做到哪，做下一个。
- **内容风格**：写有实质内容的原创文档（技术解析、方案设计、方法指南、流程路线），并给出明确项目推荐——推荐做什么、为什么值得做、怎么做、产出什么。开源项目只作支撑论据和参考来源（标注真实 URL），不要只堆 star 列表。
- **每轮约定**：新建文件须同步 `mkdocs.yml` nav；**每轮独立 `mkdocs build` 通过后单独 commit**（即使连跑多轮也逐轮 build+commit，不得整批最后才 build——否则 nav 指向未提交文档会导致中间 commit 构建不过）；commit 消息 `chore: 持续补充 <栏目> <简述>`，**不 push**。
- **不碰** `docs/社交/`、`docs/行动记录/`、`data/`、`chat-analyzer/`。该轮无有价值新内容时写"本期无更新"并说明原因，不硬凑。
- ⚠️ 主循环已于 2026-08-06 暂停；若用户要求重启，按上述约定恢复即可。

## 健身数据后端（api_server.py）

- FastAPI 服务，为健身页面提供数据读写/导出/照片上传接口；数据存于 `data/` 下的 JSON（`training_records.json`、`body_metrics.json`、`photo_meta.json` + `photos/`）。
- 运行：`uvicorn api_server:app`（fastapi/uvicorn 全局安装，未列入 requirements.txt）。

## 独立子项目

- `chat-analyzer/` — 聊天记录评估系统（独立 Python 项目，与 MkDocs 站点无关），将 WeChatMsg 导出的聊天记录解析、评估并生成 `docs/社交/AI评估/` 下的报告。完整操作流程见「社交板块固定操作」第 2 节；配置与 API key 说明同节。

## Claude Code 技能

- 技能源码位于 `.agents/skills/`，通过符号链接暴露到 `.claude/skills/`（新增技能需两处都配置）。
- 自定义技能：
  - `diary` — 写日记（见上，有严格的文件/索引/nav 流程）
  - `article-review` — 通用文章审查（博客、日记、笔记、技术文档等非小说内容）
- 第三方技能（来源记录在 `skills-lock.json`）：`novel-assistant`、`novel-review`（网文写作与章节审稿）。

## 内容审查约定

- 审查/审稿/校对类请求：非小说内容用 `article-review` 技能，小说章节用 `novel-review`。
- 审查报告按 Red（致命）/Yellow（重要）/Green（优化）三级输出，必须引用原文片段定位问题，并给出可操作修改建议；审查只出报告、不直接修改原文。
