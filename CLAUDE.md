# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

`myMarkdown` 是一个中文优先的个人文档站，使用 MkDocs + Material for MkDocs 构建，在线站点为 <https://minkelxy.github.io/MinkeWiki/>。仓库同时包含两个与文档站配套的本地程序：

- **文档站**：`docs/` 是 Markdown、图片、样式和博客源文件，`mkdocs.yml` 是站点配置，`site/` 是构建产物并被 Git 忽略。内容按技术、创作、生活、事业等栏目组织。
- **聊天分析器**：`chat-analyzer/` 是独立的 Python CLI。它读取 WeChatMsg 导出的聊天记录，经过解析、总结、评分、人物画像和阶段分析后，把 Markdown 报告导出到 `docs/社交/AI评估/`。
- **健身 API**：根目录 `api_server.py` 是 FastAPI 应用，读写 `data/` 下的训练、身体指标和照片元数据；`docs/健身/` 页面内嵌了对应的前端脚本。

没有发现 Cursor 或 Copilot 规则文件。仓库级约束以本文件、`README.md`、`mkdocs.yml`、`.github/workflows/deploy.yml` 和相关技能文件为准。

## 常用命令

命令默认从仓库根目录执行；使用 Python 3.10+。

### MkDocs 文档站

```bash
python3 -m pip install -r requirements.txt
# 本地构建社交页面前创建 .mkdocs-passwords.yml；CI 使用 MKDOCS_SOCIAL_PASSWORD Secret
mkdocs serve                         # http://localhost:8000
mkdocs build                         # 构建到 site/
mkdocs build --strict                # 警告即失败（当前会被密码熵警告触发）
```

`mkdocs.yml` 通过 `.mkdocs-passwords.yml` 读取社交页面密码；该文件被 Git 忽略，不能提交。首次本地构建前创建它，例如 `printf "social: '你的密码'\\n" > .mkdocs-passwords.yml`。GitHub Actions 需要配置 `MKDOCS_SOCIAL_PASSWORD` Secret，workflow 会在构建时生成临时密码文件。密码保护只作用于生成的站点，原始 Markdown 仍必须按私密资料处理。

仓库没有独立的 lint 配置或 Makefile。修改 Markdown、导航或 MkDocs 配置后至少运行 `mkdocs build`。`mkdocs build --strict` 当前会因 mkdocs-encryptcontent-plugin 的密码熵警告（`WARNING`）而中止，未登记页面只会以 INFO 列出；提高 `.mkdocs-passwords.yml` 中的密码强度可消除该警告。GitHub Actions 的部署工作流运行的是非 strict 的 `mkdocs build`。新增普通页面时应登记到 `mkdocs.yml` 的 `nav`，明确不展示的页面才加入 `not_in_nav`。博客文章由 blog 插件发现，社交页面使用 `level: social` 加密，日记日期仍需维护索引和导航。

### 聊天分析器

```bash
cd chat-analyzer
python3 -m pip install -r requirements.txt pytest
python3 -m pytest tests                              # 全部测试
python3 -m pytest tests/test_parser.py -v            # 单文件
python3 -m pytest tests/test_parser.py::test_parse_iso_format -v
python3 -m compileall -q main.py modules              # 快速语法检查
python3 main.py --date YYYY-MM-DD                    # parse → summarize → eval → portrait
python3 main.py --date YYYY-MM-DD parse
python3 main.py --date YYYY-MM-DD eval
python3 main.py report                               # 长期趋势报告
python3 main.py export --target ../docs/社交/AI评估
```

`config.yaml` 被 `chat-analyzer/.gitignore` 忽略，首次使用需要在 `chat-analyzer/` 创建本地配置，至少提供联系人、`paths`、API 配置、评分权重和提醒阈值；配置中的相对路径相对于配置文件所在目录解析。API key 可放在本地配置，或留空后通过 `DEEPSEEK_API_KEY` 提供。不要把配置、原始聊天记录或 `data/`、`output/` 生成物加入 Git。注意仓库历史中已跟踪 `chat-analyzer/single_*.json`（WeChatMsg 原始导出，含 wxid 和聊天原文）；不要新增此类文件，处理时按私密资料对待。

`main.py` 的其他子命令包括 `portrait`、`portrait-show`、`dedup`、`stats`、`html` 和 `stage`；全局参数包括 `--date`、`--all`、`--force`、`--dry`、`--config`，它们必须放在子命令之前（`export --target` 这类子命令自有参数除外）。`summarize` 不是可调用的子命令。`report` 生成长期趋势报告（`Reporter`），`html` 生成综合 HTML 报告（`ReportGenerator`）。`--all` 会增量跳过已有评分的日期，处理后自动生成 HTML 并导出；使用 `--force` 才会重跑已有日期的 summarize/eval/portrait，但 `parse` 对已存在的 `parsed/<日期>.json` 总是跳过，需要手动删除解析文件才能重新解析。`--dry` 只被 summarize、portrait、stage、report 等部分路径检查，`parse` 和 `eval` 仍会写文件，`--all` 末尾的 HTML 生成与导出也仍会执行，不能把它当作全流程只读预览。`export` 的相对 `--target`（含默认值 `../docs/社交/AI评估`）由 `MdExporter` 相对于配置文件所在目录解析，因此在 `chat-analyzer/` 下用默认配置运行就指向 `docs/社交/AI评估`；但 `--config` 本身默认是相对当前工作目录的 `config.yaml`，所以仍应 `cd chat-analyzer` 或显式传 `--config`。导出会覆盖目标目录中的同名报告和日记，但不会维护 `日记/index.md` 或导航。

测试目前只覆盖 `chat-analyzer/modules/parser.py` 的 3 个用例，API 没有自动化测试。聊天分析器的运行依赖在 `chat-analyzer/requirements.txt`（测试还需单独安装 `pytest`），健身 API 的依赖不在其中；不要假定根 `requirements.txt` 已安装它们。

### 健身 API

API 运行依赖 FastAPI、Uvicorn 和文件上传所需的 `python-multipart`，这些不在根依赖文件中：

```bash
python3 -m pip install fastapi uvicorn python-multipart
python3 -m uvicorn api_server:app --reload --host 127.0.0.1 --port 8001
```

后端路由是 `/fitness/*`（`/fitness/training-records`、`/fitness/body-metrics`、`/fitness/photos`、`/fitness/export/...`）。`docs/健身/` 页面的 `data-api-base` 默认为空，脚本中 `apiEnabled = Boolean(API)`；为空时页面只读并显示本地提示，不会发出请求。要启用读写，把 `data-api-base` 设为服务基址（例如 `http://127.0.0.1:8001/fitness`，或反向代理到该前缀）。仅启动 Uvicorn 不会自动提供 `/api` 或根路径别名。API 无鉴权、CORS 对全部来源开放，默认只应在受信任的本机/内网运行，不能直接暴露到公网。接口会直接写入被 Git 跟踪的 `data/*.json`，上传还会创建 `data/photos/<年>/<月>/`；操作后检查工作树，避免把运行数据或照片随意提交。

## 代码与数据流

### 文档站

`mkdocs.yml` 的 `nav` 是手工维护的站点信息架构，不能依赖文件自动发现。栏目入口优先使用 `README.md` 或 `index.md`。新增、重命名或删除普通页面时同步修改 `nav`；旧栏目入口的兼容路径还要检查 `redirect_maps`。文档 frontmatter 中的 `tags` 由 tags 插件汇总到 `docs/tags.md`。`docs/社交/` 下的页面（含 `README.md`、`AI评估/*` 和每篇日记）需要在 frontmatter 写 `level: social` 才会被 encryptcontent 加密，新增社交页面不要漏掉。

`docs/blog/` 由 Material blog 插件管理，文章作者定义在 `docs/blog/.authors.yml`，不要把博客文章逐篇复制进普通栏目导航。Mermaid 使用 `pymdownx.superfences` 的自定义 fence 和 `extra_javascript` 中的 CDN，不要假设启用了 `mermaid2`。原始 HTML 中的 `<a href>` 不会经过 MkDocs 链接转换，首页卡片等 HTML 链接必须写渲染后的 URL；Markdown 链接才会自动转换。

内嵌 ECharts 常见于健身页面和 AI 评估报告。图表放在隐藏 tab 中时，切换显示后调用 `chart.resize()`；时间序列数据先按日期排序。

修改 `docs/社交/` 或 `mkdocs.yml` 后运行 `mkdocs build`。新日记的固定维护步骤是：

1. 创建或更新 `docs/社交/AI评估/日记/YYYY-MM-DD.md`；
2. 按日期升序在 `日记/index.md` 添加 `- [MM-DD](YYYY-MM-DD.md)`；
3. 按当前 `mkdocs.yml` 的实际结构，在日记导航中添加新日期条目。

`.agents/skills/diary/SKILL.md` 中关于导航的描述曾与当前配置不一致，以仓库现状和本文件为准。

### 聊天分析器流水线

1. 将 WeChatMsg 导出文件放入配置指定的 `chat-analyzer/data/chat_logs/raw/`。
2. `parse` 生成 `data/chat_logs/parsed/<日期>.json`；已有解析文件会跳过，日期分界由 `day_boundary` 控制，默认凌晨 4 点。
3. summarizer、evaluator、portrait、stage_analyzer 等模块写入 `chat-analyzer/output/`，包括评分、日记、画像、待跟进和阶段报告。
4. `MdExporter` 把固定名称的 README、评分总表、人物画像、待跟进、阶段分析和日记复制/生成到 `docs/社交/AI评估/`。

主要模块与产物：

| 模块 | 产物 |
|------|------|
| `parser.py` | `data/chat_logs/parsed/<日期>.json` |
| `summarizer.py` | `output/diary/<日期>.md`、`output/todos.json` |
| `evaluator.py` | `output/scores.json` |
| `portrait.py` | `output/portrait.md` |
| `stage_analyzer.py` | `output/stage_report_<时间戳>.md` |
| `reporter.py` | `output/report_<YYYYMMDD>.md`（`report` 子命令） |
| `report_generator.py` | `output/full_report_<时间戳>.html`（`html` 子命令） |
| `md_exporter.py` | `docs/社交/AI评估/` 下的固定报告与日记 |

`main.py` 负责 CLI 编排，具体能力分散在 `chat-analyzer/modules/`；提示词在 `chat-analyzer/prompts/`。修改导出文件名、字段或报告格式时，同时检查 `mkdocs.yml` 导航、日记索引和站点页面。

### 健身 API 数据约定

`api_server.py` 使用 Pydantic 模型定义训练记录和身体指标。训练记录是追加写入；同一日期的身体指标 POST 会替换旧记录；ID 由服务端生成。照片上传只接受图片且不超过 10 MB，照片读取会校验路径，导出支持带 UTF-8 BOM 的 CSV 和 JSON。修改模型或接口时，同时检查 `docs/健身/` 的内嵌 JavaScript、JSON 数据格式和导出行为。

## 内容导航与日记

- 顶层导航为首页、标签、GitHub 项目索引，以及技术、创作、生活、事业四大栏目。
- `docs/行动记录/` 使用有语义的文件名，新增记录需登记导航；`_模板.md` 等明确不发布的文件放入 `not_in_nav`。
- 日记内容遵循现有的 `总结`、`计划`、`待跟进` 结构。日记技能和文章审查技能的具体格式、审核分级及输出要求分别见 `.agents/skills/diary/SKILL.md` 和 `.agents/skills/article-review/SKILL.md`。
- 审查/审稿类请求默认只生成报告，不直接改写原文；小说章节使用 `novel-review`，非小说内容使用 `article-review`。

## Claude Code 技能与自动化

技能源码在 `.agents/skills/`，`.claude/skills/` 下的同名项是符号链接。`diary`、`article-review` 是本仓库技能；`human-writing`、`novel-assistant`、`novel-review` 的来源和哈希记录在 `skills-lock.json`。修改第三方技能时注意会造成锁文件漂移。

`scripts/auto_backup.sh` 是本机专用脚本，硬编码 `/home/minke/myMarkdown`，会 `git add -A`、自动提交并尝试推送 `main`，周日还会生成备份压缩包。除非用户明确要求，不要运行它：它可能把生成数据或本地文件一起暂存/提交，且脚本日志 `scripts/backup.log` 本身会留下工作树改动。部署应以 `.github/workflows/deploy.yml` 为准，推送 `main` 后由 GitHub Actions 构建并发布 GitHub Pages；`deploy-to-github.md` 是旧的通用说明，不要把它当作当前部署流程。
