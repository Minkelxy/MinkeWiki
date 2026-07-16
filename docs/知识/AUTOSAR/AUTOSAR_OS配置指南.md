# AUTOSAR OS 配置指南

AUTOSAR OS 操作系统配置指南，涵盖 Task、ISR、Counter、Alarm、Schedule Table、Event、Resource 等核心模块。

> 📝 **博客版**：叙事风格的模块关系梳理见 [AUTOSAR OS 核心概念](../../blog/2026/05/06/autosar-os-core-concepts/)

> **参考规范**：AUTOSAR_SWS_OS
> **OSEK OS 基础**：AUTOSAR OS 基于 OSEK/VDX OS 标准扩展而来，向下兼容 OSEK OS。OSEK 定义了 4 种一致性类（BCC1/BCC2/ECC1/ECC2），AUTOSAR 在此基础上增加了多核支持、调度表、时间保护等特性。
> **可扩展性等级**：AUTOSAR OS 定义了 SC1-SC4 四个可扩展性等级 — SC1 为基础功能，SC2 增加调度表，SC3 增加时间保护，SC4 增加内存保护和应用间通信。实际项目根据功能安全等级选择合适的 SC 等级。

---

## OS 操作系统概述

AUTOSAR_SWS_OS 规范中 7.6 章节对 AUTOSAR OS 的框架定义主要包含以下核心模块：

### APPLICATION
OS-APP，负责收集操作系统对象。如果使用OS-Application，则所有的Task, ISR, Counter, Alarm, Schedule Table都必须属于某一个OS-Application 。

### SCHEDULETABLE
调度表引入是因为OSEK OS可以通过一个计数器和一系列自启动的报警器来实现静态定义的任务激活机制。但如果需要在运行时对报警器进行修改，那么就要保证报警器之间的相对同步。为了解决这个问题，调度表提供了一组静态定义的溢出点集封装。调度表可以在基于数据流的设计中，可以保证数据的一致性；可以与基于时间触发的网络中进行时间同步；保证系统运行时的正确执行顺序。

### ALARM
报警器，一般用于在操作系统运行过程中，可进行实时的报警周期设置，典型的用于功能安全相关的调度机制。一个计数器能够用于驱动多个报警器，当相应的计数器达到报警器预设值的时候，报警发生；报警器的定时值可以是相对的，也可以是绝对的；当一个报警发生的时候，预设的报警器动作将被执行，同时一个报警器只能配置唯一的报警动作。

### COUNTER
计数器（Counter）是 OS 时间管理的基础单元，用于驱动 Alarm 和 Schedule Table。关键参数：

- **OsCounterMaxAllowedValue**：计数器最大值，达到后回绕
- **OsCounterTicksPerBase**：计数器单次累加的 Ticks 值
- **OsCounterMinCycle**：以该计数器为触发源的 Alarm 所允许的最小告警周期

**硬件计数器**：由硬件定时器触发（如 GPT 接口），或通过 OsDriver 配置外部硬件驱动触发。

**软件计数器**：通过接口函数 `IncrementCounter(CounterID)` 在代码中主动触发计数。

### TASK
周期任务主要分为扩展任务和基础任务，基本任务BT（Basic Task）状态以及状态转换切换入下图所示。

扩展任务ET（Extended Task）以及状态转换切换入下图所示。

协调任务的执行次序，决定任务访问处理器的优先权：
任务优先级在系统配置阶段静态分配。
数字越大，代表的优先级越高，0的优先级最低。
BCC2/ECC2时，允许有多个任务使用相同优先级。
优先级相同的任务，开始执行的次序取决于任务的激活次序。

### ISR
中断任务，响应外部和内部事件触发的中断，中断的优先级高于任务,因此可以抢占任何任务。在执行中断子程序的时候如果激活了一项任务,那么要等到所有中断服务结束之后该任务才能开始执行。中断分为两类第一类中断（ISR1）：此类中断服务程序不使用操作系统的资源,处理过程完全由硬件完成。这类中断对任务的管理没有影响,它不要求调用操作系统的API,因此占用的资源少,处理速度快,花费也较小；第二类中断（ISR2）：操作系统进行中断预处理和中断后处理操作，可以调用操作系统的API。
中断打断任务返回的处理：第一类中断直接返回被打断的位置
第二类中断：如果被第二类中断打断的任务是可抢占的，并且在ISR执行完毕时调度器没有上锁，则系统在退出中断时会产生任务重调度，操作系统根据调度的结果选择开始执行新的任务或者返回之前被打断的任务继续执行。如果被第二类中断打断的任务是不可抢占的，或者在ISR执行完毕时调度器处于锁定的状态，操作系统将直接返回被打断的位置。

### ErrorHook
当 OS 运行时发生错误（如 Task 激活失败、资源配置错误等），OS 调用此 Hook 进行错误处理。原型为 `ErrorHook(StatusType Error)`。用于功能安全相关的错误监控和故障响应。

### ProtectionHook
当 OS 检测到时间保护或内存保护违规时调用。是 AUTOSAR OS SC3/SC4 等级的核心功能，用于：
- 监控 Task/ISR 执行时间是否超限
- 检测非法的内存访问
- 触发功能安全降级策略

原型为 `ProtectionHook(StatusType FatalError)`，进入此 Hook 后通常意味着需要重启或进入安全状态。

### StartupHook
系统上电后、OS 启动调度器之前调用，用于完成硬件初始化和启动自检。原型为 `StartupHook(void)`。

### ShutdownHook
系统下电或 OS 关闭时调用，用于保存关键数据、关闭外设、执行安全关机流程。原型为 `ShutdownHook(StatusType Error)`。

### Event
事件的主要用途是任务同步,仅供扩展任务ET（ Extended Task）使用。事件的意义由应用程序来决定，任何任务和第二类ISR都能为一个处于非终止状态的ET来设置事件
事件只能被拥有这个事件的ET清除，只有拥有某个事件的ET能等待这个事件，当一个处于运行态的ET需要等待一个事件，并且这个事件已经被设置，则这个ET将继续保持在运行状态中断服务函数或者BT不能等待事件

### Resources
任何可以被应用程序使用的对象都可称为资源、硬件设备、内存区域（ROM/RAM）、应用程序：变量，结构体，程序段等、操作系统实体（调度器）
Resources资源管理用于协调处于不同优先级上的多个任务或中断服务函数对共享资源的并发访问，保证两个任务或中断服务函数不能同时占用同一资源、不会引起死锁（Deadlock）、不会发生优先级反转（Priority Inversion）
OS 配置
SIP包OS初始配置
打开初始SIP包配置， 初始的OS CORE中只有CORE0的配置如下图所示，CORE0自带相关OS-Application，Application中也自带相关的默认TASK和一些以配置模块的中断，对应的多核启动，需要我们手动添加CORE1与CORE2相关配置。

添加CORE1的相关示例如下：

添加OScore1时候我们需要添加对应的core的APPLICATION：

SIP包中自带默认TASK如下图所示。该默认的TASK在后续的配置中一直有所保留，可以在默认的TASK任务中添加周期任务，在该项目中每一个核对应的为一个APPLICATION。

同样步骤完成添加core2的相关内容，至此完成OS的初始配置。
OS配置介绍
在配置选项界面中选择点击Runing System，然后点击OS Configuration。该界面为OS配置界面。主要配置项如下：

OS Cores相关配置
OS Cores:CPU的内核，新建一个Core，工程会自动生成一个Applicaion以及里面Task。改界面主要配置硬件核相关属性，在初始SIP配置中默认配置的时候已经完成该部分的默认配置，该界面的配置说明如下所示：
OS Application相关配置
OS Application：每一个核都对应一个OS Application。Application可以配置是否Trust，Trust Application里面的的TASK可以访问所有的memmery flash的权限。OSApplication是程序应用的单元，每个OSApplication包含如下内容:
对应一个OS Application通用配置的说明如下图所示：

TASK相关配置
Tasks:Task菜单栏里面包含了该OsCore应用下所有Task的配置，需要根据Task的业务关系，分配Task优先级，需要注意的是Task优先级数字越大优先级越高Task的类型有AUTO、Basic、Extended。其中AUTO类型由系统自动计算Task是属于Basic或者Extended类型。TaskSchedule配置Task是否可以抢占。

Interrupt Service Routines:中断服务程序菜单会列出该OSCoreApplication下所有配置的中断服务程序配置，比如如下CounterlsrSystemTimer中断服务程序的配置。需要注意的是中断优先级数字的大小可能与Task优先级数字大小不一样，中断优先级数字大小与优先级关系需要查看对应的芯片手册。

Alarm相关配置
Alarm：Alarms菜单会列出该OSCoreApplication下所有的Alarm，在RTE创建的周期任务，然后将其分配给某个Task，一般会自动生成一个Alarm，AlarmCounter的参考Counter一般来自于SystemTimer， Alarm一般会关联一个Event，用来设置Alarm的行为。

Events相关配置
Events：Events菜单下会列出系统中所有生成的Event，在RTE上创建一个Runnable，其等待一个信号之后触发，这种就会生成一个Event。另外Task中周期的Runnable也会生成一个Event作为条件。生成Alarm时候一般会关联一个Event。

Resources/ Spin Locks相关配置
Resources：Resources菜单下会列出系统中所有配置的资源，资源对象用于协调Task/ISR对共享资源的并发访问，例如调度程序、任何程序序列、内存或任何硬件区域。

Spin Locks：SpinLocks菜单下会列出系统中所有配置的自旋锁，自旋锁对象用于协调不同核上的Task/ISR对共享资源的并发访问。

周期task配置示例
以新建立核0的一个TASK示例所示，选择在OsCore0.systemApplication_OsCore0的TASK选项卡新建任务可以自动关联到对应的核。

TASK新加成功后点击对应的TASK配置对应的TASK的名字、优先级、任务是否可以被抢占，以及Task的任务类型。

然后需要给对应的TASK配置对应的运行函数，相关步骤如下图所示。在MAP界面可以对想要的周期函数进行搜索。

当关联好对应的周期函数后，TASK会自动添加对应的Alarms。当所添加的周期任务的周期相同时候关联的Alarms统一、不会关联EVENT，可以生成的对应的基础任务类型的TASK。当所添加的周期任务的周期不同时候，会关联不同的Alarms，同时生成关联不同的EVENT，生成扩展类型的任务。

中断配置示例
以新建立核1的一个TIM中断示例所示，选择在OsCore0.systemApplication_OsCore1的Interrupt Service Routines选项卡新建任务可以自动关联到对应的核。

新加好后的中断进行对应的中断类型进行配置，选择填入合适的优先级，以及堆栈空间。以TIM31的ICU捕获中断为例。查找对应的芯片手册的中断源计算如下。通过查询芯片手册的计算中断源为3060填入配置中。

查询芯片手册计算ICU捕获中断源。

在CFG中配置完相关的中断函数和中断源后需要在C代码中手动添加中断服务函数，如下图所示：


---

## 🔗 相关链接

- [返回 AUTOSAR 知识](./README.md)
- [返回知识库](../目录.md)

---

*原始文档：AutoSAR OS配置指南.docx*
*转换日期：2026-05-06*
