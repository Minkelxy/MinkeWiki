# 部署到GitHub

以下是如何将您的MkDocs文档站点部署到GitHub的详细步骤：

## 1. 创建GitHub仓库

1. 登录到GitHub
2. 点击"New"创建新仓库
3. 仓库名称可以是`your-username.github.io`（用于用户页面）或任何其他名称（用于项目页面）
4. 将仓库设置为Public
5. 不要初始化仓库（不添加README、.gitignore或license）

## 2. 将本地项目推送到GitHub

如果您还没有本地git仓库，请初始化并添加远程仓库：

```bash
# 初始化git仓库（如果还没有的话）
git init

# 添加所有文件
git add .

# 提交更改
git commit -m "Initial commit"

# 添加远程仓库（替换为您创建的仓库URL）
git remote add origin https://github.com/your-username/your-repo-name.git

# 推送到GitHub
git branch -M main
git push -u origin main
```

## 3. 启用GitHub Pages

1. 转到您的GitHub仓库
2. 点击仓库页面上的"Settings"选项卡
3. 在左侧菜单中选择"Pages"
4. 在"Source"部分，从下拉菜单中选择"GitHub Actions"
   - 注意：如果使用上述工作流，构建后的页面将自动从gh-pages分支提供服务

## 4. 自定义mkdocs.yml（可选）

如果您使用非用户名的仓库名，可能需要在mkdocs.yml中添加以下配置：

```yaml
site_url: https://your-username.github.io/your-repo-name/
```

## 5. 自定义域名（可选）

如果您想使用自定义域名：

1. 在您的域名提供商处设置DNS记录指向GitHub Pages
2. 在mkdocs.yml中添加：
   ```yaml
   extra:
     homepage: https://yourdomain.com
   ```
3. 在仓库的Settings → Pages中设置自定义域名

## 6. 工作流说明

此项目包含一个GitHub Actions工作流，将自动：
- 在每次推送到main分支时构建MkDocs站点
- 将构建的静态文件部署到GitHub Pages
- 网站将在几分钟后通过GitHub Pages URL可用

## 验证部署

1. 在GitHub仓库中，转到"Actions"标签页，确认工作流正在运行且无错误
2. 转到"Settings" → "Pages"，查看部署状态
3. 访问 `https://your-username.github.io/your-repo-name` 查看您的文档站点

## 故障排除

- 如果页面没有正确构建，请检查Actions工作流日志
- 确保所有依赖项在requirements.txt中正确列出
- 检查mkdocs.yml配置是否正确