# Minke的技术文档库

基于 [MkDocs](https://www.mkdocs.org/) + [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) 的个人技术文档站，涵盖嵌入式开发、电机控制、AUTOSAR、游戏自动化，以及音乐、剧本、健身、社交等个人内容。

🌐 在线访问: [https://minkelxy.github.io/MinkeWiki/](https://minkelxy.github.io/MinkeWiki/)

## 本地开发

```bash
pip install -r requirements.txt   # 安装依赖
mkdocs serve                      # 本地预览 http://localhost:8000
mkdocs build                      # 构建静态站点到 site/
```

## 目录结构

- `docs/` — 站点内容源，按栏目组织（知识 / 制作 / 游戏 / 音乐 / 剧本 / 观影 / 视频 / 博客 / 社交 / 行动记录 / 健身 / 创业 / 小屋装修 / 个人项目）
- `mkdocs.yml` — 站点配置；`nav` 为手工维护，新增文档需登记
- `site/` — 构建产物（gitignored）
- `scripts/auto_backup.sh` — 每晚自动提交并尝试推送

## 部署

推送到 `main` 分支后，GitHub Actions 自动构建并部署到 GitHub Pages。

## 许可证

[MIT License](LICENSE)
