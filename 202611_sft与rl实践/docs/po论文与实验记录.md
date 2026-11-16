# PO方法：论文与实现证据

核验日期：2026-11-16。正文见[学习报告](../output/DPO_PPO_GRPO与其它优化方法.md)。资料以论文全文和固定版本实现为准，搜索结果只用于发现来源；不引用社区排行榜作为方法普遍优劣的证据。

## 1. 阅读的原始论文

下列版本为本次PDF快照，版本日期与初次发表日期不同。版本号链接固定原文；[下载清单](../intermediate/po论文快照.json)保留下载时的URL、大小、SHA-256与核验日。PDF、抽取文本保存在忽略的`tmp/po_papers`，不将全文提交仓库。清单中的不带版本URL可能漂移，重取应使用下表固定版本并核对散列。

| 方法 | 论文与固定版本 | 该版本日期 | 支持的机制与阅读重点 |
| --- | --- | --- | --- |
| PPO | Schulman等：[Proximal Policy Optimization Algorithms](https://arxiv.org/abs/1707.06347v2) | 2017-08-28 | §3裁剪目标、§5算法；裁剪并非硬信任域保证 |
| DPO | Rafailov等：[Direct Preference Optimization: Your Language Model is Secretly a Reward Model](https://arxiv.org/abs/2305.18290v3) | 2024-07-29 | §4奖励重参数化、偏好目标；固定偏好数据与参考策略 |
| GRPO | Shao等：[DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models](https://arxiv.org/abs/2402.03300v3) | 2024-04-27 | GRPO章节；组内相对优势、移除critic、KL项 |
| IPO | Azar等：[A General Theoretical Paradigm to Understand Learning from Human Preferences](https://arxiv.org/abs/2310.12036v2) | 2023-11-22 | Identity-PO的有限目标间隔与平方目标 |
| SimPO | Meng等：[SimPO: Simple Preference Optimization with a Reference-Free Reward](https://arxiv.org/abs/2405.14734v3) | 2024-11-01 | §3长度平均log概率、target reward margin |
| ORPO | Hong等：[ORPO: Monolithic Preference Optimization without Reference Model](https://arxiv.org/abs/2403.07691v2) | 2024-03-14 | NLL+odds ratio目标，不是简单删掉DPO参考模型 |
| KTO | Ethayarajh等：[Model Alignment as Prospect Theoretic Optimization](https://arxiv.org/abs/2402.01306v5) | 2026-09-08 | 好坏单标签、相对参考点的效用；本次读到v5，不当成2024首版原文 |
| RLOO | Ahmadian等：[Back to Basics: Revisiting REINFORCE Style Optimization for Learning from Human Feedback in LLMs](https://arxiv.org/abs/2402.14740v2) | 2024-02-26 | leave-one-out基线、REINFORCE与critic比较 |
| DAPO | Yu等：[DAPO: An Open-Source LLM Reinforcement Learning System at Scale](https://arxiv.org/abs/2503.14476v2) | 2025-05-20 | §3四项组件、Algorithm 1动态采样；本次仅部分组件训练 |
| Dr.GRPO | Liu等：[Understanding R1-Zero-Like Training: A Critical Perspective](https://arxiv.org/abs/2503.20783v2) | 2025-10-06 | §3.2与后续分析，长度/难度归一化偏置；COLM 2025版本 |
| GSPO | Zheng等：[Group Sequence Policy Optimization](https://arxiv.org/abs/2507.18071v2) | 2025-07-28 | §4.1序列级重要性比、裁剪；稳定性结论限于原文实验 |

这些论文跨不同模型、任务、数据和计算预算，正文不将各自最佳成绩拼成横向排名，也不把预印本发布等同于同行评审接受。

## 2. 固定实现版本

本次实际依赖：Python 3.12.14、PyTorch 2.5.1+cpu、Transformers 4.57.3、TRL **0.28.0**、Datasets 4.4.1、Accelerate 1.11.0。完整[依赖快照](../intermediate/环境依赖.txt)、[安装指南](运行指南.md)。

官方固定版本入口：[TRL v0.28.0文档](https://huggingface.co/docs/trl/v0.28.0/en/index)、[源码tag](https://github.com/huggingface/trl/tree/v0.28.0/trl)。本次核对安装wheel及其源码，临时解包位于`tmp/trl_source`。以下路径相对该版本的`trl/`：

| 方法 | 源码位置 | 本地实现选择 |
| --- | --- | --- |
| DPO / IPO | `trainer/dpo_trainer.py`, `trainer/dpo_config.py` | `loss_type=["sigmoid"]` / `["ipo"]`；IPO长度平均 |
| SimPO | `experimental/cpo/cpo_trainer.py` | `loss_type="simpo"`, **`cpo_alpha=0`**关闭额外NLL |
| ORPO | `experimental/orpo/orpo_trainer.py` | 归一化回答概率与odds，联合chosen NLL |
| KTO | `experimental/kto/kto_trainer.py` | 单条label，好坏效用、KL参考点 |
| PPO | `experimental/ppo/ppo_trainer.py` | 真正的actor–critic Trainer，程序奖励适配其接口 |
| RLOO | `trainer/rloo_trainer.py` | 现代Trainer含样本复用/裁剪细节，不能简化成仅原始梯度公式 |
| GRPO及变体 | `trainer/grpo_trainer.py`, `trainer/grpo_config.py` | 显式设置loss/scale/importance层级，避免默认项歧义 |

PPO/CPO/ORPO/KTO位于experimental命名空间，可能随版本移动。0.28.0的GRPO默认loss不是原始GRPO，示例必须显式传入；GSPO使用`importance_sampling_level="sequence"`；Dr.GRPO须同时配置loss与奖励缩放。CPO/ORPO/KTOConfig不接收旧教程的`max_prompt_length`，本例使用`max_length=32`，没有混用旧API。

实现与论文不保证每一项工程细节相同。本报告把“用固定版本Trainer执行相应目标”与“复现论文全套实验”分开，尤其DAPO明确缺少动态采样/超长奖励塑形。

## 3. 自己做了什么实验

- 共用本地随机微型GPT-2架构，26,976参数；先SFT，再从**同一份SFT**分别启动全部方法。
- 25训练/5验证/6测试；按操作数交换不变的分组切分，数据构造见`common.py`。DPO等用程序生成的好坏对；KTO拆成50条；在线方法在训练集prompt上真正生成后评分。
- DPO/IPO/SimPO/ORPO/KTO、GRPO/RLOO/Dr.GRPO/GSPO各40step；PPO256 episodes，每批8，每批4轮；DAPO组件40step。这些预算不同，不是公平效果比较。
- 每种训练检查权重变化；PPO额外检查critic变化，以及真实奖励适配接口的正反例。
- 结果与解释保存在[汇总](../intermediate/po实验汇总.json)及逐方法JSON；全部留出精确匹配0/6，未显示泛化改善。
- [数学演算脚本](../scripts/check_po_math.py)检查DPO/PPO手算、正负优势裁剪、同分组、非法组大小、GSPO几何平均、长度归一化与过滤。这是公式教学验证，不是模型效果测评。

## 4. 尚未验证的内容

真实预训练大模型效果、多GPU吞吐/显存、学习型RM训练、多步Agent轨迹、完整DAPO recipe、中文偏好质量与真实点赞偏差均未实测。原论文的收益属于各自实验设置，本地CPU demo不继承其结论。模型权重/日志在忽略的tmp中，重新clone后需按运行指南重新生成SFT起点。
