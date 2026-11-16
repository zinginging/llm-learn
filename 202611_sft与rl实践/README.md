# SFT、偏好优化与在线RL：原理、选型和可运行demo

核验日期：2026-11-16。先解释SFT与在线RL的不同，再用同一算术任务实际训练两阶段，避免将“有奖励字段的数据”误当成已经运行RL。

- [场景选择、原理与两个demo](output/SFT与RL的场景选择和实操.md)
- [DPO、PPO、GRPO及其它优化方法：原理、选型与实操](output/DPO_PPO_GRPO与其它优化方法.md)
- [PO方法的论文与实验记录](docs/po论文与实验记录.md)
- [PO实验汇总](intermediate/po实验汇总.json)
- [DPO/PPO/GRPO等11种优化方法：原理、场景与实操](output/DPO_PPO_GRPO与其它优化方法.md)
- [PO论文与实现证据](docs/po论文与实验记录.md)、[PO实际训练汇总](intermediate/po实验汇总.json)
- [SFT/RL训练框架与批量推理选型](output/训练与批量推理框架选型.md)
- [安装及运行指南](docs/运行指南.md)
- [论文、版本与验证范围](docs/来源与验证.md)
- [实际微型训练结果](intermediate/微型训练结果.json)

在本主题目录安装依赖后运行：

```bash
python scripts/check_verifier.py
tmp/venv/bin/python scripts/sft_demo.py
tmp/venv/bin/python scripts/rl_demo.py
```

默认是CPU上26,976参数的真实自回归Transformer，随机初始化、不下载模型权重。两个训练阶段已运行，但6道留出题都没有改善，详细记录如实保留。它验证流程，不是大模型效果基准。

同一脚本支持从固定修订的`Qwen/Qwen2.5-0.5B`开始，见运行指南；这一路径本次只核验元数据，未下载/训练，资源要求需实测。

脚本：

- [SFT](scripts/sft_demo.py)：prompt-completion，teacher forcing，completion-only loss。
- [在线GRPO](scripts/rl_demo.py)：模型采样、程序奖励、组内优势及KL约束。
- [共享模型/数据/奖励](scripts/common.py)、[验证器边界检查](scripts/check_verifier.py)、[核心依赖](scripts/requirements.txt)。

checkpoint、tokenizer、缓存和运行日志位于忽略的`tmp/`；保留结果与依赖快照用于追溯。可联读[面试题SFT/偏好模块](../202611_大模型数据开发面试/output/06_SFT偏好与标注.md)。

新增偏好/在线优化实操：

- [DPO/IPO/SimPO/ORPO/KTO](scripts/offline_po_demo.py)。
- [PPO：实际训练policy和critic](scripts/ppo_demo.py)。
- [GRPO/RLOO/Dr.GRPO/GSPO及DAPO部分组件](scripts/online_po_demo.py)。
- [公式与边界演算](scripts/check_po_math.py)，仅标准库、无需安装训练依赖。

以上均从同一份`tmp/sft`分别起步，实际运行后参数有更新，留出题仍为0/6；不是算法效果排名，DAPO也未复现完整动态采样流程。
