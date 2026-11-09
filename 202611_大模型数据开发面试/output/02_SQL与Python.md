# 02 SQL与Python

题源与原始定位见[问题清单](../docs/问题采集与分类.md)。以下用SQLite可执行实验和官方机制说明，方言差异另标；不是Spark或生产集群实测。

<a id="q07"></a>
## Q07 SQL如何求第N高的值，并处理并列？

**先答结论：**先问“第N行还是第N个不同值”“并列返回几人”“NULL怎么处理”。这些契约决定使用ROW_NUMBER、RANK还是DENSE_RANK。

ROW_NUMBER逐行编号，同分仍编号不同；RANK同分并列并留下跳号；DENSE_RANK同分并列但不同值连续编号。比如分数100、100、90，三者分别得到1/2/3、1/1/3、1/1/2。“第二高的不同分数”应使用DENSE_RANK=2；“严格取前2个人”需要ROW_NUMBER并定义稳定的次序。

```sql
WITH ranked AS (
  SELECT person_id, score,
         DENSE_RANK() OVER (ORDER BY score DESC) AS r
  FROM scores
  WHERE score IS NOT NULL
)
SELECT person_id, score FROM ranked WHERE r = 2;
```

如果改成按部门求前N，增加PARTITION BY department_id。不要为DENSE_RANK的排序加唯一person_id来“稳定”：这样会破坏分数并列；应在最终输出ORDER BY时稳定展示。ROW_NUMBER用于确定性选行时，才在窗口排序中加时间、版本和唯一序号。

**追问：**N超过不同值数量时返回空集还是NULL行，由接口约定；不是数据库自动替你决定。`LIMIT 1 OFFSET N-1`只是在特定排序下取第N行，通常不等于第N个不同值。示例在[离线实验](../scripts/interview_exercises.py)验证。

题源：DE-sql。依据：[T01](../docs/答案依据与研究笔记.md)。

<a id="q08"></a>
## Q08 INNER/LEFT JOIN有什么区别？为什么关联后行数和指标会膨胀？

**先答结论：**INNER保留满足关联条件的匹配组合，LEFT还保留左侧未匹配行并补右侧NULL。关联的结果是匹配行的组合，不是集合交并的简单图解。

若某键左表有m行、右表有n行，该键的等值连接最多产生m×n行。订单头连多条明细后再SUM订单金额，会重复累加头表指标。先确定每张表的粒度和关联键唯一性，再选择明细预聚合、维表去重或使用EXISTS做存在性判断，而不是事后随便DISTINCT。

LEFT JOIN的右表条件放WHERE可能排除补NULL行，使结果行为接近INNER；若要保留左表所有记录，通常将限定右表匹配的条件写在ON中。NULL通常不与NULL等值匹配，是否需要null-safe equality要依业务及SQL方言明确。

**例子：**一笔订单金额100，命中两条重复客户维度后金额变200；行数对账和金额对账会同时发现问题。但若另有漏单恰好抵消，总金额正常也不能证明正确，需要主键级比对。

**追问与误区：**维表SCD2要按业务键与有效期连接，不能任意取当前最新值解释历史事实。去重时必须知道应保留哪一条；没有业务规则的DISTINCT只会隐藏缺陷。脚本验证fan-out反例。

题源：DE-sql的JOIN题，行数膨胀为研究追问。依据：[T01、T08](../docs/答案依据与研究笔记.md)。

<a id="q09"></a>
## Q09 窗口函数ROWS和RANGE有什么区别？

**先答结论：**ROWS按排序后的行位置定义窗口；RANGE按排序值及同值peer group定义范围。对于相同排序值，累计结果可能不同。

例如按day排序，某天有两行金额10、20。`ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`可能在两行分别累计10和30；对应RANGE通常让这两条同值行共享包含全部该日peer的累计结果30。没有额外稳定排序时，ROWS内同值行的先后本身也不能保证。

```sql
SELECT day, amount,
  SUM(amount) OVER (
    ORDER BY day RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS cumulative_amount
FROM payments;
```

滚动7日不是“最近7行”。缺日时先用日期骨架补齐可加指标，或用方言支持的日期值区间；若一天多行，先聚到正确粒度。滚动UV不能将每日UV相加，必须在整个窗口对用户去重，或使用经过误差评估的可合并集合摘要。

**追问与误区：**某些方言对RANGE偏移、排序列数量、日期INTERVAL有限制；回答时说明目标引擎。窗口默认frame还可能让LAST_VALUE返回当前frame尾部而非分区最后一行，必要时显式写UNBOUNDED FOLLOWING。实验覆盖同值peer的行为，不冒充所有SQL方言都相同。

题源：W624。依据：[T01](../docs/答案依据与研究笔记.md)。

<a id="q10"></a>
## Q10 Python如何处理超过内存的大文件？生成器解决了什么？

**先答结论：**用流式迭代和有界批次降低峰值内存；生成器只避免一次性物化结果，不会自动解决全局排序、全局去重或无限缓存。

JSONL可以逐行解析，CSV应使用真正的CSV解析器而非简单split逗号；Parquet按row group/批次读取并做列裁剪。处理时保留文件、行号、对象版本和失败原因，把坏行写入隔离队列。写出采用分片与临时位置，完成校验后再发布，不能每处理一行就提交一个超小文件。

若平均一条解析后占s字节，批次B、并发C、预取P，粗估缓冲占用与s×B×C×P相关，还要加解压、对象与模型开销。这个估计只用于定位，必须实际测峰值RSS。读取500MB压缩文件可能膨胀为数GB的Python对象。

**追问：**精确全局去重若把所有hash放set仍可能OOM，应使用外部分桶、排序、磁盘KV或分布式任务；Bloom filter有假阳性，不能未经确认就删除训练样本。大JSON数组不天然支持逐行读取，需流式解析器或源端改为JSONL。

**误区：**不要把生成器马上包成list，也不要把所有Future及其结果都存在列表。限制在途任务数、设置背压、区分可重试读取错误与永久坏数据。

题源：DE-python。依据：[T15、T30](../docs/答案依据与研究笔记.md)。

<a id="q11"></a>
## Q11 Python多线程、多进程与GIL如何理解和选用？

**先答结论：**默认启用GIL的CPython中，同一进程通常不能让多个线程同时执行Python字节码；I/O等待和释放GIL的原生计算仍可并发。不能把这一结论推广成“Python线程完全没用”。

网络采集、对象存储读写常用线程或asyncio配合限流；Python密集的解析与规则计算可评估多进程；NumPy、tokenizer或模型库可能在原生层并行，应先profile。多进程需要付出启动、对象序列化、复制和进程间通信代价，任务过小可能更慢。

CPython从3.13开始提供可选free-threaded构建，因此面试要说明解释器版本与构建，不能再把GIL描述为所有Python运行环境永恒不变的限制。关闭GIL也不意味着共享状态无需同步，第三方扩展兼容性仍要确认。

**例子：**对100万篇文档调用远程质量API，瓶颈可能是服务token配额，应使用有界并发、指数退避和按文档ID恢复；开更多进程不增加服务端额度。对本地tokenization，先看库是否已有线程池，避免进程×线程过度订阅CPU。

**追问与误区：**并行处理必须固定随机种子与分片方式，避免重跑改变采样。工作进程不要重复加载十份大模型，也不要在不支持的进程启动模式下复用已初始化的CUDA上下文。

题源：I01。依据：[T02、T30](../docs/答案依据与研究笔记.md)。

<a id="q12"></a>
## Q12 Pandas和Spark DataFrame有什么区别，何时选择？

**先答结论：**Pandas主要在单机进程里处理表格；Spark DataFrame通过查询计划在分布式执行引擎上处理数据。API名字相似，不代表执行、排序、类型、NULL和内存语义相同。

小数据探索、抽检和复杂本地分析可用Pandas；大规模join、聚合、分区读写和可恢复作业常考虑Spark。选择还看数据分布、团队基础设施、启动开销和数据搬运成本，不能只给一个“超过1GB必须Spark”的统一阈值。

Spark通常惰性构造逻辑计划，action触发执行；`collect()`/`toPandas()`把结果集中到driver，容易破坏分布式内存边界。Pandas向量化在单机上可能非常快；大量小任务在Spark中会受调度、序列化和shuffle影响。Spark中的行顺序未经ORDER BY不应视为稳定。

**例子：**先用Spark按领域抽取少量样本，再用Pandas人工分析质量分布；不要把整套亿级语料toPandas。跨引擎核验时比较时区、decimal精度、空值、重复键和排序契约，而不只检查两边行数。

**追问与误区：**Pandas API on Spark与原生Pandas也不是同一执行引擎；pandas UDF不意味着把整个数据集搬到driver，但分组批次和Arrow内存仍可能失控。重点是知道计算和数据分别在哪里。

题源：I01。依据：[T03–T05](../docs/答案依据与研究笔记.md)。
