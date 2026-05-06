# MCAL开发配置指南

MCAL（Microcontroller Abstraction Layer）开发配置指南，基于 Infineon TC3xx（TC377）平台和 Elektrobit EB-tresos 工具。

> 📝 **博客版**：如果你更想看叙事风格的精简版，见 [TC3xx EB-tresos MCAL 配置全流程](../../blog/2026/05/06/mcal-config-guide.md)

> **MCAL 简介**：MCAL 是 AUTOSAR 架构中的微控制器抽象层，位于硬件之上、ECU 抽象层之下。它提供标准化的驱动接口，使上层软件与具体芯片解耦。MCAL 模块包括 MCU、DIO、PORT、ADC、PWM、ICU、SPI、CAN、LIN 等，每个模块对应芯片的一个外设功能域。
>
> **EB-tresos** 是 Elektrobit 提供的 AUTOSAR 配置工具，用于可视化配置 MCAL 模块并生成 ARXML 配置文件，然后导入 Davinci 等工具进行代码生成。

---

## 1. TC3xx EB-tresos 工程建立
首先，使用默认路径或者提前建立好的文件夹路径存放workspace文件。

选择File-->New-->Configuration Project,建立新的工程。

填写ECU_ID以及根据实际情况选择芯片类型，注意勾选Automatically add minimum number of child elements in lists。这样新建的工程会添加一些基本的配置结构，包括Port里各个Pin。

建立好之后就能在Project Explorer中见到我们刚建立好的工程,右键选择Module Configurations添加驱动模块。

下图添加了MCU模块，选中左边的可选模块中的MCU，然后单击右指的绿色加号摁扭即可完成添加。 删除的话选中中部已添加的模块，单击右指的红色减号摁扭即可完成删除。最右边可以修改生成代码的路径和使用的xdm文件，如果需要导入已有的模块xdm配置文件，在这里选择点击OK即可 。

至此完成EB工程的初始化建立。

## 2. MCU模块
对于MCU模块而言，其最主要配置内容为时钟配置，时钟配置主要包括时钟源的选择，PLL分频系数的选择，外设时钟通道的分配。
XCU所用的芯片TC377对于MCU模块而言，其最主要配置内容为时钟配置，时钟配置主要包括时钟源的选择，PLL分频系数的选择，外设时钟通道的分配。三个时钟源的选择是由寄存器SYSPLLCON0 的INSEL位决定。

该项选择的是外部晶振时钟源，输入外部晶振时钟频率选择MCU配置选项进入时钟树的配置。

PLL 包括 SYSTEM PLL 和 Peripheral PLL，两者参考频率计算公式不同：

**SYSTEM PLL：** `fPLL0 = fOSC × (N + 1) / ((P + 1) × (K2 + 1) × (K3 + 1))`

**Peripheral PLL：** `fPLL1/2 = fOSC × (N + 1) / ((P + 1) × (K2 + 1))`

> 其中 N 为倍频系数，P、K2、K3 为分频系数（计算时均需 +1），DIVBY 为寄存器 PERPLLCON0 的一个位。
> 两组公式中的 N、P、K2 是独立的，在 EB 的 `McuSystemPllSettingConfig` 和 `McuPeripheralPllSettingConfig` 中分别配置。

PLL的时钟源，即外部时钟、外部晶振、备用时钟源三者中的一个，由配置项   McuPllInputSrcSelection确定，时钟源通过PLL倍频后得出参考时钟fPLL0，fPLL1，fPLL2。除此之外，外部晶振时钟，备用时钟均可直接作为参考时钟。有了参考时钟之后便可将这些参考时钟根据需要分配给各外设，如ADC，PWM等。

McuPIIDistributionSettingConfig进行时钟树的分配，选择的时钟源是选择哪个参考时钟（备用时钟源、PLL二者中的一个）分配给各外设。

在下图中对各个模块的时钟进行分配，该界面显示了给各个外设模块所分配的时钟频率，以SPB模块为例，SPB的时钟源是fPLL0，且SPB的时钟频率与fSOURCE0的时钟频率的比例关系由寄存器CCUCON0的SPBDIV位决定，如下图所示：

GTM时钟是本项目使用比较多的时钟，GTM时钟的计算公式在芯片手册中配置如下如下，EB里要求GTM的时钟必须和SPB的是整数倍关系。

左图为GTM时钟频率在EB工具里的配置，配置完成后，CCUCON0寄存器的GTMDIV位的值会自动改变，如右图所示，XCU项目的EB配置为100M后GTMDIV位为0011，即：
fGTM=fSOURCE0/ GTMDIV=300M/3=100M

对于GTM，其时钟频率又可分配给TIM、TOM、ATOM，并且可以各自配置分频和倍频系数以获得所需要的时钟频率。对于TIM、TOM、ATOM而言，各自又有多个module，每个module又包含多个channel，每个channel可以作为相应外设的时钟源。
GTM(Generic Timer Module)通用定时器模块由多个子模块构成，分为多个Cluster，每一个Cluster都拥有很多独立的子单元，每一个Cluster都有一个独立的CCM（Cluster Configuration Module）模块管理。时钟和时间基准管理（CTBM）只存在于Cluster0，管理所有Cluster的时钟，CTBM可以分为CMU (Clock Management Unit)、TBU (Time Base Unit）、DPLL (Digital PLL Module)、MAP (TIM0 Input Mapping Module)。时钟管理单元(CMU) 是CTBM的一个重要模块，负责生成计数器和GTM的时钟，CMU由三个子单元EGU、CFGU和FXU组成，它们为整个GTM产生不同的时钟源。它根据CMU主源信号（CLS0_CLK）为GTM的子模块产生多达16个时钟，包括3个外部时钟(CMU_ECLK0~2)、8个可配置时钟(CMU_CLK0~7)和5个固定时钟(CMU_FXUCLK0~4)。GTM(Generic Timer Module)通用定时器模块配置界面如下图所示点击进入配置。

可配置时钟生成子单元(CFGU)为GTM模块: TIM、ATOM、TBU和MON提供了8个专用可配置的时钟源。其配置界面如下所示。该单元的时钟计算频率公式如下所示。
TCMU_GCLK_EN=(Z/N)*TCLS0_CLK
TCMU_CLK[x]=(CLK_CNT[x]+1)*TCMU_GCLK_EN

固定时钟生成子单元(FXU)主要为TOM模块生成预定义的不可配置时钟信号，用于内部PWM的生成，FXU的时钟源可以选择CMU_GCLK_EN、CMU_CLK0~7，时钟分频因子固定为2的0，4，8，12，16次幂。

Cluster Configuration Module (CCM)，XCU所使用芯片的GTM有6个Cluster对应9个CCM。分频选择会影响到TIM、TOM、ATOM的时钟频率。

Time Base Unit (TBU)时间基准单元，TBU产生信号主要作为边缘检测时钟给GTM其他模块使用。TBU生成三个时钟基准信号 TBU_TS0、TBU_TS1、TBU_TS2，其中TBU_ST0是27位计数器，TBUTS1和TBU_TS2都是24位计数器。

使能了TBU，就要配置TBU的信号源，TBU的主源时钟信号可选CMU单元产生的CMU_CLK[1~7]时钟信号。

TGC(TOM Global Channel Control)，选择TOM时钟基准，可选择TBU_TS0或者TBU_TS1，如下图所示每一个TOM共16个输出通道由TGC0和TGC1控制，同时在该地方配置TOM通道于引脚对应的映射关系。

ARU-connected Timer Output Module (ATOM)，选择ATOM时钟基准，可选择TBU_TS0、TBU_TS1和TBU_TS2，AGC(ATOM Global Channel Control)，选择ATOM时钟基准，如下图所示每一个ATOM共8个输出通道由TGC0和TGC1控制，同时在该地方配置ATOM通道于引脚对应的映射关系。

Timer Input Module (TIM)负责过滤和捕获GTM的输入信号。每一个TIM共8个输出通道,同时参考芯片手册配置TIM通道和对应的引脚的引脚进行映射。例如下图所示。


## 3. DIO模块
Dio模块的作用可理解为汇总所有的数字量IO口，首先在工程中添加DIO模块

双击DIO模块进入配置环境，根据硬件原理图进行配置，下图为XCU部分硬件原理图和EB的DioPort配置界面。

双击相应的DioPort，可在该DioPort中添加属于该Port且用作数字量IO口的所有Pin，以DioPort0为例，双击进去后的界面如下图所示。在该配置界面中添加属于该Port的作数字量IO口的Pin，具体该Port的哪些Pin脚是作数字量IO口用根据需求确定。右边的DioChannelID需和Pin脚编号一致，该DioPort有多少个PIN需要控制就添加几个，添加后可以更新硬件原理图对PIN脚进行命名。

其他的PORT根据同样的流程完成DIO的配置。

## 4. PORT模块
对于Port模块而言，其主要目的是配置每个Pin脚的属性，同样首先在工程中添加port模块，其最主要配置内容为输入输出的选择、高低电平的选择、是否复用、输出模式等。如下图所示，PORT20中包含13个PIN引脚。

双击相应的Port，可以配置该Port的每一个Pin的属性，以Port20为例，双击进去后的界面如下图所示，为了便于查找和提高代码的可读性，PinName最好与硬件原理图上的每个Pin名称一致。

双击相应的Pin，即可进入该Pin的配置界面，以Pin20.0为例，双击进去后的界面如下图所示，对于一个Pin，将其配置为输入或者输出两种模式时，其需要配置的属性不同，如图，高亮显示的为输出模式下的可配置项，灰色为输出模式下的不可配置项。

在配置输出引脚的PortPinInitialMode时候，需要根据引脚功能而设置不同的模式，假如原理图中将该脚作为PWM输出用，由于PWM的输出直接与GTM的TOM关联，即为左图中的O1，因此右图选择ALT1。

输出引脚的PortPinOutputPadDriveStrength是配置输出引脚的输出能力，STRONG表示输出能力较强，边缘变化速度快，但过冲较大。MEDIUM较STRONG和DEFAULT的输出能力较弱，边缘变化速度慢，但过冲较小。
通常引脚作普通IO口时选择DEFAULT模式，若作为频率输出用如，PWM输出、CAN的TX、LIN的TX、SPI的MISO、SPI的MOSI、SPI的CLK、SPI的CS等时需要配置成MEDIUM模式。原因是MEDIUM模式的过冲小，产生的电磁干扰小。

PortPinOutputPinDriveMode的配置项有两种选择：推挽、开漏。
推挽：CPU对该管脚写1，该管脚输出高电平； CPU对该管脚写0，该管脚输出低电平。
开漏：CPU对该管脚写1，该管脚输出电平状态取决与外部电路，外部电路有上拉电阻时输出高电平，外部电路没有上拉电阻时输出低电平； CPU对该管脚写0，该管脚输出低电平。

双击Pin20.1（硬件原理图中该引脚为输入引脚），进入Pin20.1的配置界面如下图所示。同输出一样，灰色为不可配置项。

PortPinInputPullResistor配置作用为配置该引脚是否内部上下拉，或者浮空。可根据需求进行配置。一般在该项目中都配置了外部上下拉，所以软件配置中一般将这个配置成悬空处理。

PortPinInputPadLevel该配置项的作用为配置该引脚的电压等级，根据需求进行选择，该项目的选择都是COMS。


## 5. ADC模块

## 5. 1 总览
ADC模块的主要配置项为时钟和ADC通道，下图左侧为ADC的General配置界面，右侧为MCU的CLOCK配置界面，左图中的选项即选择前面在MCU模块中所配置的时钟。

AdcGlobalInputClass配置：默认会生成两个Class，每个Class都可配置AD转换的降噪等级和预充电时间，默认状况下两个Class的配置相同。

AdcHwUnit界面配置：左图为硬件原理图，右图为EB的AdcHwUnit配置界面。原理图中的G0CH0表示Group0的Channel0，其余类似。每一个Group对应一个AdcHwUnit。

双击AdcHwUnit即可进入每个AdcHwUnit的配置界面，以AdcHwUnit_0为例，如图所示。
General界面采用默认配置，AdcClockSource界面，由于前面已经选择ADC的时钟为MCU里所配置的，因此此处配置项不起作用，配置为默认值。

AdcPrescale界面参数配置ADC时钟的分频系数，可根据需要进行配置，XCU项目此处采用默认值。AdcHwUnitInputClass界面与前面的Class配置相同，此处也采用默认值。
AdcChannel界面中可根据需要添加ADC通道，如图为在ADC Group0中添加通道。

AdcChannel配置：双击AdcChannel可对每个AdcChannel进行具体配置，以AN0为例。由右图数据手册可知，AN0只有一个可用通道，因此左图直接选G0CH0；假若需为AN4选择通道，由右图可知，有G11CH0和G0CH4可用，因此可以二选一，只需保证该通道仅被AN4选用。

AdcGroup界面可为每个AdcHwUnit创建一个AdcGroup，该项目中分为两个Group，分别为硬件触发和软件触发如下图所示。

双击添加的AdcGroup可进行具体配置，如下图所示。

该配置界面可配置ADC为连续转换还是单次转换、软件触发还是硬件触发、数据缓冲是线性的还是循环的，可根据需求进行配置，XCU项目此处除去触发模式外均为默认值。

## 5. 2 硬件组配置
针对需要硬件触发的ADC采样组，需要配置对应的PWM通道，例如本项目中采用PWM_ADC_TRIG作为触发ADC硬件组采样触发源。

GTM到ADC有五个触发源，分别为TRIG0、TRIG1、TRIG2、TRIG3、TRIG4。其中ADCTRIGiOUT0负责AdcHwUnit_0、AdcHwUnit_1、AdcHwUnit_2、AdcHwUnit_3、AdcHwUnit_4、AdcHwUnit_5、AdcHwUnit_6、AdcHwUnit_7。ADCTRIGiOUT1负责AdcHwUnit_8、AdcHwUnit_9、AdcHwUnit_10、AdcHwUnit_11。

本项目中，采用ATOM0_7作为触发通道，GTM_ADCTRIG0OUT1的SELx选择为8H，在ADC硬件組的配置上，AdcHwExtTrigSelect  选择ADC_TRIG_8_GxREQTRI_GTM_ADCx_TRIG0，同时，需要配置AdcGroupTriggSrc 为ADC_TRIGG_SRC_HW，转换模式AdcGroupConversionMode  为ADC_CONV_MODE_ONESHOT，onshot模式，触发一次采集一次。

上图选择了TRIG8作为中断的触发源，在MCU的模块中，GtmTriggerForAdc选项卡中，GtmAdcTrigger0Select需要对应的配置成TRIG_8。

边沿的选择要根据触发路的PWM波形配置好对应的上升/下降沿，这里配置成上升沿触发，同时配置好中断服务子程序，中断服务子程序中实现相应的电流采样结果的计算和应用层算法的执行。

所有硬件组如下：


## 5. 3 软件组配置
软件组的配置如下图，其中需要注意的是AdcGroupConversionMode 需要设置为one-shot，AdcGroupTriggSrc  为ADC_TRIGG_SRC_SW软件触发。AdcStreamingBufferMode  配置为ADC_STREAM_BUFFER_LINEAR线性buffer。

AdcGroupDefinition中定义了group中的channel，且在AdcResRegDefinition需要配置相同数量的结果寄存器用于接收结果，即channel和reg保持一一对应的关系。

所有软件组如下：


#### HSI 分配
> HSI（Hardware Signal Interface）分配表请参见原始文档中的截图。

## 6. PWM 模块

## 6. 1 总览
PWM的配置主要包括通道配置、时钟选择、极性配置等、PWM模块的General界面的配置项主要为是否启用相关函数，可根据需要进行配置。
PwmChannel界面可根据需要在PwmChannel界面添加通道，XCU项目中有19路PWM输出，因此在此添加19个通道。

双击上图中添加的PwmChannel，可对每个PwmChannel进行具体的配置，如下图所示，PwmChannelClass界面进行配置为PWM_VARIABLE_PERIOD，选择该模式时，频率和占空比均可变。

GtmTimerOutputModuleConfiguration界面为PWM通道配置时钟源，双击进去可进行具体配置，如下图所示，这里选择TOM2的Channel1作为HSD1_EN_P13_1的时钟源（左图），同时可以选择该通道的时钟源，具体时钟频率可以看MCU配置模块说明文档，并且需要提前在MCU模块里进行分配（右图）。

同时配置完时钟通道后需要将该资源映射到对应的引脚上，在前面MCU模块配置中有说明该问题。

## 6. 2 电控单元PWM配置
针对电控单元的PWM配置说明如下， ATOM需要分配整组用作电控PWM使用，同时需要在MCU单元对引脚进行分配，PWM_BASE路和PWM_Trigger路可不分配引脚。PWM_BASE路的配置如图所示，其channel class属性需要配置成 PWM_FIXED_PERIOD模式，同时在GtmTimerOutputModuleConfiguration选项中添加时钟来源，选择McuGtmAtomChannelAllocationConf_0下的GTM_CONFIGURABLE_CLOCK_0。

针对六路中的某一路PWM，例如PWM_UH_PO，其配置图关键的点在于，Channel class属性需要配置为 PWM_FIXED_PERIOD_SHIFTED,同时要勾选PWM Coherent Update选项，在GtmTimerOutputModuleConfiguration中需要分配相应的GTM_CONFIGURABLE_CLOCK_0时钟信号来源， 其他路的配置完全相同。

下图的两路pwm，IPHREFP_PO和IPHREFN_PO用于配置两路过流阈值，其PWMchannelClass需要配置成可变周期模式。


#### HSI 分配
> HSI 分配表请参见原始文档中的截图。

## 7. ICU 模块
ICU模块的配置主要包括通道配置、时钟选择、测量属性等。根据需要在IcuChannel界面添加通道，该项目加入的PWM输入如下所示。


## 7. 1 频率量获取
双击上图中添加的IcuChannel，可对每个IcuChannel进行具体的配置，以第一个通道为例，下图所示为双击进去之后的General配置界面。

IcuSignalMeasurement界面，双击上图中添加的配置选项，该配置项有四个选择，各选项含义分别为测量占空比及周期、测量信号高电平时间、测量信号低电平时间、测量信号周期。

在该项目中除了对PWM输入进行周期与占空比进行捕获，同时还可以对输入的PWM边沿就行检测，以项目的P00.8为例，配置为下降沿捕获，设检测模式为边沿检测模式。

在IcuSignalEdgeDetection界面添加边沿检测通知函数，对函数命名如下图所示。需要加边沿检测的函数需要添加对应的引脚的中断配置。

GtmTimerInputConfiguration界面为PWM输入通道配置时钟源，TC377的芯片手册DataSheet里可查看每个管脚的可用TIM通道，选择其中一个未被其他管脚选用的即可，选择TIM3的Channel3作为PWM输入P22.7的时钟源（左图）时，与PWM输出一样需要提前在MCU模块里进行分配（右图）。


## 7. 2 时间戳获取

如上两路ICU通道用于DSADC和FOC的时间戳的获取，需要将对应配置项的IcuMeasurementMode  配置为ICU_MODE_TIMESTAMP，IcuTimestampMeasurement中需要添加一个 handling buffer。

同时GTM的时钟单元也需要配置，不过针对时间戳捕获模式，不涉及滤波等参数的配置。在MCU模块中需要使能USED_BY_ICU，不需要配置引脚。


## 7. 3 边沿事件获取
边沿事件是一种很常用的ICU通道配置方式，首先在general选项卡需要将mode设置为ICU_MODE_SIGNAL_EDGE_DETECT，边沿模式，同时设置好边沿属性，上升沿或者下降沿触发。

一般边沿的捕获用于一些信号的及时处理，所以会跟中断搭配用于故障捕获，这里配置通知函数，当有边沿发生时，自动调用回调函数。

同样的需要Gtm单元的时钟配置。

这个选项卡同样会有滤波的选项，注意需要配置滤波属性时，需要将enable选项勾上，选择ChFilterMode和ChFilterTime时，区分上升沿和下降沿，这里将模式设置成DEGLITCH_WITH_UPDOWN_COUNTER上下计数的方式，由于GTM的频率为100M，这里将滤波时间配置为200，即对应200us。

同时别忘了，需要在mcu模块中配置引脚，一定不可以忘记，否则中断不能正确的触发。每一个通道可选配的引脚有多个，根据原理图选配好正确的引脚。


#### HSI 分配
> HSI 分配表请参见原始文档中的截图。

## 8. SPI 模块
SpiChannel界面可根据需要添加SpiChannel，例如项目中用到8路SPI，因此此处添加8个SpiChannel。

双击上图中添加的SpiChannel，可对每个SpiChannel进行具体的配置，下图所示为双击进去之后的General配置界面，Buffer类型配置成外部或者内部均可，但一般配置成外部较多，配置成两种不同模式时，在SPI的驱动代码中调用的函数不同，XCU项目的配置均为外部Buffer。数据长度和传输起始位的选择需根据芯片手册确定。
SpiExternalDevice界面可根据需要添加SpiExternalDevice，例如项目中用到8路SPI，因此此处添加8个SpiExternalDevice。

双击上图中添加的SpiExternalDevice ，可对每个SpiExternalDevice进行具体的配置，下图所示为双击进去之后的General配置界面，波特率根据需求进行配置，片选信号的高低需根据芯片手册确定。

SpiCsSelection界面该界面选择片选模式，当需要配置Delay时间时，应选择CS_VIA_PERIPHERAL_ENGINE模式，当不需要配置Delay时间时选择CS_VIA_GPIO模式。

SpiCsGpio界面选择片选管脚，如下图所示选择片选脚位P22.2。


### 9. DSADC模块
选择DSADC模块进入配置，首先选择General进行相关配置如下。载波时钟频率，决定了输出载波的频率上电后先停止载波输出，可以在上电后转换为Sine模式，是否使用Bit_reverse_mode，使用后输出载波频谱更平滑。


### 10. EB工程导入CFG

## 1. 首先需要将EB MCAL中的配置导出为arxml,EB中点击Im-and Exports

点击“+”，随后按照图片所示操作

选择导出的版本以及路径。

在File Name 中选择文件路径，随后点击左下角的RUN Exporter即可


## 2. Davinci导入EB MCAL
点击File->Import,在弹出的窗口中选择arxml文件即可，之后点击NEXT，选择需要导入的模块，其中CAN、LIN、ETH相关模块不要导入，需要达芬奇配置

在导入EB配置的arxml时候,ecuc和ecum模块的不要导入。这样我们才可以把EB中配置的MCAL导入到达芬奇中，并且可以在达芬奇中直接生成MCAL的代码。


## 11. 变更记录

| 变更内容 | 原因 |
|----------|------|
| DSADC CGPWM 修改为 sin mode，ICU Tim5_5/Tim5_3 增加 notification 函数 | 漏配置 |
| IPU 过流阈值 PWM（IPHREFP_PO、IPHREFN_PO）设置为周期可变 | 固定周期模式导致无法通过 MCAL 函数设定周期占空比 |
| 修改 P00.5-10、P01.6、P00.11-12、P10.0-10.2 为上拉输入 | A2 样件变动 |
| 增加 ICU 通道 NIP_OC_FLT_EI2_P22_10_L16、NIP_OC_FLT_EI1_P22_11_L17 的滤波属性 | 提高边沿捕获稳定性 |
| 修改 IGBT 短路、欠压和 KL15 的 PORT 配置 | HIL 测试故障无法触发：错误配置内部上下拉导致外部拉低时 MCU 仍检测到高电平 |
| ① 增加 ADC 通道 2 路 ② 删除 ICU 通道 3 路 ③ 提高 SPI 引脚 Port13.5/13.3 驱动等级 ④ 增删部分 PORT | B 样硬件变更 |
| 增加 12 路 ICU 通道并分配到 Core1 | IGBT 故障检测方式从周期读取 IO 状态更换为下降沿捕获 |


---

## 🔗 相关链接

- [返回 AUTOSAR 知识](./README.md)
- [返回知识库](../目录.md)

---

*原始文档：MCAL开发配置指南.docx*
*转换日期：2026-05-06*
