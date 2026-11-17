# Ontop：本体驱动的虚拟知识图谱与取数

研究基线2026-11-16；2026-11-17依据会话重建。对象`ontop/ontop`，固定SHA `efeac43a26e834727a23d771a77f304c5a8d08db`；源码5.6.0-SNAPSHOT，原研究时latest release为ontop-5.5.0。代码Apache-2.0，文档与驱动另查许可。[来源](../docs/来源与源码证据.md)

## 1. 定位：业务图视图之下仍然是数据库

Ontop通过本体和映射，把关系数据库中的内容暴露为虚拟RDF知识图谱。应用用SPARQL查询业务概念，系统改写为SQL交给数据库执行，不要求先复制全部数据为三元组。

这属于Ontology-Based Data Access。它适合统一业务实体和关系访问，不自动提供自然语言理解、通用指标口径、企业目录、接入后台或Agent对话管理。

## 2. 原理与论文

```text
SPARQL问题
 → 根据本体理解概念及关系
 → 按映射展开为数据库访问
 → SQL优化和执行
 → 返回类型化查询结果
```

本体说明概念关系，映射说明实例从哪些表/视图和字段来，数据库执行过滤、连接和聚合。正式支持范围应按版本核验，不能把“支持OWL”解释为任意OWL Full推理。

原研究采用《Ontop: Answering SPARQL queries over relational databases》（Semantic Web，2017卷期；DOI 10.3233/SW-160217）和《The Virtual Knowledge Graph System Ontop》（ISWC 2020；DOI 10.1007/978-3-030-62466-8_17）。论文提供查询改写基础，不能直接证明当前源库方言、跨源关联和业务口径已正确。

## 3. 源码阅读路径

| 文件/模块 | 职责 |
| --- | --- |
| QueryReformulator.java | 业务图查询到执行查询的改写接口 |
| SparqlQueryController.java | SPARQL HTTP入口 |
| OntopQuery.java | CLI查询参数、加载与执行 |
| mapping/sql/native、mapping/sql/r2rml | 原生OBDA与标准R2RML映射 |
| exampleBooks.obda及ttl | 官方实体、属性、IRI模板和SQL列绑定示例 |

主键、实体IRI、数据库约束和方言影响正确性及优化。生成稳定IRI不能只依赖可能重复的显示名称。

## 4. 教学映射与上手

本主题附[本体](../input/业务本体.ttl)、[OBDA](../input/净回款.obda)、[SPARQL](../input/净回款.sparql)。样例将paid订单映射为业务实例，净额按整数分计算；只是虚构教学输入，未通过真实Ontop执行验收。

```bash
# 先准备匹配发行版、支持的JDBC驱动、测试库与连接属性
# 这是运行指引，本次未执行Ontop
ontop query -m input/净回款.obda -t input/业务本体.ttl \
  -p tmp/ontop.properties -q input/净回款.sparql
```

生产可将复杂口径先封装为批准视图，再映射。具体CLI参数与驱动见[官方指南](https://ontop-vkg.org/guide/cli)。源密码不提交，连接文件放tmp。

## 5. 正确性难点

**粒度与重复：**订单连接明细后直接SUM可能重复金额。数据库行、RDF三元组和SPARQL解序列的重复语义不同；DISTINCT不是通用修补。必须定义主键、粒度、基数及多事实关联规则。

**时间与金额：**支付、下单、到账时间不同。北京时间十月的UTC范围是9月30日16:00到10月31日16:00，左闭右开。退款归期、时区、DECIMAL/整数分和币种均由业务口径决定。

**NULL与开放世界：**缺少三元组并不总意味着事实为假，未知与零不能混淆；源NULL、未映射与无结果也要区分。

**多源与性能：**虚拟统一视图不等于任意数据库联邦JOIN零配置成立。核对连接、方言、下推和必要的访问层。成本包括改写、源库扫描/JOIN、网络与序列化，昂贵SQL仍可能昂贵。

## 6. 统一接入与权限边界

Ontop是访问适配层中的一个查询分支，不是所有API、HBase、文件和消息来源的管理门户。登记Source、Connection、Mapping、Schema版本，完成样例等价性验证后再发布Binding供场景使用。

权限不能只依赖Agent prompt。使用可信身份、数据库RLS、限定视图/账号或服务端模板，并测试连接池的身份隔离。SPARQL里写tenant=A只是查询条件，允许任意改写时不构成安全边界。

建议外部接口形状：

```text
query_metric(metric_id, dimensions, filters, time_range)
 → 身份/允许参数检查 → 批准SPARQL模板 → Ontop → 数据库
 → 结果 + 映射/本体版本 + 数据时点 + 查询证据
```

这是建议适配契约，不声称上游已经提供同名完整MCP工具。

## 7. 适配当前业务

| 需求 | 优先起点 |
| --- | --- |
| 用统一实体/关系查询已有关系数据 | Ontop |
| dbt指标编译与分析口径 | MetricFlow等现有指标层 |
| 共享服务、预聚合与查询API | Cube等服务型语义层 |
| 文档主题与解释 | GraphRAG或普通RAG |

先用批准SQL/API得到黄金值；明确需要本体访问再加入Ontop。对同样问题比较SPARQL与黄金SQL，覆盖fan-out、时区、NULL、改名、版本、源权限和性能。本次没有Ontop引擎运行结果，不能宣称已完成这些验收。
