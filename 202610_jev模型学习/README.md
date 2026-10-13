# Jev 模型学习

研究对象为 TypeSafe AI 的 Jev System One 决策模型。资料核验日期：2026-10-13。

- [原理与实践学习指南](output/jev模型原理与实践学习指南.md)：模型定位、三种原语、概率与 confidence、独立评估、API 示例与学习路线。
- [离线公式演算](scripts/confidence_examples.py)：均值、尾部概率与并列最可能等级；不调用付费 API。
- [来源与验证记录](docs/来源与验证记录.md)：官方链接、版本与实测范围。

运行离线示例：

```bash
python 202610_jev模型学习/scripts/confidence_examples.py
```

运行目录为仓库根目录，脚本只使用 Python 标准库，不产生输出文件。
