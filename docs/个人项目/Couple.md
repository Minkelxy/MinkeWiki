# 桌面情侣套件 Couple

一款常驻系统托盘的桌面伴侣应用，集相册轮播、信箱、打卡日历、影视看板、旅行地图、五子棋于一体。支持双机局域网/云中转同步，让两台电脑像在身边一样。

- **仓库**：[github.com/Minkelxy/Couple](https://github.com/Minkelxy/Couple)
- **语言**：Python
- **平台**：Windows 10/11

---

## 功能一览

| 模块 | 说明 |
|------|------|
| 桌面相册 | 透明置顶窗口轮播照片，支持拍立得边框、日期水印、Ken Burns 动画、模糊背景填充、滚轮缩放、双击重置 |
| 画廊浏览 | 网格浏览所有相册，右键共享当前相册给对方 |
| 信箱 | 写信、延时投递、收件箱、附件加密存储（Fernet），支持纪念日自动提醒 |
| 打卡日历 | 月历打卡、心情曲线、连续打卡统计、对方打卡侧栏 |
| 影视看板 | 豆瓣抓取海报/简介、评分记录、对比报告（可选 Playwright 抓取） |
| 旅行地图 | 中国省级边界离线地图（DataV GeoJSON）、城市标记、足迹图层、对方共享 |
| 五子棋 | 双人对战、悔棋、同步走子 |
| 想你了 | 一键向对方发送心跳通知 |

## 同步机制

- **双机局域网 / 云中转**双通道同步
- 附件加密存储：`Fernet` 对称加密
- 邮箱/信箱内容加密，双机互传不落地明文

## 技术栈

- Python 3.10+
- GUI：PySide6
- 图像：Pillow
- 加密：cryptography（Fernet）
- 图表：matplotlib

## 开发与打包

```bash
# 开发运行
pip install PySide6 Pillow cryptography matplotlib
python launcher.py

# 打包（PyInstaller）
pip install pyinstaller
python -m PyInstaller couple_suite.spec --noconfirm
```

首次运行会弹出引导窗口，设置昵称、照片目录，可选开启同步。

---

## 🔗 相关链接

- [个人项目目录](目录.md)
- [GitHub项目索引](../GitHub项目索引.md)

---

*文档版本：v1.0*
*创建日期：2026-08-05*
*内容来源：仓库 README*
