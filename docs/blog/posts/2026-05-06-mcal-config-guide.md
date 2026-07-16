---
date: 2026-05-06
slug: mcal-config-guide
authors: [minke]
categories: [AUTOSAR, 嵌入式]
---

# TC3xx EB-tresos MCAL 配置全流程

最近项目需要把 MCAL 从零配起来，记录一下 TC377 平台的完整配置过程。MCAL（Microcontroller Abstraction Layer）是 AUTOSAR 架构里最贴近硬件的一层，配置对了，上层才能正常工作。

## 环境

- 芯片：Infineon TC377
- 工具：EB-tresos
- 代码生成：Davinci

## 工程初始化

EB-tresos 新建 Configuration Project，填 ECU_ID、选芯片类型。关键一步：**勾选 "Automatically add minimum number of child elements in lists"**——不勾的话 Port 里的 Pin 要手动一条条加，浪费时间。

建好后右键 Module Configurations 添加需要的驱动模块。MCU 是第一个要加的，因为时钟配置是所有外设的基础。

## 时钟配置（最核心）

MCU 模块主要配三件事：时钟源、PLL、外设时钟分配。

TC377 有三个时钟源可选，由 `SYSPLLCON0.INSEL` 决定。项目用的外部晶振。

PLL 分两种：

- **SYSTEM PLL** → 产生 `fPLL0`，公式：`fOSC × (N+1) / ((P+1)×(K2+1)×(K3+1))`
- **Peripheral PLL** → 产生 `fPLL1/2`，公式：`fOSC × (N+1) / ((P+1)×(K2+1))`

配完后在 `McuPllDistributionSettingConfig` 里把参考时钟分配给各外设（ADC、PWM、SPI 等）。

**一个容易踩的坑**：GTM 时钟必须和 SPB 时钟呈整数倍关系。比如 SPB=300MHz，配 GTM=100MHz 才能通过。

## GTM 配置（PWM 和 ICU 的基础）

GTM 结构比较绕：CTBM → CMU(EGU/CFGU/FXU) → CCM → TBU → TIM/TOM/ATOM。

- **CFGU** 产生 8 个可配置时钟 `CMU_CLK[0~7]`，公式：`TCMU_CLK[x] = (CLK_CNT[x]+1) × TCMU_GCLK_EN`
- **FXU** 产生 5 个固定时钟给 TOM 做内部 PWM

项目中用 ATOM 做电控 PWM，时钟源来自 `GTM_CONFIGURABLE_CLOCK_0`。每个 ATOM 通道还要配 `PWM_FIXED_PERIOD_SHIFTED` 模式并勾选 Coherent Update。

## DIO 和 PORT

这两个模块经常被一起提到但作用不同：

- **DIO**：汇总所有数字量 IO，按 Port 和 Pin 组织
- **PORT**：配置每个 Pin 的属性——输入/输出、推挽/开漏、驱动强度、是否上拉

一个经验：**PinName 一定跟硬件原理图保持一致**，否则后面调试时对不上会非常痛苦。

MEDIUM 驱动模式用于 PWM 输出、CAN/LIN/SPI 通信引脚（过冲小，EMI 低），DEFAULT 用于普通 IO。

## ADC

两个 Group：硬件触发组（PWM 同步触发）和软件触发组。关键配置：

- 硬件组：`AdcGroupTriggSrc = HW`，`ConversionMode = ONESHOT`，触发源选 `GTM_ADCx_TRIG0`
- 软件组：`AdcGroupTriggSrc = SW`，`ConversionMode = ONESHOT`

GTM 到 ADC 有 5 个触发源（TRIG0~TRIG4），每个触发源的 OUT0/OUT1 对应不同的 AdcHwUnit 范围。项目用 ATOM0_7 作触发通道。

## 写在最后

MCAL 配置本质上就是把芯片手册里的寄存器描述翻译成工具的图形界面。核心原则：

1. 先配时钟再配外设（时钟是上游依赖）
2. 每个 Pin 的属性单独确认（输入/输出/复用/驱动强度）
3. 变更后重新导出 ARXML 给 Davinci

> 完整配置细节（ICU、SPI、DSADC、变更记录）见知识库：[MCAL开发配置指南](../../知识/AUTOSAR/MCAL开发配置指南.md)
