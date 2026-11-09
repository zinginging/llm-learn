# 大模型批量推理与实时 API 推理

比较离线批量任务与在线服务的目标、接口、调度及优化手段，分清 Batch API、并发请求和引擎连续批处理。

- [对比调研与学习指南](output/批量推理与实时api推理对比调研.md)：原理、能力对比、加速矩阵、选型与实施路径。
- [压测与验收方案](docs/压测与验收方案.md)：公平比较、延迟/吞吐、缓存、质量、失败和成本统计。
- [来源与论文笔记](docs/来源与论文笔记.md)：官方产品文档、vLLM 固定源码文档与系统论文。
- [指标教学脚本](scripts/inference_metrics_demo.py)、[验证记录](intermediate/验证记录.json)、[来源快照](intermediate/来源快照.json)。

核验日期：2026-11-04。重点讨论自回归文本生成；多模态编码、Embedding 和扩散语言模型有不同执行特征，不能直接套用所有结论。未进行 GPU、供应商 API 或真实模型性能测试。

在仓库根目录运行标准库教学实验，无需网络、模型、密钥、GPU 或付费：

```bash
python 202611_批量与实时推理对比/scripts/inference_metrics_demo.py
```

脚本使用人工 token 时间戳展示吞吐与 goodput 的区别，并演算常规 GQA KV 内存；不能当作任何引擎或 API 的成绩。

关联学习：[MoE 与 Dense](../202610_moe与dense入门/README.md)、[LangChain 与 LangGraph](../202610_langchain与langgraph学习/README.md)、[Tool/MCP/Skill](../202610_tool与mcp及skill学习/README.md)。
