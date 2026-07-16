# Polyspace 使用指南

Polyspace 基于抽象解释原理的代码级静态分析和验证工具，包含 Bug Finder 和 Code Prover 两大模块。

> 📝 **博客版**：实战视角见 [代码静态分析实战](../../blog/2026/05/06/polyspace-static-analysis/)

> **Bug Finder**：使用语义分析查找运行时错误、并发问题、安全漏洞等。
> **Code Prover**：使用抽象解释法证明源码不存在溢出、除零、数组越界等运行时错误。

---

## 1. Polyspace功能简介

Polyspace是基于抽象解释原理的代码级静态分析和验证工具，由Bug Finder和Code Prover两大模块组成。

Polyspace Bug Finder：使用语义分析的方法查找代码中的运行时错误，并发问题，安全漏洞和其他缺陷。它能够帮助开发人员在编译前发现和解决潜在问题，提高代码质量。

Polyspace Code Prover：使用抽象解释法证明源码中不存在溢出，被零除，数组访问越界等运行时错误，这一功能加强了代码的可靠性。


## 2. 使用方法


## 1. 安装和配置

Polyspace可以通过MATLAB进行安装，在安装过程中，可以选择只安装Polyspace相关功能。安装完成后，进行一些基本配置。

大家的虚拟桌面中Tools/MATLAB文件夹下一般安装的有，可以直接使用。


## 2. 创建新工程

打开Polyspace后，点击“File”→“New Project”，输入工程名并选择保存路径。完成后点击Next


## 3. 导入源码和头文件

在创建新项目后，需要导入待测的.c文件。点击“Project Source Files”，选择待测的.c文件，并点击“Add Source Folders”将其添加进工程。

然后点击Next，添加头文件路径，点击“Add include Folders”，将路径添加进工程中。（如果头文件太多，手动添加麻烦，可以使用脚本，将脚本放到SRC同目录下，然后双击运行

会生成所有头文件的H文件夹，脚本会放到本文附件中）。


## 4. 参数配置


## 1. 在导入源码和头文件后，需要进行参数配置。主要配置包括代码语言，标准，编译器以及处理器内核版本等。


## 2. Macros配置界面主要配置预处理宏定义和取消已有的宏定义。


## 3. Environment Settings配置界面主要配置软件的其他环境信息。

【Code from DOS or Windows file system】：配置文件来源是哪个文件系统，用于识别路径是否区分大小写以及路径符号

【Continue with compile error】：勾选时，使能在编译错误时依旧继续，建议默认不勾选即可

【Command/script to apply to preprocessed files】:配置每个文件预处理后执行的脚本，没有这个需求的可以不配置.

【Include】：配置编译每个文件时，自动Include的文件。该配置可用于使用的编译器支持特定关键字时，代码使用了该关键字，但是Polyspace不支持该关键字的情况。通过手动模式把关键字写到一个头文件。配置方法为：点击右边的文件夹图标，在打开的界面选择对应的头文件。


## 4. Inputs&Stubbing用于配置全部变量，指针，函数参数的数据约束以及Stubbing函数。

【Constraint setup】:配置全部变量、指针、函数参数的数据约束条件，通过点击【Edit】添加对应约束。

【Ignore default initialization of global variables】:配置是否忽略默认C标准的含蓄初始化全局变量（没有明显的初始化变量，char 默认初始化为0，int 默认初始化为0，等等）。为了提高我们的代码安全性，我们要求所有的变量都必须明显地初始化，所以要勾选该选项，忽略C标准里面的默认初始化。

【No automatic stubbing】:配置是否不自动产生stubbing函数，可以用于发现未定义的函数，也可以用于手动定义stubbing函数。

【Functions to stub】:配置哪些函数为stubbing函数，当检测时不想再检测某一个确定的函数时，可以在此指定函数为stubbing函数。


## 5. Multitasking界面用于配置多任务相关配置

【Enable automatic concurrency detection】:使能自动多任务检测，用于有标准的POSIX接口的多线程创建接口函数。

【Configure multitasking manually】:使能手动配置多任务。


## 6. Coding Standards & Code Metrics界面配置代码规则检查和代码质量检测。

【Check MISRA C 2004】：勾选，则可以选择检查MISRA C 2004检查，然后选择对应的规则，可以选择custom然后点击【Edit】自定义检查条例或者装载以前定好的规则。

【Check MISRA AC AGC】：自动生成的代码的检查规则，所以我们应该是选择勾选该规则。

【Check MISRA C 2012】：None。

【Check custom rules】：检查用户定义的其他规则，按需配置即可。

【Effective Boolean types】：定义制定哪个类型的数据为boolean类型。


## 7. Code Prover Verification配置Code Prover检测的相关行为。

Code Prover Verification界面配置代码检测整个代码还是只检测模块，由于我们开发的只是其中一个模块的APP，所以我们勾选【Verify module】。这样polyspace找不到main()函数的情况下，会自动生成一个main()函数，该main()函数会执行以下操作：

初始化【Variables to initialize】里面指定的变量

调【Initialization functions】里面指定的初始化函数

按任意的顺序调【Functions to call】里面指定的函数


## 8. Precision配置检测的精度。

【Precision level】：指定检测精度等级，精度越高，耗时越久，目前使用默认的等级2即可。

【Verification level】:指定源代码的检测次数，等级越高，耗时越久，目前使用默认等级level 2即可。

【Verfication time limit】:指定检测超时时间，如果超时，检测停止，以小时为单位，如2.5表示2小时30分。

【Retype variables of pointer types】：勾选时使能允许把指针强制转换为别的类型。为了防止指针越界，建议不要勾选该选项。

【Retype symbols of integer types】：勾选时使能允许把一个整数强制转换为指针。由于我们一般不操作底层地址，所以建议不要勾选该选项。


## 9. Advanced Settings配置一些高级功能

【Command/script to apply after the end of the code verification】：选择检测结束后执行一个脚本，如果需要该功能，输入对应的脚本路径即可。

【Automatic Orange Tester】：是否使能在代码检测结束后，针对Orange的结果执行动态检测以查找运行时错误。。

【Number of automatic tests】：设置在代码检测结束后，Orange动态检测的次数。

【Maximum loop iterations】：设置在代码检测结束后，Orange动态检测最大循环次数。

【Maximum test time】：设置在代码检测结束后，Orange动态检测最长时间。

【other】：可以输入其他的polyspace option。


## 5. 分析运行

参数配置完成后，点击"Run Bug Finder"或“Run Code Prover”开始分析。分析过程中可以看到分析进度，信息输出，以及遇到的问题。（分析代码编译有问题会有红色警告，文件查找失败有黄色警告）


## 3. Polyspace结果查看

Dashboard分析结果报告显示窗口，会显示如下信息内容：

1）风险错误数量比例饼状图：红色表示高风险错误，粉红表示低风险。

2）分析覆盖度柱状图

3）错误类型及错误数量统计图

result list

1）例举出具体风险类型项，位置，数量等信息。

2）点击风险项，在Source窗口对照源码分析问题。

经过 Polyspace 分析后的代码以不同颜色标识：

| 颜色 | 含义 | 处理方式 |
|------|------|----------|
| 🟢 绿色 | 安全代码 | 无需审查 |
| 🔴 红色 | 问题代码（确定有运行时错误） | 必须立即修复 |
| 🟠 橙色 | 有风险代码（可能存在运行时错误） | 需要重点审查验证 |
| ⚫ 灰色 | 不可达代码 | 审查代码逻辑，确认是废弃还是逻辑错误 |
| 🟣 紫色 | Bug Finder 检测到的缺陷 | 根据严重程度处理 |

### 生成报告

点击 Reporting → 选择 Bug Finder 或 Code Prover → 选择文件路径和格式 → Run Report 生成报告。建议每次分析后导出 PDF 报告存档。

### 常见问题排查

| 问题 | 可能原因 | 解决方法 |
|------|----------|----------|
| 大量 Orange 结果 | Stubbing 不充分 | 在 Inputs & Stubbing 中为全局变量和函数参数添加约束条件 |
| 编译错误（红色警告） | 缺失头文件或宏定义 | 在 Include 路径中添加缺失目录，或在 Macros 中添加宏定义 |
| 分析超时 | 代码复杂度高 | 适当降低 Precision level 或增加 Verification time limit |
| MISRA 检查不生效 | 未正确勾选检查规则 | 确保在 Coding Standards 中勾选对应 MISRA 规则集 |

> **Polyspace Access**：Polyspace 还提供 Web 界面版本（Polyspace Access），允许团队通过浏览器上传和查看分析结果，支持结果对比和协作审查。适用于团队多人协作场景。

## 4. 附件

头文件自动收集脚本（将脚本放到 SRC 同目录下双击运行即可生成包含所有头文件的 H 文件夹）。

---

## 🔗 相关链接

- [返回软件测试知识](./README.md)
- [返回知识库](../目录.md)
- [Tessy 使用指南](./Tessy使用指南.md)

---

*原始文档：Confluence 导出 (000_Polyspace使用指南)*
*转换日期：2026-05-06*
