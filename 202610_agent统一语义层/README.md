# Agent 统一语义层

- [四项目对比调研](output/四项目语义层对比调研报告.md)：架构、表达能力、Agent 接入、治理、性能与场景选型。
- [来源与版本核验](docs/来源与版本核验.md)：固定仓库 commit、许可和官方证据。
- [PoC 验收方案](docs/poc验收方案.md)：统一契约、黄金值、执行与转换测试。
- [在线对比报告](https://chatgpt.com/space/page_3b749c0618fc819196e2423e62f493ad)：包含适配场景和原生、集成、外部职责能力矩阵。

核验日期：2026-10-14。比较包含四项目源码追踪、Wren/Ossie 针对性测试与 Wren DuckDB 小样本查询，不是四项目性能基准。

- [源码追踪与验证](docs/源码追踪与验证.md)：编译、关联粒度、权限、缓存、转换损失与实际测试结果。
- [固定源码克隆脚本](scripts/clone_sources.py)与[Wren 黄金案例](scripts/wren_golden_case.py)：复现源码版本和小样本执行。
