# TextInsightBench — 测评资源

[English](README.md) | **简体中文**

对应 **{{TASKS}} 道开放发现任务**的公开评分说明，与[参与者语料](https://huggingface.co/datasets/CodeSoulco/TextInsightBench)及[代码仓库](https://github.com/erwinmsmith/TextInsightBench)配合使用。

## 内容

- `docs/SCORING.md`：公式、证据约束与汇总规则。
- `docs/USAGE.zh-CN.md`：下载、运行、评审及报告。
- `references.json`：绑定任务哈希的 {{TASKS}} 条参考可用性记录。
- `protocol.json`、`release.json`、`manifest.json`：协议、数量及校验。
- `docs/RESULTS.zh-CN.md`、`results/agent-runs.json`：开发实验结果。

**没有固定参考结论**。所有 `reference_id` 均为空，这些记录不是标注答案。发现按原文证据和公开评分规范评价，不要求匹配固定答案；参考覆盖率不可用。

## 使用

安装代码仓库后执行 `tib download --organizer --output data/evaluation`。当前评分可不加载参考文件，标准流程是：在参与者语料运行 Agent → `tib judge` 抽样语义评审 → `tib evaluate` 输出 JSON 与 Markdown。[完整使用指南](docs/USAGE.zh-CN.md)。

本地全量校验分类、精确引用及算术；模型盲检抽样原文，限制后续结论评分。模型评审收费且可能出错，不代表全部标签得到认证。报告分数时一并提供评分覆盖、未决、无效、缺失及弃答情况。

三个开源 Agent 共完成 150 次开发运行，其中 70 次有数值评分。不同批次配置有调整，不是严格控制条件的排行榜。[实验详情](docs/RESULTS.zh-CN.md)。

所有仓库公开，通过提交哈希固定快照。严格评测应阻止求解器访问评审反馈。[来源条款](SOURCES.md)。
