# RSI 递归自我改进学习

本主题按人工智能中的 Recursive Self-Improvement 整理，研究系统如何利用反馈修改自身，以及怎样区分回答修正、Agent 代码演化、权重适应和改进能力的递归提升。

- [深度调研与学习报告](output/rsi递归自我改进深度调研报告.md)：概念、机制、代表路线、2026 年新证据、横向比较与工程选型。
- [论文阅读笔记](docs/论文阅读笔记.md)：STOP、SICA、DGM、SEAL、AIDE²、RRSI、PAST-Bench、AI4AI-Bench 等的方法、实验与边界。
- [来源与版本核验](docs/来源与版本核验.md)：原始论文、会议、作者仓库、许可与数字核对。
- [离线评估实验](scripts/evaluation_gate_demo.py)：演示开发集过拟合、晋级门禁和最终审计，不复现自主 RSI。
- [论文快照](intermediate/论文快照.json)、[仓库快照](intermediate/仓库快照.json)、[验证记录](intermediate/验证记录.json)。

核验日期：2026-10-26。优先使用论文 PDF、会议和官方代码；9 篇 arXiv PDF 的版本及哈希留有记录，另查阅 ACL Gödel Agent 论文与相关原始资料。全文下载与提取文本保存在被忽略的 tmp/，不随仓库提交。

## 运行教学实验

在仓库根目录执行，Python 3.10+ 标准库，无需网络、密钥、GPU 或付费模型：

```bash
python 202610_rsi递归自我改进/scripts/evaluation_gate_demo.py
```

脚本使用手工候选与虚构收入数据，不生成或执行外部代码。它验证评估分离的教学反例，不证明模型学会了改进自身；真实模型、训练和上游 Agent 未运行。

建议先读报告第 1—4 节理解概念，再读第 5—8 节与论文笔记，最后运行实验并按评估方案设计自己的小型验证。

关联学习：[LangChain/LangGraph](../202610_langchain与langgraph学习/README.md)、[Tool/MCP/Skill](../202610_tool与mcp及skill学习/README.md)、[上下文建设](../202610_agent上下文建设/README.md)、[统一语义层](../202610_agent统一语义层/README.md)。
