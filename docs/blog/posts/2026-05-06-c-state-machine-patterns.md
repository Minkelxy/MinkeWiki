---
date: 2026-05-06
authors: [minke]
categories: [嵌入式, 编程规范]
---

# C 语言状态机实战：从交通灯到电机换相

状态机是嵌入式开发中最常用的设计模式之一。从按键扫描到通信协议，从电机换相到整车状态管理——本质上都是状态机。

## 两种经典实现

### 方式一：switch-case（最简单）

```c
typedef enum {
    STATE_IDLE,
    STATE_RUNNING,
    STATE_ERROR
} State;

State current = STATE_IDLE;

void run_state_machine() {
    switch (current) {
        case STATE_IDLE:
            if (start_condition) current = STATE_RUNNING;
            break;
        case STATE_RUNNING:
            if (error_condition) current = STATE_ERROR;
            break;
        case STATE_ERROR:
            if (reset_condition) current = STATE_IDLE;
            break;
    }
}
```

**优点**：直观，新人一看就懂
**缺点**：状态多了 switch 很长；新增状态要改函数体，违反开闭原则

### 方式二：函数指针表（状态多时推荐）

```c
typedef void (*StateHandler)(void);

void idle_handler(void)    { /* ... */ }
void running_handler(void) { /* ... */ }
void error_handler(void)   { /* ... */ }

StateHandler state_table[] = {
    [STATE_IDLE]   = idle_handler,
    [STATE_RUNNING] = running_handler,
    [STATE_ERROR]  = error_handler,
};

// 调度
state_table[current]();
```

**优点**：状态和行为一一对应；新增状态只需加函数 + 表项
**缺点**：需要额外的状态转移机制

## 实战案例：电机换相状态机

六步换相本质上就是一个 6 状态的循环状态机：

```
扇区0 → 扇区1 → 扇区2 → 扇区3 → 扇区4 → 扇区5 → 扇区0...
```

每次换相本质就是状态转移：改变三相 MOSFET 的通断模式。用函数指针表实现：

```c
void commutation_sector0(void) {
    // A相上桥 ON, B相下桥 ON, C相 OFF
    set_phase(PHASE_A, HIGH_SIDE);
    set_phase(PHASE_B, LOW_SIDE);
    set_phase(PHASE_C, OFF);
}
// sector1 ~ sector5 类似...

void (*comm_table[6])(void) = {
    commutation_sector0, commutation_sector1,
    commutation_sector2, commutation_sector3,
    commutation_sector4, commutation_sector5,
};

// 换相就是 index 加 1
current_sector = (current_sector + 1) % 6;
comm_table[current_sector]();
```

## 状态机设计原则

1. **每个状态只做一件事**：如果在某个状态的处理函数里出现了"如果 flagA 就做 X，如果 flagB 就做 Y"，考虑拆分成两个状态
2. **转移条件要显式**：不要依赖隐式的前后关系，每个转移条件都写在代码里
3. **非法状态要有默认处理**：switch 的 `default` 或数组的越界检查，防止跑飞

## 什么时候不该用状态机

不是所有逻辑都适合状态机。一个简单的判断标准：**如果有明确的"阶段"概念，用状态机；如果只是条件组合，用 if-else 或决策表**。

比如"根据转速和负载查表决定 PWM 占空比"就不适合状态机——这是查表，不是状态转移。

> 完整代码示例（交通灯状态机）见：[状态机学习](../../知识/其他/状态机学习.md)
