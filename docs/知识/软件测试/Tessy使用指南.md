---
tags:
  - 软件测试
---

# Tessy 使用指南

Tessy 单元测试工具使用指南，涵盖测试环境配置、用例编写、覆盖率分析、回归测试等完整流程。

> 📝 **博客版**：叙事风格的精简版见 [嵌入式单元测试实战：Tessy 从入门到覆盖率](../../blog/posts/2026-05-06-tessy-unit-test-intro.md)

> **适用场景**：嵌入式 C/C++ 代码的单元测试，支持 ISO 26262 功能安全标准。

---


## 0. 单元测试

### 0.1 单元测试的定义与目标

### 0.2 测试框架的选择
1.编写和执行测试用例：
2.断言方法：
3.测试覆盖率检测：
4.生成测试报告：
5.Unity案例：

### 0.3 测试用例的设计

### 0.4 测试覆盖率

### 0.5 ISO26262中的单元测试

### 0.6 公司单元测试过程文档

## 1. 配置Tessy

### 1.1 安装Tessy

### 1.2 打开License配置工具

### 1.3 连接License服务器

### 1.4 获取License信息

## 2. 创建测试工程

### 2.1 获取单元测试范围

### 2.2 创建工程目录

### 2.3 导出头文件（可选）

### 2.4 添加测试文件

### 2.5 分析代码
#### a) 宏定义报错
#### b) 缺失头文件
#### c) 不能识别的汇编语句
#### d) 其他问题

### 2.6 屏蔽无关函数

## 3. 编写单元测试用例

### 3.1 理解代码逻辑

### 3.2 打桩外部函数
#### a) 普通桩
#### b) 高级桩
#### c) 手写桩

### 3.3 设置输入输出变量
a）指针
b）函数指针
c）void型的指针

### 3.4 创建测试用例

### 3.5 维护测试用例
#### a) 用例命名
#### b) 输入输出描述
#### c) 测试方法&测试用例导出方法

### 3.6 编写测试步骤

### 3.7 验证测试用例

### 3.8 提高用例覆盖率

### 3.9 记录测试问题

## 4. 输出Tessy测试报告
a） 总结报告
b） 详细报告

### 4.1 导出设置

### 4.2 生成报告

### 4.3 更多报告设置

## 5. 导出单元测试用例报告

### 5.1 格式化用例描述

### 5.2 导出测试用例
#### a) 单个导出
#### b) 批量导出

## 6. 回归测试

### 6.1 比对代码更改

### 6.2 更新测试工程

### 6.3 更新测试用例

### 6.4 执行测试

### 6.5 更新测试报告


## 7. 技巧

### 7.1 协同单元测试

### 7.2 更改宏定义提高测试效率

### 7.3 对常用寄存器进行包装

## 8. 工具使用说明

### 8.1 圈复杂度工具

### 8.2 Tessy许可证排队工具

### 8.3 单元测试用例导出

## 9. 附录

## 0. 单元测试
单元测试做的事情像是无用功，多数时候看上去就只是验证了一下1+1是不是等于2，还要煞有介事的担心一些捕风捉影的边界风险。

但如果真的保证开发过程中同步进行单元测试，测试用例也是真正根据函数的需求和功能进行设计。这些验证就会起到效果，最明显的两个效果

1）规避低级错误

常在河边走，哪有不湿鞋。即使一个高明的软件工程师的出错概率极低，也很难说自己不会犯错。最基本的条件判断，数据移位也可能出错。

此时，单元测试的效果自然会体现。如果放任这种错误进入review，集成测试，不说这些环节对这种偶然错误的感应能力，发现错误后，最后还是要开发人
员去定位错误，还是一样要花大量时间。

2）代码改动验证

另一点更明显，旧代码的测试用例对代码更新后也是有意义的，正常版本升级时，大部分的需求和设计是没有发生改变的，执行旧测试用例后，得到的报告
可以佐证新的代码没有影响旧功能，增加新代码的信心。

只是这两点就足够驱动模块开发人员维护自己的测试用例了。


### 0.1 单元测试的定义与目标
单元测试是针对编写的单个函数或模块（这里是根据拆分的单元而不同）进行测试，通过编写小型、独立的测试用例来验证其内部逻辑的正确性，确保每个
组成单元都能按照预期工作。其主要目标包括：


**1. 验证功能正确性**：确保模块在正常和异常条件下的行为符合预期。

例如 `int add(int a, int b)` 函数：测试 `add(3, 4)` 应返回 7；边界测试 `add(INT_MAX, 1)` 和 `add(-INT_MAX, -1)` 确保极端情况下正确。这是单元测试最重要的功能。

**2. 早期缺陷发现**：在编码阶段即开始测试，快速捕获实现错误，减少集成测试和系统测试阶段的修复成本。

例如 `char* concatenate(char* str1, char* str2)` 函数：编码阶段就能发现内存溢出、字符串未正确拼接等问题。越早发现，修复成本越低。

**3. 支持重构与维护**：单元测试作为模块行为的文档，帮助理解现有代码逻辑。重构时运行旧测试用例，验证改动未影响原有功能的正确性。


### 0.2 测试框架的选择
在进行C语言单元测试时，选择适合的测试框架至关重要。这些框架通常提供了以下功能：

1.编写和执行测试用例：
单元测试工具允许开发人员编写测试用例，这些用例定义了代码的各个部分应该如何工作。

这些测试用例是函数的输入输出，他们可能以代码，表格，或者脚本的形式输入和保存。

工具能够执行这些测试用例，并自动检查代码的实际行为是否与预期一致，也就是比较程序需求的输出和程序实际的输出作比较。

2.断言方法：
断言是单元测试中的关键部分，用于验证代码的行为。

单元测试工具通常提供丰富的断言方法，如等于、不等于、大于、小于、包含等，以及更复杂的自定义断言。

用于在测试代码中检查条件是否成立，如果不成立则测试失败。常见的断言宏包括相等断言、不等断言、为真断言、为假断言等。
例如，Unity框架提供了TEST_ASSERT_EQUAL_INT、TEST_ASSERT_TRUE等断言宏。

单元测试的实际要做的就是给定输入，确定输出的正确性，所以一系列的断言就是单元测试里的验证环节。

3.测试覆盖率检测：
单元测试工具通常支持测试覆盖率检测，即检查测试用例覆盖了代码的哪些部分。

这有助于开发人员了解测试的全面性和完整性，并找出未覆盖的代码区域进行补充测试。

所谓覆盖率就是测试用例运行过程中对被测代码的执行覆盖率，也就是：执行过的目标数/总的需要执行的目标数。

根据覆盖目标不同可以分为函数覆盖率，语句覆盖率，分支覆盖率，MC/DC覆盖率。

覆盖率是单元测试可靠性的保证，不管测试结果如何，覆盖率不够都会让结果的可信程度降低。

举例来说，测试函数A中的一个if else语句，如果测试用例在执行过程中只执行过其中的一个分支，就停止了单元测试，这时候分支覆盖率就是不足的。测
试结果只能保证在这个分支下函数有效，其他情况就是没覆盖到，不能验证结果。

在提高覆盖率过程中也可以发现一些废弃或者不可达的代码。

通过提高覆盖率，可以确保更多的代码路径被测试覆盖，从而提高测试的充分性。这有助于发现潜在的错误和缺陷，提高软件的健壮性和可靠性。

4.生成测试报告：
单元测试工具能够生成详细的测试报告，包括测试结果、测试覆盖率、测试时间等信息。

这些报告有助于开发人员理解测试结果，并找出代码中的问题。

在测试执行完毕后，框架会生成测试结果报告，包括测试通过的数量、失败的数量以及失败的详细信息等。

5.Unity案例：
如上所述，框架提供的功能几乎覆盖测试的整个流程，下面展示一个使用开源的unity测试一段个加法函数的过程，unity是一个开源的C语言测试框架，

函数声明定义my_functions.h，my_functions.c

// my_functions.h
#ifndef MY_FUNCTIONS_H
#define MY_FUNCTIONS_H

int add(int a, int b);

#endif // MY_FUNCTIONS_H

// my_functions.c
#include "my_functions.h"

int add(int a, int b) {
return a + b;
}

测试用例编写

// test_my_functions.c
#include "unity.h"
#include "my_functions.h"

void test_add_positive_numbers(void) {
TEST_ASSERT_EQUAL(5, add(2, 3));
}

void test_add_negative_numbers(void) {
TEST_ASSERT_EQUAL(-5, add(-2, -3));
}

void test_add_mixed_numbers(void) {
TEST_ASSERT_EQUAL(-1, add(2, -3));
}

void test_add_zero(void) {
TEST_ASSERT_EQUAL(0, add(0, 0));
TEST_ASSERT_EQUAL(2, add(2, 0));
TEST_ASSERT_EQUAL(2, add(0, 2));
}

int main(void) {
// Unity
UNITY_BEGIN();

//
RUN_TEST(test_add_positive_numbers);
RUN_TEST(test_add_negative_numbers);
RUN_TEST(test_add_mixed_numbers);
RUN_TEST(test_add_zero);

// Unity
return UNITY_END();
}

编译执行测试用例

gcc -o test_runner unity.c my_functions.c test_my_functions.c

./test_runner

测试报告输出

-----------------------
RUNNING ALL TESTS
-----------------------
test_add_positive_numbers: PASS
test_add_negative_numbers: PASS
test_add_mixed_numbers: PASS
test_add_zero: PASS

-----------------------
ALL TESTS PASSED
-----------------------

Unity自身不支持覆盖率统计，但gcc附带的gcov工具可以统计代码覆盖率，包括函数覆盖率和分支覆盖率。

虽然开源工具也有很多优异的功能，但对大量的测试用例编写工作，操作还是过于复杂了。使用Tessy来编写测试用例要更方便协作和迭代。


### 0.3 测试用例的设计
101_Tessy单元测试三种测试方法和三种测试用例导出方法 - Solution-AP 新能源团队 - AE Community

测试用例是单元测试的核心，其设计直接影响到测试的质量和效果。在设计测试用例时，有以下原则：

边界值分析：测试输入数据的边界值，因为边界值往往是出错最多的地方。例如，对于一个接受整数输入的函数，应测试其能接受的最大值、最小值和接近
这些值的边界值。

等价类划分：将输入数据划分为若干个等价类，从每个等价类中选取一个或多个代表性数据进行测试。这样可以减少测试用例的数量，同时保证测试的全面
性。

错误注入：故意在代码中引入错误或异常条件，然后编写测试用例来验证这些错误或异常是否得到了正确处理。这有助于发现代码中的潜在缺陷。


### 0.4 测试覆盖率
测试覆盖率是衡量测试质量的重要指标之一。它表示测试用例覆盖了多少代码路径和条件。常见的有下面这些指标：

语句覆盖：确保每个代码语句至少被执行一次。

分支覆盖：确保每个分支路径都被测试到，包括真分支和假分支。

条件覆盖：确保每个条件都被测试到，包括条件的真值和假值。

MC/DC覆盖：对于需要高可靠性和安全性的汽车软件，可能需要满足更严格的MC/DC（Modified Condition/Decision Combination）覆盖要求。

不同的软件对于覆盖率的指标是不同的，对于要求到的覆盖率类型，应该尽量100%覆盖。下面是一些提高覆盖率的建议：（待补充）

编写更多的测试用例：针对每个函数或模块编写更多的测试用例，以覆盖更多的代码路径和条件。这里的多是有要求的，比如目的是分支覆盖100%，这个时
候并不是直接用代码里的分支条件去覆盖。

使用代码覆盖工具：使用代码覆盖工具来分析测试用例覆盖了多少代码。这些工具可以生成代码覆盖率报告，帮助开发人员了解哪些代码路径还没有被测试
覆盖到。

优化测试用例：根据代码覆盖率报告，优化测试用例以覆盖更多的代码路径和条件。


### 0.5 ISO26262中的单元测试

在ISO26262-6 中，对软件单元测试有一些描述，

++表明必要，+则可选。所以可以得知，

1a：对所有要求ASIL的软件测试用例，需求分析都是生成测试用例的基本方法。

1b：而后的等价类是根据输入输出进行分类来划分等价类，对于大部分函数，分支通常就是等价类的划分依据，这里就考虑if，while，for，switch这些条件
分支转换的语句。

1c：边界值有两个含义，一个是比较值的边界，另一个是数据范围的边界，对于比较值的边界，采用3点或者5点发覆盖即可，对于数据范围，覆盖主要考虑
上下溢出。（对数据范围的单元测试我也不知道做到什么程度算完全，目前看至少要保证有用户输入的接口要测试）

1d：这一条很抽象，我没有理解，似乎应该出现在回归测试中，对经验错误的重复测试。

一般情况下，我们要有需求分析，等价类分析，和边界值分析这三种用例生成方法。

下面是覆盖率的一些要求，

根据ASIL的等级，需要满足语句覆盖，分支覆盖，MC/DC覆盖。

这三种覆盖率的含义

一、语句覆盖（Statement Coverage）

定义：语句覆盖是指选择足够的测试用例，使得运行这些测试用例时，被测程序的每一个语句至少执行一次。

计算公式：语句覆盖率=（至少被执行一次的语句数量）/（可执行的语句总数）×100%。

特点：

语句覆盖是最基础的覆盖方式，可以检验每个可执行语句。

即使语句覆盖率达到了100%，也不能保证发现所有的逻辑错误。

二、分支覆盖（Decision Coverage）/判定覆盖（Branch Coverage）

定义：分支覆盖（判定覆盖）是指选择足够的测试用例，使得运行这些测试用例时，每个判定的所有可能结果至少出现一次。即程序中每个判断的取真分支
和取假分支至少经历一次。

计算公式：判定覆盖率=（判定结果被评价的次数）/（判定结果的总数）×100%。

特点：

若判定覆盖达到100%，则语句覆盖必为100%。

但不能确保每个组合条件都分别覆盖到真/假情况，所以同样可能存在逻辑错误未被发现。

三、MC/DC覆盖率

定义：MC/DC覆盖率是一种更高级别的测试覆盖率指标，它要求程序中的每个判定中的每个条件都要独立地影响判定结果，并且每个判定和每个条件都要至
少取到一次所有可能的结果。

特点：

MC/DC覆盖强调条件之间的独立性，即每个条件都要能够独立地影响判定结果，这有助于发现那些由于条件间依赖关系导致的错误。

相比条件组合覆盖等其他高级覆盖策略，MC/DC覆盖能够在保证较高覆盖度的同时减少测试用例的数量。

虽然覆盖率是单元测试的重要指标，但需要说明的是，时间充裕的情况下，设计用例是依照上面所说的需求，边界值，等价类等。在进行完后，此时观察覆
盖度指标，就可以反映出代码问题，比如废弃代码，不可达代码。处理完这些问题，再补充合适的用例，达到更高的覆盖率。

如果一开始就冲着覆盖率测试，很容易陷入代码是1+1等于3，测试是3等于1+1的“自证”陷阱。

但好的单元测试对测试者压力其实也很大，既要理解函数的正确意图，也要考虑好输入输出的范围和分类，复杂度低的函数还好，高复杂度的函数很需要由
开发人员本人来设计测试用例。

这里涉及到协同的问题，Tessy提供了不少方式让两个人共同测试同一个工程，可以考虑让某个人集中编写简单函数的测试用例，对复杂度高的函数，由开发
者本人编写，而后合并。


### 0.6 公司单元测试过程文档

模板在内网网盘：AE管理体系文件\COP02产品开发及验证确认过程(PDVV)\02_产品软件开发及验证\01_模板

这些文件的填写是除了测试报告外单元测试重要的文档输出。

目前测试报告公司没有提供模板，考虑要自己存档一些关键信息，比如每次测试的PDF报告，每次测试的覆盖率数据截图，每次测试的信息。如果后续需要
测试报告，这些东西可以代替。


## 1. 配置Tessy


### 1.1 安装Tessy
- 联系相关的IT&管理员

内网机自行安装，安装包在SVN获取

30X_Tessy安装包 - Solution-AP 新能源团队 - AE Community


### 1.2 打开License配置工具
- 在Tessy安装完成后，搜索License Manager，打开License配置工具。


### 1.3 连接License服务器
- 连接license服务器: 在配置工具中点击License->Server输入License服务器的IP地址和端口号。这个地址可能会变化，询问软件管理获取最新的。
Address: lm01.hirain.local
Port：10000

- 本地License服务器: 在Server选项卡里也可以配置本地License服务器。


### 1.4 获取License信息

- 点击Info可以获取License的使用情况。


## 2. 创建测试工程


### 2.1 获取单元测试范围
- 确定需要进行单元测试的代码模块。获取软件架构设计说明书，软件详细设计文档，根据文档和任务确定单元测试的范围。依据软件版本和测试目标创建工
程。

点击 新建工程，在弹出的界面中输入工程名，Project Root 中选择工程所在绝对路径，其余默认即可，点击OK
注意：工程名称以及所在路径不能包含中文字符和空格

创建工程时可以配置工程的数据的存放位置，默认即可。

点击OK后稍等即可成功创建工程。

点击Open Project，打开工程。


### 2.2 创建工程目录
- 在合适的位置创建新的工程目录，用于存放工程文件。

Tessy的层次如下图所示，从大到小为：Collection--文件夹（可选）--源文件--函数–CASE–STEP

下图箭头处可以创建各个层级，组织工程目录。

新工程内没有内容，可以依据需求创建目录。通常来说，按照工程结构来创建文件夹，文件夹内按单个c文件创建模块测试是比较合理的结构。

具体按照文档的结构划分，以便于和文档对应。也可以按照项目代码的实际文件夹结构创建。下面举例说明：

该程序包含三个源文件，对应的创建三个MOUDLE，如图所示：

单击选中当前模块，在General界面选择编译器，Environment选择GCC，Kind of Test选择Unit。


### 2.3 导出头文件（可选）
- 使用提供的脚本或Tessy功能导出所需的头文件。

如果需要经常修改头文件或者回归测试，可以考虑创建工程时使用批处理脚本导出到单个文件夹，这样的好处是，回归测试时相对方便对比，修改头文件.

下面是一个脚本，再项目根文件夹下创建一个xxx.py文件，双击执行后即可得到

import os
import shutil

#
source_dir = os.path.dirname(os.path.realpath(__file__))

# auto_h
destination_dir = os.path.join(source_dir, 'auto_h')

try:
#
if os.path.exists(destination_dir):
for filename in os.listdir(destination_dir):
file_path = os.path.join(destination_dir, filename)
try:
if os.path.isfile(file_path) or os.path.islink(file_path):
os.unlink(file_path)
elif os.path.isdir(file_path):
shutil.rmtree(file_path)
except Exception as e:
print('Failed to delete %s. Reason: %s' % (file_path, e))
else:
os.makedirs(destination_dir)

# .h
files_copied = {}
for root, dirs, files in os.walk(source_dir):
for file_name in files:
if file_name.endswith('.h'):
base_name = os.path.splitext(file_name)[0]
extension = os.path.splitext(file_name)[1]
new_file_name = file_name
counter = 1

#
while new_file_name in files_copied.values() or os.path.exists(os.path.join(destination_dir,
new_file_name)):
new_file_name = "{}_{}{}".format(base_name, counter, extension)
counter += 1

#
src_path = os.path.join(root, file_name)
dst_path = os.path.join(destination_dir, new_file_name)
try:
shutil.copy2(src_path, dst_path)
files_copied[file_name] = new_file_name

#
if new_file_name != file_name:
print("File '{}' renamed to '{}' due to existing name.".format(file_name,
new_file_name))
except Exception as e:
print("Error copying file '{}': {}".format(file_name, str(e)))

print("All .h files have been copied successfully.")

except Exception as e:
print("An error occurred: {}".format(str(e)))

#
input("Press Enter to exit...")


### 2.4 添加测试文件
- 将源代码文件(.c)添加到测试工程中。

按下图依次点击创建好的模块，打开属性页，可以在source选项卡里找到输入源文件。

源文件选择很简单，一般情况就选对应的.c文件。

include头文件有几种方式

第一个选项是每次选择一个路径，可以重复操作插入多条

第二个选项是添加多个路径，可以递归的添加工程的全部头文件

第三个选项是直接编辑输入头文件路径，如果多个模块头文件一致，这个最方便


### 2.5 分析代码
- 使用Tessy的分析功能对代码进行分析。
- 根据Tessy的提示解决配置过程中的任何错误。

如图所示，先点击选中MOUDLE，然后点击分析按钮。

也可以点击模块前的列表箭头，一样是分析。

分析过程中可见一些Console报错，常见的有：

#### a) 宏定义报错
源码编译环境如果定义了一些宏，也要在测试工程中添加，例如_HIGHTEC，TASKING_，可以根据报错添加。

如果需要添加宏定义，点击 Defines，再点击图标，可以添加宏定义。

#### b) 缺失头文件
通常是以为编译环境的变化，引入了不存在的头文件，例如_GNUC_，屏蔽这条指令，或者直接修改代码里的宏即可。

#### c) 不能识别的汇编语句
使用汇编的地方都要尽量屏蔽。

#### d) 其他问题
可以参考team里的问题汇总
分析没有报错并不意味着完全没有问题，后面执行用例的时候还需要一些修改。

选中被测函数，点击TIE 界面，可以看到识别出来的输入和输出接口。
如果需要进行改动，可在想要修改的位置修改测试对象接口。


### 2.6 屏蔽无关函数
导入和分析后可见函数列表，

函数列表常见到很多不属于源文件的函数被导入，这里面通常是一些头文件里的内联函数，Tessy在分析过程中也把这些引入工程，这样会影响我们测试
报告的可读性和美观性.需要屏蔽这些函数。

点击如图位置的过滤器。

在这个位置就可以选择希望屏蔽的函数了。

屏蔽无关函数很重要，直接影响输出的报告和后续用例的导出以及覆盖率的审查。所以添加模块的时候就要注意。


## 3. 编写单元测试用例
在处理好工程后，就可以开始测试用例的编辑了.

首先要说明的是MODULE的测试用例结构。

每个函数下可以创建多个TESTCASE，每个TESTCASE下可以创建多个步骤。

需要说明的是，CASE适合作为我们测试的最小单元，一是方便管理分支覆盖，圈复杂度和CASE数目对应就可以完成覆盖。

另外，每个CASE，Tessy都会独立的执行，两个CASE间不会被影响，而step是会相互影响的，上一次函数遗留或者修改会影响下一次执行，这一点对维护测
试影响很大，例如CASE相互之间变换执行顺序是不会改变结果的，而step在换位置后很可能走向不同分支。

步骤具备覆盖一个分支的能力，但不该使用一个CASE的多个步骤覆盖不同分支，如果有多个STEP他们应当是补充关系。

避免出现一个复杂函数只有一个CASE，却有多个step的情况。


### 3.1 理解代码逻辑
- 分析被测函数的逻辑，确定输入输出关系。

在分析完代码后，可以查看CV页面，这个页面是用来查看覆盖情况的，也可以帮助我们梳理函数逻辑，或者绘制函数流程图。

点击流程图中的框图，可以在下面的源码页面看到这部分代码的高亮。

结合函数的作用，对每个分支进行分析了解，为后续创建CASE做准备。另外这个流程图对绘制函数流程图也有一些帮助，在补充流程图的时候可以参考。


### 3.2 打桩外部函数

- 在TIE中为外部调用创建桩函数，以便隔离测试。

按如图顺序点击可以看到TIE界面的功能，函数使用的其他函数需要打桩.

因为单元测试我们关心的是测试的'单元'，也就是被测函数，所以被测函数中使用的其他函数默认他们的执行是可以正常输入输出的(可能输出异常).这就需要
对函数进行打桩.

举个例子，如果我们的函数测试的是一个电机驱动函数，涉及到IO的操作，在TESSY里，显然不能调用操作物理设备的函数，去读取或者操作IO.如果不能
按我们的需求返回不同的状态，我们是不能对所有分支进行测试的.所以替换原有的函数，在测试过程中是很常见的.
在TESSY中这个操作在TIE界面中进行.

右键桩函数后可以看到多个选择

stub是普通桩，Advanced stub是高级桩.
打桩在TESSY中可以分三种

#### a) 普通桩
这种桩对应的函数是那种不关注输入，也没有返回值的函数.设置为普通桩后就不需要其他输入了.但如果函数里使用了他的返回值，编译时会报错.(常见的报
错 : 没打桩或者只打了普通桩)

以下四种情况通常可打普通桩：

1. 函数没有返回值、没有形参
2. 函数不影响后续实现以及变量
3. 函数本身有返回值但无需使用
4. 函数有形参，但不观测

例： STUB_1()在当前 .c文件中没有定义，如果直接执行测试用例会报未定义错误。

在TIE界面将其打普通桩，解决报错。

#### b) 高级桩
需要输入或者返回值的函数，设置为高级桩后，需要设置其输入输出返回值的使用情况，通常Tessy会自动识别，用户去修改不需要的就可以。

以下两种情况建议打高级桩：

1. 使用到桩函数的返回值
2. 函数有形参且需要接口传检测

例1：被测函数中用到了STUB_2()函数的返回值，如果对函数的返回值，如果对STUB_2()函数打普通桩会报无返回值的错误。

在TIE界面将其打高级桩，并在TDE界面设置其预期返回值。

例 2：对STUB_3()函数进行传参检测，需要给该函数打高级桩，第一个接口为返回值，其余为形参接口。

#### c) 手写桩
如果需要特殊的处理,或者返回值不方便在高级桩输入，可以手写桩函数，在TDE界面中

如果需要让桩函数有额外的功能 ，如传参检测 、局部数据处理、多传参检测函 、函数实现变更等，可以进行手写桩 。

例：

想要监控对 STUB_3()函数每一次参传递是否正确，可以对其打普通桩，通过手写桩实现传参检测。步骤如下：

1）在TIE界面新建一个数组。

2）对STUB_3()打普通桩，在TDE的Stub Functions界面手写桩函数的代码。

3）对vol数组输入预期值，检查测试结果。


### 3.3 设置输入输出变量
和高级桩的设置类似，为了到达特定分支，外部的全局变量，函数参数的输入也是重要的信息

TIE界面里可以设置是否使用他们.设置完毕后可以在TDE界面进行设置

指针相关测试

a）指针
与指针有关的测试要点在于构建合适对象，将地址传入接口。

例：

在 TIE界面设置输入出接口

在TDE界面设置指针的具体指向，赋值后执行测试

b）函数指针
与函数指针有关的测试要点在于构建类型相同对象，并将地址传入指针接口。

例：

在TIE界面设置函数指针的输入出接口

在TDE的Declarations/Definition界面实现函数的声明和定义，并让指针指向这个函数，赋值后执行测试

c）void型的指针
例：

需要新建一个有类型的全局变量，然后将指针指向该变量，将变量地址传入指针接口


### 3.4 创建测试用例
- 根据代码逻辑设计覆盖各种场景的测试用例。

按下面的操作可以打开Test Items界面.在这个界面可以进行CASE和STEP的创建.

如果是MCDC覆盖，建议对每个分支创建一个CASE，也就是对每个独立的判断语句的每个独立情况设立CASE.使CASE数大于等于圈复杂度.也就是TC/C
(Test Case To Complexity Ratio)大于1.


### 3.5 维护测试用例
- 确保测试用例的清晰和可维护性。

在创建CASE时要考虑后续的可读性和可维护性，具体说单元测试过程中需要填写下面这些文档

其中，测试用例的统计和导出是比较麻烦的一环.如下图

对每个用例都要填写信息，所以我们需要一个一个填写，这显然要花费大量时间，好在有一些工具可以使用
我们目前使用的用例导出软件如图所示

为了使用它，下面这些信息需要填写

#### a) 用例命名
首先是对用例进行命名，通常我们把用例的名称命名为他所覆盖的分支的条件情况，这样后续即使增加或者删除了分支，，也很容易定位修改的位置。

先选择用例

然后点击属性页面输入名字

这里对用例进行命名是可选的，如果函数非常简单，用例不必命名，不会影响导出。

#### b) 输入输出描述
TIE界面里选中一个函数，在Propreties中的Description里填写内容，前半部分是对测试输入的描述，后半部分是对输出的描述，使用&分割。

每一个函数都要有Description，导出时没有Description会报错。

#### c) 测试方法&测试用例导出方法
详见：

301_Tessy单元测试用例导出脚本

101_Tessy单元测试三种测试方法和三种测试用例导出方法

102_Tessy描述添加与测试技巧

填写用例名称

选中一条CASE，在其Test Definition中的Description中填写描述，先填写测试方法，其后使用;分割后填写测试用例导出方法

下面是可选的一些选项
测试方法：
- 基于需求的测试 Requirement-base test
- 接口测试 Interface test
- 故障注入测试 Fault injection test
- 资源使用测试 Resource usage test
- 背靠背测试 Back to back test
测试用例导出方法：
- 需求分析 Analysis of requirements
- 需求分析及等价类 Analysis of requirements and Analysis of equivalence classes
- 等价类的生成和分析 Generation and analysis of equivalence classes
- 等价类及边界值分析 Analysis of equivalence and boundary values
- 边界值分析 Analysis of boundary values
- 错误猜测测试 Error guessing test

每一个CASE都需要Description，导出时也会报错。


### 3.6 编写测试步骤
- 明确每个测试用例的执行步骤和预期结果。

在每个新的CASE下都有一个空白的STEP，在其中输入合适的inputs达成分支覆盖.


### 3.7 验证测试用例
- 执行测试用例，验证其有效性。

选取函数，点击RUN按钮可以开始执行测试用例，

也可以对执行情况进行设置

在这里有选择覆盖率指标的选项。

跑完如图所示

跑不了的参考200_Tessy错误分类总结 - Solution-AP 新能源团队 - AE Community

自己排除错误推荐使用Debug功能

用Debug找出运行时错误


### 3.8 提高用例覆盖率
- 使用Tessy的覆盖率分析工具，确保测试覆盖所有可达代码。

查看CV页面，观察未覆盖分支。

右上角的MC/DC覆盖可以参考来补全用例，右下角的C0C1是语句和分支覆盖的信息，可以点击查看分支的实际走向。


### 3.9 记录测试问题
- 记录测试过程中发现的任何问题。

建议记录测试中所有的特例，比如添加的宏，修改的代码等等，这样方便在回归测试时重新覆盖。


## 4. 输出Tessy测试报告
Tessy可以导出单元测试的报告，形式是PDF，如图所示，可以输出单元测试的信息，分为总结报告和详细报告两种

a） 总结报告

b） 详细报告

下面介绍输出报告文件的过程


### 4.1 导出设置

- 在Tessy中配置测试报告的输出格式和路径。

黄色区域用来生成报告，通常我们需要整个工程的总结报告，和各个模块的详细报告。
报告中的信息是可以配置的，例如在下图中的勾选项，可以根据需要勾选和去除。

还有一些信息，在这个界面并不能去除，可以设置Tessy的设置，直接不包含这些信息，报告中自然也没有了。
进入Preferences

选择Metrics，根据需要关闭即可


### 4.2 生成报告
- 运行测试后，使用Tessy的报告功能生成详细的测试报告。

这一步注意生成的路径，Output文件夹可以使用一些描述来分组比如

$(PROJECTROOT)\report\$(MODULE)

全部的token如下：


### 4.3 更多报告设置


## 5. 导出单元测试用例报告


### 5.1 格式化用例描述
- 确保测试用例的描述清晰，详细。


### 5.2 导出测试用例
- 使用Tessy的导出功能，生成测试用例文档。

用例脚本的导出

#### a) 单个导出
选中需要生成 Script 脚本的函数，单击 Export；

更改 Directory 为目标路径，更改 Type 为 TESSY Script；

Conversion 选择 None，Export Options 选择 Input and expected values；

单击 OK，等待 Script 脚本文件生成

#### b) 批量导出
在 Test Project 界面，单击鼠标右键；

选择 Database Backup 下的 Save；

Modules and Tasks 中选择需要生成 Script 脚本的 C 文件或者模块；

更改 Output Folder 为目标路径；

单击 OK，等待所有 Script 脚本文件生成


## 6. 回归测试


### 6.1 比对代码更改
- 检查代码的变更，确定影响范围。

在更新前建议对比版本间代码差异，对变动情况有个大致了解，对于没有更新的部分做区分，减少后续工作量.

在比对过程中要注意对之前在单元测试过程中修改的部分要同步上去，比如屏蔽或添加的宏定义，辅助测试的全局变量等等.不然又要重蹈覆辙.

下面是WinMerge工具


### 6.2 更新测试工程
- 根据代码变更更新测试工程配置。

重新分析模块，代码变化可能导致接口变化。

切换至IDE页，可以看到新旧接口的对比，点击右上角commit即可切换至新接口。

对新增加的接口需要进行配置，可以点击文件或者函数的TIE界面进行配置


### 6.3 更新测试用例
- 调整或新增测试用例以覆盖变更的代码。


### 6.4 执行测试
- 运行测试用例，确保变更未引入新问题。


### 6.5 更新测试报告
- 根据回归测试结果更新测试报告。


## 7. 技巧


### 7.1 协同单元测试
Tessy提供了多种方式传递测试用例，经常遇到的是不同模块的单元测试要合并到一个工程，这个时候，有几种情况

如果是以源文件为单位导入测试用例，点击MOUDLE后右上角导入导出即可，这里导出的是tmb文件

如果是导出单个函数，点击函数后采取相同操作，然后可以导出excel文件或者tessy脚本等几种格式

这几种格式本质上都是对测试用例的输入输出进行记录，我们选用tessy script为例，其内信息如下

如果要合并两个人的case，这时候可以考虑导出双方的函数的测试信息，对excel或者script进行合并，然后再导入


### 7.2 更改宏定义提高测试效率
（这个方法要修改代码，并不推荐，只在测试是发现Tessy因为循环卡死时考虑）

单元测试只关心单元内部的逻辑正确性，在一些情况下，可以对代码中的宏进行修改，提高测试效率，比如下图中的代码，里面有一个LoopCounter的计数
循环，我们在单元测试的时候肯定要让这个循环跑完的，但不同于正常的程序运行，tessy对这种循环中产生的信息还会进行记录，通常这个循环是数以千计
的，在运行测试的时候会占用大量时间，却完全没有意义。

针对这种情况，考虑使用

#undef TLE5012_TIMEOUT_CNT

#define TLE5012_TIMEOUT_CNT 0xf

让循环次数降低，结果并没有不同。


### 7.3 对常用寄存器进行包装
对地址，寄存器的直接使用也会影响单元测试，tessy中没办法访问指定的地址，对于读写地址后，过程中该地址上的变量不需要变化的，通常采用创建全局
变量替换的方式进行单元测试，可以赋初值和读输出即可。但如果存在多次使用的，运行过程中会改变的，就不能用变量替换，比如系统时间寄存器，在单
片机上，该值会随时间变化，在测试过程中并没有这个寄存器，这个时候简单的创建变量也不行，我采用了define这个寄存器为函数的方法。函数就可以打
桩，给出变化的输入输出。


## 8. 工具使用说明


### 8.1 圈复杂度工具
Tessy报告中包含了很多信息，其中就包括圈复杂度，但生成Tessy报告需要一定的时间，为了保证开发过程中实时了解函数的圈复杂度，可以使用开源软件
Lizard，这是一个开源的圈复杂度分析器，支持多种语言，唯一一个不太好的地方是这是一个命令行工具，指令如下

usage: lizard [options] [PATH or FILE] [PATH] ...

lizard is an extensible Cyclomatic Complexity Analyzer for many programming
languages including C/C++ (doesn't require all the header files). For more
information visit http://www.lizard.ws

positional arguments:
paths list of the filename/paths.

optional arguments:
-h， --help show this help message and exit
--version show program's version number and exit
-l LANGUAGES, --languages LANGUAGES
List the programming languages you want to analyze. if
left empty， it'll search for all languages it knows.
`lizard -l cpp -l java`searches for C++ and Java code.
The available languages are: cpp， java， csharp，
javascript， python， objectivec， ttcn， ruby， php，
swift， scala， GDScript， go， lua， rust， typescript
列出要分析的编程语言。如果如果留空，它将搜索它知道的所有语言。'Ligal-L CPP-L java '搜索C++和java代码。
cpp， java， csharp，javascript， python， objectivec， ttcn， ruby， php， swift， scala， GDScript， go， lua， rust， typescript

-V， --verbose Output in verbose mode (long function name)

-C CCN， --CCN CCN Threshold for cyclomatic complexity number warning.
The default value is 15. Functions with CCN bigger
than it will generate warning
圈复杂度数警告的阈值，默认值为15，>15会产生警告。

-f INPUT_FILE， --input_file INPUT_FILE
get a list of filenames from the given file
根据给出的文件获取文件名列表

-o OUTPUT_FILE， --output_file OUTPUT_FILE
Output file. The output format is inferred from the
file extension (e.g. .html)， unless it is explicitly
specified (e.g. using --xml).
根据格式输出到文件

-L LENGTH， --length LENGTH
Threshold for maximum function length warning. The
default value is 1000. Functions length bigger than it
will generate warning
最大函数长度阈值警告，默认1000，超过报警

-a ARGUMENTS， --arguments ARGUMENTS
Limit for number of parameters
-w， --warnings_only Show warnings only， using clang/gcc's warning format
for printing warnings.
http://clang.llvm.org/docs/UsersManual.html#cmdoption-
fdiagnostics-format
打印警告，只显示warning，clang/gcc's格式

--warning-msvs Show warnings only， using Visual Studio's warning
format for printing warnings.
https://msdn.microsoft.com/en-us/library/yxkt8b26.aspx
打印警告，只显示warning，Visual Studio's格式

-i NUMBER， --ignore_warnings NUMBER
If the number of warnings is equal or less than the
number， the tool will exit normally; otherwise， it
will generate error. If the number is negative， the
tool exits normally regardless of the number of
warnings. Useful in makefile for legacy code.
如果警告数等于或小于number，则工具将正常退出；否则，它将生成错误。
如果数字为负数，则工具正常退出，无论警告的数量。
在遗留代码的makefile中很有用。

-x EXCLUDE， --exclude EXCLUDE
Exclude files that match the pattern. * matches
everything， ? matches any single character，
"./folder/*" exclude everything in the folder
recursively. Multiple patterns can be specified. Don't
forget to add "" around the pattern.

排除与模式匹配的文件。*匹配一切？匹配任何单个字符，“/folder/*”递归地排除文件夹中的所有内容。
可以指定多个模式。不要忘了在模式周围加“”号。

-t WORKING_THREADS， --working_threads WORKING_THREADS
number of working threads. The default value is 1.
Using a bigger number can fully utilize the CPU and
often faster.
默认使用线程数是1，大于这个数会更分的利用cpu或者运行的更快。

-X， --xml Generate XML in cppncss style instead of the tabular
output. Useful to generate report in Jenkins server
生成cppncss样式的XML而不是表格输出。在Jenkins服务器中生成报表很有用

--csv Generate CSV output as a transform of the default
output 生成CSV输出作为默认输出的转换

-H， --html Output HTML report
-m， --modified Calculate modified cyclomatic complexity number ，
which count a switch/case with multiple cases as one
CCN.
计算修正的圈复杂度数，它将一个switch/case视为一个CCN。

-E EXTENSIONS， --extension EXTENSIONS
User the extensions. The available extensions are:
-Ecpre: it will ignore code in the #else branch.
-Ewordcount: count word frequencies and generate tag cloud.
-Eoutside: include the global code as one function.
-EIgnoreAssert: to ignore all code in assert.
-ENS: count nested control structures.

使用扩展。可用的扩展包括：
-Ecpre：它将忽略#else分支中的代码。
-Ewordcount：统计词频并生成标签云。
-Eoutside：将全局代码作为一个函数。
-EIgnoreAssert：忽略assert中的所有代码。
-ENS：计数嵌套控制结构。

-s SORTING， --sort SORTING
Sort the warning with field. The field can be nloc，
cyclomatic_complexity， token_count， p#arameter_count，
etc. Or an customized field.
用字段对警告进行排序。场可以代码行数，圈复杂度，令牌数，参数数或自定义字段。

-T THRESHOLDS， --Threshold THRESHOLDS
Set the limit for a field. The field can be nloc，
cyclomatic_complexity， token_count， parameter_count，
etc. Or an customized file. Lizard will report warning
if a function exceed the limit
设置字段的限制数。可以代码行数，圈复杂度，令牌数，参数数或自定义字段。
如果函数设置超过了限制数会报警。

-W WHITELIST， --whitelist WHITELIST
The path and file name to the whitelist file. It's
'./whitelizard.txt' by default. Find more information
in README.
设置白名单， 默认'./whitelizard.txt'

常用的使用方式是

cd /.../...你的代码目录

（1）lizard 默认递归检测文件下的所有文件

（2）lizard -o check.txt 将所有文件输出到某个文件

（3）lizard -C 15 检测CCN超过15

（4）lizard -C 15 .\yingjiafupan\run_fupan.py 检测某个文件CCN超过15

为了方便使用lizard，用python整了个界面，可以复制代码直接查看圈复杂度，

使用时复制函数定义，可以直接复制整个文件进入检测区.然后点击分析圈复杂度，就可以获得圈复杂度列表，可以点击最下方批量复制结果，导出所有的函
数圈复杂度.

需要注意的是,这个工具只建议用来参考，和tessy的结果可能不完全吻合，最终圈复杂度仍然以tessy报告为准.


### 8.2 Tessy许可证排队工具
Tessy软件的许可证资源很多时候是紧缺的，碰到比较急的任务，只能过一会打开看一眼，给人精神和肉体的双重折磨，在等待过程中，发现Tessy提供了一
些工具获取许可证使用情况，可以很方便的进行自动排队，结合Py，开发了一个脚本，读取许可证的使用情况，有空位就会启动tessy，脚本是针对我的这个
环境写的，在其他环境需要修改软件的路径。

找到这两个软件对应的地址进行修改即可


### 8.3 单元测试用例导出
导出用例这部分，使用了下面这个工具

该工具内有使用说明，上文也有一些填写的注意事项。


## 9. 附录


---

## 🔗 相关链接

- [返回软件测试知识](./README.md)
- [返回知识库](../README.md)
- [Polyspace 使用指南](./Polyspace使用指南.md)

---

*原始文档：Tessy使用指南.pdf + Confluence 导出*
*转换日期：2026-05-06*
