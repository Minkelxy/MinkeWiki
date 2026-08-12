---
tags:
  - 游戏
---

# YOLO 训练实战

教你**训练一个自己的游戏目标检测模型**（识别血条、敌人、可拾取物等动态目标），从采数据到部署到[游戏自动化技术基础](游戏自动化技术基础.md)的管线里。

---

## 一、什么时候该上 YOLO（而不是模板匹配）

| 场景 | 用哪个 |
|------|--------|
| 固定图标/UI/按钮 | **模板匹配**（`cv2.matchTemplate`），不用训练 |
| 动态、多形态目标（敌人/血条/可拾取物） | **YOLO**，泛化能力强 |

> 判断标准：目标会变（大小/角度/部分遮挡）就用 YOLO；一成不变用模板。

## 二、完整流程

```
数据采集 → 标注 → 训练 → 验证 → 部署
```

## 三、数据采集（最耗时，别省）

- 从游戏**录屏抽帧**（每 2-5 秒一帧，覆盖不同场景/光照/角色状态）
- 每个目标类**至少 300 张**起步，越多越好
- 覆盖困难情况：远距离（小目标）、部分遮挡、不同地图

## 四、标注（labelImg）

- 工具：[HumanSignal/labelImg](https://github.com/HumanSignal/labelImg)（已验证 ★25k）
- 用矩形框框出目标，标注类别
- 导出格式选 **YOLO**：每个目标一行 `class x_center y_center w h`（归一化坐标）

目录结构（关键）：

```
dataset/
├── images/
│   ├── train/   （约 80% 图片）
│   └── val/     （约 20%）
├── labels/
│   ├── train/   （与 images 同名 .txt）
│   └── val/
└── data.yaml    （类别定义）
```

`data.yaml` 示例：

```yaml
path: dataset
train: images/train
val: images/val
names:
  0: enemy
  1: hp_bar
  2: pickup
```

## 五、训练（Ultralytics YOLO）

工具：[ultralytics/ultralytics](https://github.com/ultralytics/ultralytics)（已验证 ★60k）

```bash
pip install ultralytics
yolo detect train data=dataset/data.yaml model=yolo11n.pt epochs=100 imgsz=640 batch=8
```

| 参数 | 建议 | 说明 |
|------|------|------|
| `model` | `yolo11n.pt`（nano 起步） | 小模型快，游戏场景够用 |
| `epochs` | 100 | 数据少可减到 50 |
| `imgsz` | 640 | 训练尺寸 |
| `batch` | 显存允许尽量大 | 8-16 |

> 没 GPU 可先用 `yolo11n` 小模型在 CPU 慢训，或用云 GPU（Colab）。

## 六、验证与导出

- 训练完看 `runs/detect/train/` 里的 **混淆矩阵 / mAP**：每类 AP>0.7 算不错
- 导出/直接推理：

```bash
yolo detect predict model=runs/detect/train/weights/best.pt source=截图.jpg
```

- 要接其他框架可导出 ONNX：`yolo export model=best.pt format=onnx`

## 七、部署到游戏自动化

接进[技术基础](游戏自动化技术基础.md)的管线：

```
每 N 帧截图 → YOLO 推理（得到框/类别/置信度）→ 取最高置信目标
→ 中心点换算屏幕坐标 → 坐标映射 → 输入注入
```

- 帧率：检测 10-15 FPS 足够，别每帧都跑
- 加**置信度阈值**（如 0.6）过滤误检；同一目标加简单跟踪（上一帧位置附近优先）减少抖动

## 八、注意事项

- 标注质量 > 数量：框歪了宁可少一张
- 类别别太细（敌人分 3 类就好），越细越难训
- **合规**：游戏自动化涉及服务条款与反作弊，仅在合规场景使用（见[技术基础](游戏自动化技术基础.md)）

---

## 🔗 相关链接

- [游戏自动化技术基础](游戏自动化技术基础.md)
- [游戏自动化开源参考](游戏自动化开源参考.md)
- [逆战未来](逆战未来/逆战未来.md)

---

*文档版本：v1.0*
*创建日期：2026-08-05*
