# Tool、Function Calling、MCP 与 Skill 学习

理解四者的层次、能力和组合方式，围绕取数 Agent 学习上下文加载、执行位置、选型与验收。

- [原理与选型指南](output/tool_function-calling_mcp_skill原理与选型.md)：定义、对比矩阵、调用链路、适配场景、性能与设计方法。
- [来源与版本核验](docs/来源与版本核验.md)：官方 Function Calling 文档、MCP 版本与 Agent Skills 规范。
- [离线调用示例](scripts/call_boundary_demo.py)：内部调用归一化、工具目录适配、可信身份与错误参数检查。
- [实验记录](intermediate/验证记录.json)：实际命令、输出、Python 版本与脚本哈希。

核验日期：2026-10-26。Python 标准库示例无需安装依赖、网络、密钥、付费 API 或业务数据。在仓库根目录执行：

```bash
python 202610_tool与mcp及skill学习/scripts/call_boundary_demo.py
```

示例模拟应用内部的调用与适配，不运行真实模型、MCP SDK/传输或 Skill 加载器，不能作为协议兼容性、模型准确率或性能测试。

关联学习：[LangChain 与 LangGraph](../202610_langchain与langgraph学习/README.md)、[Agent 上下文建设](../202610_agent上下文建设/README.md)、[统一语义层](../202610_agent统一语义层/README.md)。
