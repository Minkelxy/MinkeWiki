# 我的文档站

这是一个使用MkDocs构建的文档网站。

## 本地开发

1. 确保已安装Python和MkDocs
2. 在项目目录运行:
   ```bash
   pip install mkdocs
   mkdocs serve
   ```
3. 访问 http://localhost:8000 查看文档

## 项目结构

- `/docs` - Markdown源文件
- `mkdocs.yml` - MkDocs配置文件
- `/site` - 生成的静态网站文件

## 部署到GitHub Pages

网站将通过GitHub Actions自动部署。