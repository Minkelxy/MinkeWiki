---
date: 2026-05-06
authors: [minke]
categories: [AUTOSAR, 嵌入式]
---

# AUTOSAR OS 核心概念：Task、ISR、Event 怎么协同工作

AUTOSAR OS 是基于 OSEK/VDX OS 扩展而来的实时操作系统。刚接触时概念很多——Task、ISR、Counter、Alarm、Schedule Table、Event、Resource——每个单独看都能懂，合在一起容易乱。这篇梳理一下各模块之间的关系。

## 从 OSEK 到 AUTOSAR

OSEK OS 定义了 4 种一致性类：

| 等级 | 特性 |
|------|------|
| BCC1 | 基础任务，每个优先级只能有一个任务，不能等待事件 |
| BCC2 | 基础任务，允许多个任务同优先级 |
| ECC1 | 扩展任务（可等待事件），每个优先级只有一个 |
| ECC2 | 扩展任务，允许多个任务同优先级 |

AUTOSAR 在此基础上增加了：

- **多核支持**（每个核独立调度）
- **调度表**（Schedule Table，用于时间触发场景）
- **时间保护**（SC3）和**内存保护**（SC4）
- **自旋锁**（多核间同步）

## 核心模块关系图

```
Counter（时间基准）
  ├──→ Alarm（定时触发）
  │      └──→ 激活 Task 或 设置 Event
  └──→ Schedule Table（静态调度表）
         └──→ 按预设时间点触发 Task

Task（执行单元）
  ├── Basic Task：不能等待事件，执行完就结束
  └── Extended Task：可以等待 Event，被唤醒后继续执行

ISR（中断服务）
  ├── ISR1：不使用 OS 资源，速度快
  └── ISR2：可调用 OS API，退出时可能触发任务重调度

Event（同步机制）
  └── 仅供 Extended Task 使用，用于任务间同步

Resource（互斥机制）
  ├── 单核用 Resource（优先级天花板协议）
  └── 多核用 SpinLock（自旋锁）
```

## 一个典型的 Task 是怎么跑起来的

假设有个 10ms 周期的 Task：

1. **Counter**（如 SystemTimer）从 0 往上计数
2. Counter 到达某个值时触发 **Alarm**（Alarm 关联了这个 Counter）
3. Alarm 的动作是激活 **Task**（或设置 **Event** 唤醒正在等待的 Extended Task）
4. **调度器**按优先级决定是否抢占当前 Task
5. Task 执行完后进入 `SUSPENDED` 状态，等待下一次 Alarm 触发

## ISR 打断 Task 的两种结果

**ISR1**（一类中断）：
- 不使用 OS API，完全由硬件处理
- 退出后直接返回被打断的位置，不触发调度

**ISR2**（二类中断）：
- 可以使用 OS API（如 `ActivateTask()`）
- 退出时如果调度器未锁：
  - 被打断的 Task 可抢占 → 触发重调度，可能切到更高优先级 Task
  - 被打断的 Task 不可抢占 → 直接返回

## 几个容易搞混的点

**Counter vs Timer**：Counter 是 OS 层面的抽象（硬件计数器或软件计数器），Timer 是硬件定时器。一个硬件 Timer 可以驱动一个硬件 Counter。

**Alarm vs Schedule Table**：Alarm 适合"每 X ms 执行一次"，Schedule Table 适合"在 T1 时刻执行 A，T2 时刻执行 B"的精确时序。

**Event vs Resource**：Event 是做**同步**（等我准备好了再执行），Resource 是做**互斥**（同一时间只能一个 Task 访问）。Event 只给 Extended Task 用，Resource 所有 Task/ISR 都能用。

## 实战：配置一个周期 Task

在 CFG 工具中：

1. 选目标 Core 的 OS Application
2. 新建 Task → 填名字、优先级（数字越大越高）、类型（Basic/Extended/Auto）
3. 在 MAP 界面搜索并关联周期函数
4. 系统自动生成对应的 Alarm
5. 相同周期的 Task 共享 Alarm → 生成 Basic Task；不同周期的 → 各自独立 Alarm + Event → Extended Task

> 完整配置细节（多核、中断源计算、SpinLock 等）见：[AUTOSAR OS 配置指南](../../知识/AUTOSAR/AUTOSAR_OS配置指南.md)
