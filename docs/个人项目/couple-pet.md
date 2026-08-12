---
tags:
  - 个人项目
---

# 双人共享桌宠 couple-pet

基于 OpenPets 的**双人共享桌宠**——不是另一套桌宠壳，而是 OpenPets 的扩展层：真实猫猫角色 + 双人房间/共享状态/离线事件/传话/礼物/共同成长。

- **仓库**：[github.com/Minkelxy/couple-pet](https://github.com/Minkelxy/couple-pet)
- **语言**：JavaScript（Node.js）
- **依赖**：OpenPets 3.x（manifest v3 / SDK 3.0.0）

---

## 架构

```text
OpenPets 桌面应用
├─ 团团 pet package（8×9 标准 spritesheet）
└─ openpets.shared-pet（SDK v3 插件）
   └─ HTTPS → shared-pet 同步服务
```

- **OpenPets** 负责：透明窗口、置顶、拖动、鼠标穿透、托盘、多显示器、缩放、宠物渲染、插件沙箱
- **本项目实现**：团团角色包 + 双人共享（房间、状态、离线事件、传话、礼物、共同成长）

## 目录结构

| 路径 | 说明 |
|------|------|
| `openpets/plugins/openpets.shared-pet/` | OpenPets Developer Mode 直接加载的插件 |
| `openpets/pets/tuan-tuan/` | 可通过 OpenPets CLI 安装的宠物包 |
| `apps/server/` | 云端权威状态服务（仅 Node.js 内置模块） |
| `scripts/build_spritesheet.py` | 把透明猫猫源图生成 OpenPets 固定 192×208、8×9 spritesheet |
| `scripts/prepare-openpets.mjs` | 把插件和宠物包覆盖到 OpenPets 源码 checkout |
| `img/` | 用户提供的真实猫猫日常参考图 |

## 本地端到端运行

要求 Node.js 20+、OpenPets 3.x：

```powershell
# 1. 启动同步服务
node apps/server/index.js

# 2. OpenPets → Plugins → Developer Mode → Load unpacked plugin folder
#    选择 openpets/plugins/openpets.shared-pet
```

---

## 🔗 相关链接

- [个人项目目录](README.md)
- [GitHub项目索引](../GitHub项目索引.md)

---

*文档版本：v1.0*
*创建日期：2026-08-05*
*内容来源：仓库 README*
