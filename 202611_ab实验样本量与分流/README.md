# A/B 实验：需要多少样本，应该怎样分流

以转化率为例，解释如何从希望识别的业务变化计算样本量，再换算实验覆盖比例和天数。面向初次接触实验设计的读者。

本次参数为基准 10%、期望 lift 11%、每日可参与用户 2 万。按相对 lift 计算，目标为 11.1%，双侧 5% 显著性水平、80% 功效下每组约需 12,242 人；学习文档同时说明“目标为 11%”的另一种解释与观察窗口假设。

- [学习文档](output/AB实验的样本量与流量规划.md)：样本量、置信水平、检验功效、分流、周期与结果判断。
- [计算脚本](scripts/ab_sample_size.py)：Python 标准库实现两组独立转化率的正态近似规划，支持不等比例分流。
- [结果“置信度”怎么算](output/AB实验的样本量与流量规划.md#confidence)：用人数和转化数逐步计算差异、95% 区间与 p 值，解释为什么 `1−p` 不等于胜出概率。
- [置信区间的直觉解释](output/AB实验的样本量与流量规划.md#ci-intuition)：点估计与误差范围、95%的重复实验含义、区间宽度与业务门槛。
- [置信区间的定义与构造](docs/置信区间的定义与构造.md)：从抽样波动、正态分位数和不等式变形，推导上下界，并区分人为选定项与数据计算项。
- [标准误是什么意思](docs/置信区间的定义与构造.md#standard-error)：换一批样本后，估计结果会波动多大；与标准差、实际误差和区间半宽的区别。
- [结果计算脚本](scripts/ab_result_demo.py)、[合成结果算例](intermediate/结果置信区间算例.json)：与实验前样本量规划分开。
- [计算算例](intermediate/规划算例.json)、[来源与核验](docs/来源与核验.md)。
- [交付文件清单](input/交付文件清单.json)：用于检查远端保存是否包含全部成果。

在本目录运行，无需联网、密钥或安装依赖：

```bash
python scripts/ab_sample_size.py --self-check
python scripts/ab_result_demo.py --self-check
python scripts/ab_result_demo.py --examples
python scripts/ab_sample_size.py --examples
python scripts/ab_sample_size.py --baseline 0.10 --target 0.11 --daily-new-users 10000 --enrollment 0.20
```

脚本用于固定期限、独立用户、每个用户一个二元结果的规划。收入、请求级比率、用户重复观测、企业整组分流、序贯检验等，需要另外设计。计算量足够不保证实验一定得到显著结果。

关联：[评测、灰度与 A/B 面试问题](../202611_大模型数据开发面试/output/08_评测与数据闭环.md#q48)、[模型概率与校准](../202610_jev模型学习/docs/02_校准评估与实验设计.md)。
