# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

个人技术文档库（Minke的技术文档库），基于 MkDocs + Material for MkDocs 构建，内容以中文为主，涵盖嵌入式开发、电机控制、AUTOSAR、游戏自动化等技术领域，以及社交/日记等个人内容。推送到 `main` 分支后由 GitHub Actions（`.github/workflows/deploy.yml`）自动构建并部署到 GitHub Pages（https://minkelxy.github.io/MinkeWiki/）。

## 常用命令

```bash
pip install -r requirements.txt   # 安装依赖（mkdocs、mkdocs-material 等）
mkdocs serve                      # 本地开发服务器，热重载，访问 http://localhost:8000
mkdocs build                      # 构建静态站点到 site/（gitignored）
```

- `site/` 已 gitignore，构建产物无需提交。
- **`requirements.txt` 不完整**：`mkdocs.yml` 用到的 `mkdocs-encryptcontent-plugin`、`mkdocs-git-revision-date-localized-plugin`、`mkdocs-redirects` 均为全局安装、未列入 requirements。若全新环境 build 报缺插件，需单独安装这几个包。
- 部署自动触发，无需手动操作。每晚 23:47 cron 运行 `scripts/auto_backup.sh`：自动 git 提交（`auto: daily backup YYYY-MM-DD`）并尝试 push，周日额外生成 tar 快照到 `/home/minke/backup/`（保留最近 4 份）。

## 内容架构

- `docs/` 为站点内容源，按中文分类目录组织（`知识/`、`制作/`、`社交/`、`健身/`、`创业/`、`游戏/`、`音乐/`、`剧本/` 等）。
- **`mkdocs.yml` 的 `nav` 为手工维护**：新增/删除文档必须同步更新 nav 条目，否则不会出现在站点导航中。「社交 → AI评估 → 日记」下是每天一篇的列表，需逐条追加。
- 插件约定：`encryptcontent` 支持页面加密（加密页不进入明文搜索索引）；`blog` 插件管理 `blog/` 目录；`tags` 插件依赖 `docs/tags.md` 标签页。
- **`docs/社交/` 是目前最活跃、持续维护的部分**：
  - `第0段记录.md` — 长文日记（正在持续撰写，非 AI 生成）
  - `AI评估/日记/<YYYY-MM-DD>.md` — 每日 AI 生成的日记，配套 `AI评估/日记/index.md` 索引，以及评分总表、人物画像、待跟进、阶段分析等报告
  - 每日日记的完整写入/更新流程见 `.agents/skills/diary/SKILL.md`（新建文件 → 按格式撰写 → 追加 index.md → 更新 mkdocs.yml nav）

## 健身数据后端（api_server.py）

- FastAPI 服务，为健身页面提供数据读写/导出/照片上传接口；数据存于 `data/` 下的 JSON（`training_records.json`、`body_metrics.json`、`photo_meta.json` + `photos/`）。
- 运行：`uvicorn api_server:app`（fastapi/uvicorn 全局安装，未列入 requirements.txt）。

## 独立子项目

- `chat-analyzer/` — 聊天记录评估系统（独立 Python 项目，与 MkDocs 站点无关）。将 WeChatMsg 导出的聊天记录解析、评估，生成 `docs/社交/AI评估/` 下的报告。使用方式见 `main.py` 顶部注释（`python main.py --date YYYY-MM-DD`、`--dry`、`--report`）。`config.yaml` 内含 DeepSeek API key 且已 gitignore，可用环境变量 `DEEPSEEK_API_KEY` 替代。

## Claude Code 技能

- 技能源码位于 `.agents/skills/`，通过符号链接暴露到 `.claude/skills/`（新增技能需两处都配置）。
- 自定义技能：
  - `diary` — 写日记（见上，有严格的文件/索引/nav 流程）
  - `article-review` — 通用文章审查（博客、日记、笔记、技术文档等非小说内容）
- 第三方技能（来源记录在 `skills-lock.json`）：`novel-assistant`、`novel-review`（网文写作与章节审稿）。

## 内容审查约定

- 审查/审稿/校对类请求：非小说内容用 `article-review` 技能，小说章节用 `novel-review`。
- 审查报告按 Red（致命）/Yellow（重要）/Green（优化）三级输出，必须引用原文片段定位问题，并给出可操作修改建议；审查只出报告、不直接修改原文。
