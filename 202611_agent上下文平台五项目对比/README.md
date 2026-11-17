# Agent上下文平台五项目调研

本主题研究：怎样管理不同来源的数据、说明业务含义，并为 AI 的具体任务准备所需资料。

**建议先读 [五项目横向对比：从数据接入到给 AI 准备业务资料](output/06_五项目横向对比.md)。**文章用客户回款的完整例子解释五个项目的分工，再按数据接入、业务定义、场景组装和下游交付逐项比较。实现细节可随后查阅独立报告。

原研究2026-11-16；2026-11-17依据本会话重建。目录曾作为未提交文件留在旧云端工作区，重建前检出的bbcb32b不含它；[原因与重建范围](docs/20261117_目录重建记录.md)。

| 独立报告 | 核心内容 |
| --- | --- |
| [Semantica](output/01_Semantica深度调研.md) | 关联知识、保留出处、检查过期资料、准备 AI 所需内容 |
| [DataHub](output/02_DataHub深度调研.md) | 管理有哪些数据、字段含义、负责人和数据来源 |
| [OpenMetadata](output/03_OpenMetadata深度调研.md) | 数据资料、业务术语、质量检查；开源与商业功能边界 |
| [Ontop](output/04_Ontop深度调研.md) | 将业务概念对应到数据库，按这些概念查询数据 |
| [Microsoft GraphRAG](output/05_GraphRAG深度调研.md) | 从文档提取关系、查找依据、综合回答跨文档问题 |

- [五项目横向对比](output/06_五项目横向对比.md)
- [业务接入建议与验收计划](output/07_业务接入建议与验收计划.md)
- [多源接入、元数据与场景上下文组装](output/08_多源接入管理与元数据及上下文组装设计.md)
- [来源与固定源码证据](docs/来源与源码证据.md)
- [接入与元数据补充核验](docs/接入与元数据补充核验.md)
- [GraphRAG 产物接入 Semantica / OpenMetadata](docs/GraphRAG产物接入说明.md)：内容复用、元数据治理、字段适配与检索服务组合。
- [研究范围与业务假设](docs/研究范围与业务假设.md)、[运行与复核](docs/运行与复核.md)
- [本次验证记录](intermediate/验证记录.md)
- [成果持久化与防丢失](docs/成果持久化与防丢失.md)：交付清单、未跟踪检查、在线远端核验与恢复边界。

建议先确定业务规则和访问权限，用 DataHub 或 OpenMetadata 管理数据说明；通过统一取数服务处理不同来源的真实数据；再根据查询、文档检索和资料组装的具体需要，选择 Ontop、GraphRAG 或 Semantica。

在本主题目录执行：

```bash
python scripts/contract_demo.py
python scripts/source_management_demo.py
python scripts/source_audit.py
```

已重新取得74份固定版本文件；源码保存在忽略的tmp，不提交上游全文。离线例子是自建契约，不是五框架服务测试。未运行真实业务连接、模型调用或性能基准。

关联：[统一语义层](../202610_agent统一语义层/README.md)、[GraphRAG三项目](../202611_图增强rag三项目学习/README.md)、[AI-Ready数据](../202610_ai-ready数据建设/README.md)、[Tool/MCP/Skill](../202610_tool与mcp及skill学习/README.md)。
