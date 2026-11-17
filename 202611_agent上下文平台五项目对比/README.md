# Agent上下文平台五项目调研

原研究2026-11-16；2026-11-17依据本会话重建。目录曾作为未提交文件留在旧云端工作区，重建前检出的bbcb32b不含它；[原因与重建范围](docs/20261117_目录重建记录.md)。

| 独立报告 | 核心内容 |
| --- | --- |
| [Semantica](output/01_Semantica深度调研.md) | 图语义、来源、上下文组装、依赖失效 |
| [DataHub](output/02_DataHub深度调研.md) | Entity/Aspect、来源管理、事件与Agent工具 |
| [OpenMetadata](output/03_OpenMetadata深度调研.md) | 资产/质量、本体/RDF、MCP与分组件许可 |
| [Ontop](output/04_Ontop深度调研.md) | 本体映射、虚拟图、SPARQL→SQL |
| [Microsoft GraphRAG](output/05_GraphRAG深度调研.md) | 文档索引、Local/Global/DRIFT、权限与更新 |

- [五项目横向对比](output/06_五项目横向对比.md)
- [业务接入建议与验收计划](output/07_业务接入建议与验收计划.md)
- [多源接入、元数据与场景上下文组装](output/08_多源接入管理与元数据及上下文组装设计.md)
- [来源与固定源码证据](docs/来源与源码证据.md)
- [接入与元数据补充核验](docs/接入与元数据补充核验.md)
- [GraphRAG 产物接入 Semantica / OpenMetadata](docs/GraphRAG产物接入说明.md)：内容复用、元数据治理、字段适配与检索服务组合。
- [研究范围与业务假设](docs/研究范围与业务假设.md)、[运行与复核](docs/运行与复核.md)
- [本次验证记录](intermediate/验证记录.md)
- [成果持久化与防丢失](docs/成果持久化与防丢失.md)：交付清单、未跟踪检查、在线远端核验与恢复边界。

建议先明确业务口径、权限和来源管理，再在DataHub/OpenMetadata中选择主目录；访问适配层统一实际响应；Ontop、GraphRAG、Semantica按本体查询、文档检索和上下文失效的具体缺口加入。

在本主题目录执行：

```bash
python scripts/contract_demo.py
python scripts/source_management_demo.py
python scripts/source_audit.py
```

已重新取得74份固定版本文件；源码保存在忽略的tmp，不提交上游全文。离线例子是自建契约，不是五框架服务测试。未运行真实业务连接、模型调用或性能基准。

关联：[统一语义层](../202610_agent统一语义层/README.md)、[GraphRAG三项目](../202611_图增强rag三项目学习/README.md)、[AI-Ready数据](../202610_ai-ready数据建设/README.md)、[Tool/MCP/Skill](../202610_tool与mcp及skill学习/README.md)。
