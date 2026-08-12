---
tags:
  - 音乐
---

# MIDI 基础与电子音乐

MIDI（Musical Instrument Digital Interface，乐器数字接口）是电子乐器、电脑与硬件之间的标准通信协议。理解 MIDI 是玩转[电子琴/MIDI音源等制作项目](../制作/README.md)和[词谱改编](词谱/传达不到的爱恋改编.md)的基础。

---

## 一、MIDI 是什么

MIDI 传输的是**演奏指令**（音符、力度、音色切换），而不是音频信号本身。它不发出声音，只是告诉设备「什么时候、用多大力度、弹哪个音」。

- 诞生：1983 年，5 针 DIN 接口
- 现代接口：USB-MIDI、蓝牙 MIDI（无线）
- 一条 MIDI 链路可串联/并联多个设备

## 二、消息结构

每条 MIDI 消息由**状态字节**（标志类型）+ **数据字节**（参数）组成：

```
状态字节(0x80-0xFF) + 数据字节(0x00-0x7F)...
```

两类消息：
- **通道消息**（Channel Message）：发给指定通道的设备
- **系统消息**（System Message）：发给全部设备（时钟、SysEx 等）

## 三、通道消息

MIDI 共 **16 个通道**（0-15），同一条链路可同时承载 16 路乐器。

### 音符开关

| 消息 | 十六进制 | 数据 | 说明 |
|------|---------|------|------|
| Note Off | `0x8n` | 音符号 + 力度 | 松键 |
| Note On | `0x9n` | 音符号 + 力度 | 按下 |

- **音符号 0-127**：中央 C（C4）= 60，标准音 A4 = 69（440Hz）
- **力度（Velocity）0-127**：控制音量/触感

### 控制与音色

| 消息 | 十六进制 | 数据 | 典型用途 |
|------|---------|------|---------|
| Control Change | `0xBn` | CC号 + 数值 | CC1=调制、CC7=音量、CC64=延音踏板 |
| Program Change | `0xCn` | 音色号 | 切换乐器音色 |
| Pitch Bend | `0xEn` | 14位弯音值 | 弯音轮 |

## 四、系统消息

| 类型 | 起始字节 | 用途 |
|------|---------|------|
| 系统专属（SysEx） | `0xF0` | 厂商私有协议、音色包上传 |
| 系统实时（Realtime） | `0xF8`起 | MIDI 时钟（节拍同步）、Start/Stop |

**MIDI 时钟**：`0xF8` 每拍发 24 次，用于多设备节拍同步（编曲/灯光联动常用）。

## 五、音序与制作概念

- **音序器（Sequencer）**：记录/回放 MIDI 指令，DAW 的核心
- **音源（Sound Module / Synth）**：把 MIDI 指令转成声音的引擎
- **通道对应乐器**：软件里通常把 16 通道对应 16 轨乐器

一条典型流程：DAW 里录 MIDI → 编辑音符 → 选择音源（软件合成器/硬件音源）→ 渲染出音频。

## 六、Python 实操

| 开源项目 | Star | 说明 |
|---------|------|------|
| [mido/mido](https://github.com/mido/mido) | 1.6k | Python MIDI 库，读写/发送 MIDI 消息，可配合脚本做自动化 |

示例思路（生成一段 MIDI）：

```python
import mido
from mido import Message, MidiFile, MidiTrack

mid = MidiFile()
track = MidiTrack()
mid.tracks.append(track)

for note, t in [(60, 480), (64, 480), (67, 960)]:  # C4 E4 G4
    track.append(Message('note_on',  note=note, velocity=100, time=t))
    track.append(Message('note_off', note=note, velocity=0,  time=480))

mid.save('chord.mid')  # 可导入 DAW 或播放
```

## 七、与制作项目的关联

- **midi键盘转换 / 可扩展电子琴**：本质是「按键 → Note On/Off 消息」的桥接
- **MIDI音源（esp32 synth 系）**：把收到的 MIDI 指令合成声音，见[制作项目开源参考](../制作/开源参考项目.md)音乐类
- **词谱改编**：用 [basic-pitch](音乐创作工具参考.md) 把旋律转成 MIDI 后在 DAW 里改和弦/节奏

---

## 🔗 相关链接

- [音乐创作工具参考](音乐创作工具参考.md)
- [制作项目开源参考](../制作/开源参考项目.md)

---

*文档版本：v1.0*
*创建日期：2026-08-05*
