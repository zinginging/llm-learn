# GraphRAG、LightRAG、HippoRAG 2 学习与调研

核验日期：2026-11-09。研究对象为 Microsoft GraphRAG、HKUDS LightRAG、OSU HippoRAG 2；不是所有使用图的 RAG 的统称。

建议按以下顺序学习：

1. [深度对比与学习指南](output/三项目深度对比与学习指南.md)：从普通 RAG 入门，理解三种建库和查询流程、能力与局限。
2. [论文与源码证据](docs/论文与源码证据.md)：论文实验怎么读，源码入口在哪，版本有哪些陷阱。
3. [上手实操](docs/上手实操.md)：隔离环境、安装、共享语料、首次建库、检索与问答、排错。
4. [选型与评估方案](docs/选型与评估方案.md)：业务适配、成本、基线、更新删除和上线验收。

## 先运行无密钥示例

在本主题目录执行，Python 3.10+，仅需标准库：

```bash
python scripts/ppr_learning.py
python scripts/export_graphrag_input.py
```

前者验证一个**人工构造图上的 PPR 教学例子**，后者把共享语料导出为 GraphRAG 的文本输入。它们不调用模型，也不复现任何项目的检索效果。

真实项目示例：

- [LightRAG 异步建库与检索](scripts/lightrag_demo.py)
- [HippoRAG 2 建库、检索与问答](scripts/hipporag_demo.py)
- GraphRAG 使用官方 CLI，见[实操](docs/上手实操.md)。

真实示例需要另外安装项目、设置密钥，可能产生 API 费用。本次没有执行真实 LLM/Embedding 调用，也没有进行三项目性能跑分。源码阅读、接口静态核对与离线演算的范围见[验证记录](intermediate/验证记录.md)。

## 可追溯材料

- [统一教学语料与问题](input/企业知识样例.json)：全部为虚构内容，含多跳、别名、时间变化及无答案问题。
- [仓库快照](intermediate/仓库快照.json)、[论文快照与 SHA-256](intermediate/论文快照.json)
- [源码核对脚本](scripts/source_audit.py)、[源码核对结果](intermediate/源码核对.json)
- [离线 PPR 结果](intermediate/ppr教学结果.json)

克隆源码和论文 PDF 位于被 Git 忽略的 `tmp/`；保留的文档为自写归纳和原始链接。可与仓库中的 [AI-Ready 数据](../202610_ai-ready数据建设/README.md)、[Agent 上下文建设](../202610_agent上下文建设/README.md) 及 [Tool/MCP/Skill](../202610_tool与mcp及skill学习/README.md) 联读。
