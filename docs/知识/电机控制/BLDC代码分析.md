---
tags:
  - 电机控制
---

这段代码是针对基于S32K微控制器的电机控制系统的一部分

> 📝 **博客版**：ISR 协同工作拆解见 [S32K 电机控制代码拆解](../../blog/posts/2026-05-06-motor-isr-breakdown.md)，主要关注于电机的控制逻辑、状态管理和相关中断服务例程。下面是各个函数的详细分析：

1. Gear_EngageControl()
这个函数负责根据当前的齿轮位置和PWM命令来控制电机的齿轮状态。它检查gear_position和PWM_Cmd来决定电机应该处于哪种状态（例如，初始、脱离、啮合、运行、制动或自由状态）。它也更新电机的速度要求和电机命令。

2. LPIT0_Ch0_IRQHandler()
这是一个LPIT（低功耗脉冲定时器）通道0的中断服务例程，用于执行速度和电流控制回路。在这个中断中，它计算了最近六次零交叉事件的FTM0计数器周期总和，调用Gear_EngageControl()函数来更新齿轮控制状态，并执行速度PI调节器。此外，它还负责设定下一个ADC触发，清除中断标志以准备下一次触发。

3. LPIT0_Ch1_IRQHandler()
这是LPIT通道1的中断服务例程，主要用于检测PWM信号的高低电平持续时间和周期，从而计算PWM命令值。它通过读取引脚状态并跟踪高电平和低电平的持续时间来实现这一点，然后根据这些信息计算出PWM命令值。

4. ADC1_IRQHandler()
这是ADC1中断服务例程，用于读取ADC转换的结果，包括断开相的反电动势（BEMF）电压、直流母线电流和电压的原始值。它还负责计算实际的直流母线电流和BEMF电压，并应用低通滤波器到直流母线电压和电流上。

5. FTM0_Ovf_Reload_IRQHandler()
这是FlexTimer0的溢出重载中断服务例程，用于在无传感器模式下执行六步换向控制。它通过零交叉检测算法和两次连续换向之间的时间测量来确保换向控制。这个中断还更新了FTM0计数器，恢复换向扇区，执行换向，并清除一些状态标志。

6. PORTE_IRQHandler()
这是PORTE端口的中断服务例程，用于检测MC34GD3000（可能是电机驱动芯片）的故障情况。然而，在提供的代码片段中，这个函数没有具体实现。

其他静态函数
代码中还包括了一些静态函数，如minusCalibTimes(), minusAlignTimes(), updateFTM0timer_openloop(), updateFTM0timer_closeloop(), assignNextADCtrigger(), filterDCbusCur(), restoreTriggerADCtime(), estimateSpeed(), 和 speedPIregulator()。这些函数分别用于减小校准时间、减小对齐时间、更新FTM0计时器（开放环和闭环）、设置下一个ADC触发、过滤直流母线电流、恢复ADC触发时间、估计速度和执行速度PI调节器。它们都是电机控制逻辑的关键部分，但具体的实现细节没有在提供的代码片段中给出。

整个代码片段展示了电机控制系统的复杂性和深度，涉及到了定时、中断管理、ADC转换、PWM信号分析、电机状态控制和换向逻辑。

1. PDB0_IRQHandler(), PDB1_IRQHandler()
这两个函数分别是PDB0和PDB1的中断服务例程。它们首先禁用相应的PDB模块，清除序列错误标志，然后再重新启用PDB。这通常是为了响应ADC预触发序列中的错误，确保ADC操作的正确性。

2. minusCalibTimes()
此函数用于减少校准时间计数器。当gMotorControl.driveStatus.B.Calib为真时，每次中断都会递减calibTimes，这有助于控制校准过程的持续时间。

3. minusAlignTimes()
此函数用于减少对齐时间计数器。如果gMotorControl.driveStatus.B.Alignment为真，且alignmentTimes大于0，则递减alignmentTimes。这用于控制电机对齐过程的时间。

4. updateFTM0timer_openloop(), updateFTM0timer_closeloop()
这两个函数分别用于在开环和闭环控制模式下更新FlexTimer0（FTM0）的计数器值。updateFTM0timer_openloop()在非闭环模式下设置计数器的周期，而updateFTM0timer_closeloop()则在闭环模式下进行，考虑了零交叉检测的时间。

5. assignNextADCtrigger()
此函数计算并分配下一个ADC触发的延迟。延迟基于实际的占空比，以在PWM脉冲结束时测量直流母线电压和反电动势电压。这有助于在正确的时刻进行ADC采样。

6. filterDCbusCur()
此函数用于过滤直流母线电流。当占空比大于某个阈值时，它会应用移动平均滤波器到直流母线电流测量值；否则，它会忽略低占空比下的电流测量，以避免噪声影响。

7. restoreTriggerADCtime()
此函数读取并保存FTM计数器的当前值，以便在下次ADC触发时使用。这有助于在ADC中断服务例程中恢复时间信息。

8. executiveCommutation()
此函数负责执行换向。它测量断开相的反电动势电压，更新下一换向扇区，并准备PWM设置以进行下一次换向。

9. estimateSpeed()
此函数用于估计电机速度。它基于零交叉检测算法和BEMF电压的变化来计算电机的速度。它还涉及到插值算法以提高速度估计的精度。

10. speedPIregulator()
此函数实现了速度PI调节器。它计算扭矩误差和速度误差，使用PI控制器调整PWM占空比，以达到所需的电机速度。它还考虑了最大扭矩限制和电压前馈，以改善动态响应。

这些函数共同构成了电机控制软件的核心部分，负责处理电机的状态监控、控制策略的执行以及与硬件的交互。