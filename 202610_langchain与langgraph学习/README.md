# LangChain 与 LangGraph 学习

理解 Agent 应用框架与状态编排运行时的分工，围绕取数任务学习工具调用、上下文、权限、检查点、恢复和选型。

- [深度学习指南](output/langchain与langgraph深度学习指南.md)：概念、架构、能力对比、业务设计、学习路径和自测。
- [来源与版本核验](docs/来源与版本核验.md)：官方文档、固定源码、许可、版本与证据边界。
- [实验说明与验收](docs/实验说明与验收.md)：安装、命令、断言、预期结果和生产化验收。
- [LangChain 工具循环实验](scripts/langchain_tool_loop.py)：脚本模型、工具结果、隐藏运行参数与身份注入。
- [LangGraph 恢复实验](scripts/langgraph_checkpoint_flow.py)：SQLite 检查点、跨进程恢复、审批分支、并行汇总与重试。
- [依赖基线](scripts/requirements.in)、[完整依赖锁定](scripts/requirements.lock)、[实测记录](intermediate/验证记录.json)。

核验日期：2026-10-26。Python 基线为 LangChain 1.4.7、LangGraph 1.2.17。示例安装需要网络；安装后运行不调用外部模型、无需密钥或付费，使用虚构业务数据。模型选择工具的准确率、真实数据库权限和生产性能不在离线实验结论范围内。

## 快速运行

在本主题目录执行，Python 3.12 与 uv：

```bash
export UV_CACHE_DIR="$PWD/tmp/uv-cache"
uv venv tmp/venv --python 3.12
uv pip sync --python tmp/venv/bin/python scripts/requirements.lock
LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false \
  tmp/venv/bin/python scripts/langchain_tool_loop.py
LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false \
  tmp/venv/bin/python scripts/langgraph_checkpoint_flow.py
```

虚拟环境与缓存位于被 Git 忽略的 tmp/；脚本创建的 SQLite 实验库在系统临时目录，结束后清理。不要将真实凭据或数据放进实验。

关联学习：[Agent 上下文建设](../202610_agent上下文建设/README.md)、[AI-Ready 数据](../202610_ai-ready数据建设/README.md)、[统一语义层](../202610_agent统一语义层/README.md)。
