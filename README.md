# Minke的技术文档库

基于 [MkDocs](https://www.mkdocs.org/) + [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) 构建的个人技术文档网站，涵盖嵌入式开发、电机控制、AUTOSAR、游戏自动化等领域。

🌐 在线访问: [https://minkelxy.github.io/MinkeWiki/](https://minkelxy.github.io/MinkeWiki/)

---

## 本地开发

### 环境要求

- Python 3.x
- pip

### 安装与运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动本地开发服务器（支持热重载）
mkdocs serve
```

访问 http://localhost:8000 查看文档。

### 构建静态站点

```bash
mkdocs build
```

构建产物输出到 `site/` 目录。

---

## 项目结构

```
myMarkdown/
├── docs/                  # Markdown 源文件
│   ├── index.md           # 首页
│   ├── 知识/               # 技术知识库 (8个分类, 21篇)
│   ├── 制作/               # 制作项目文档 (5个子项目)
│   ├── 创业/               # 创业相关 (农业+抖音直播)
│   ├── 游戏/               # 游戏相关
│   ├── 音乐/               # 音乐创作
│   └── 剧本/               # 剧本创作
├── mkdocs.yml             # MkDocs 配置文件
├── requirements.txt       # Python 依赖
├── .gitignore             # Git 忽略配置
├── .github/workflows/     # GitHub Actions 自动部署
└── site/                  # 构建产物 (已忽略, 不提交到 Git)
```

---

## 主题特性

使用 **Material for MkDocs** 主题，支持：

- 🌓 亮色/暗色模式切换
- 🔍 全文搜索（支持中文分词）
- 📋 代码块一键复制
- 📱 响应式布局（适配移动端）
- 🧭 标签页导航 + 侧边栏展开

---

## 自动部署

推送到 `main` 分支后，GitHub Actions 会自动：

1. 安装 Python 依赖
2. 执行 `mkdocs build` 构建静态站点
3. 部署到 GitHub Pages

工作流配置见 [.github/workflows/deploy.yml](.github/workflows/deploy.yml)。

---

## 内容统计

| 分类 | 文档数 |
|------|--------|
| 知识库 | 8个分类, 21篇文档 |
| 制作项目 | 5个子项目, 28个文档 |
| 创业 | 农业信息 + 抖音直播 |
| 游戏 | 3篇 |
| 音乐 | 1篇 |
| 剧本 | 1篇 |

---

## 许可证

[MIT License](LICENSE)
