# TextInsightBench

[English](README.md) | **简体中文**

自然语言数据挖掘 Agent benchmark：**{{TASKS}} 道任务、{{TASK_DOCUMENTS}} 篇任务文本、{{LEARNING_DOCUMENTS}} 篇无标签学习文本**。

每题 5,000 或 10,000 篇，Agent 自选分析条件、范围及比较对象，最多提交 3 个发现，附完整文档分类、精确引用、统计量、反例与局限。不限定分析方法。

## 包含什么

- `tasks.json`：题目与约束。
- `corpora/*.jsonl.gz`：每题完整原文。
- `learning/*/*.parquet`：可选无标签学习池。
- `output.schema.json`：输出格式。
- `protocol.json`、`release.json`、`manifest.json`：协议、数量与文件校验。
- `results/agent-runs.json`：开发实验统计，不是排行榜。

语料来自 Amazon Beauty、Android App Reviews、CFPB 和 NHTSA。任务包含 20 道群体差异、15 道时间变化、15 道复合关联。

## 使用

```bash
git clone https://github.com/erwinmsmith/TextInsightBench.git
cd TextInsightBench
python -m venv .venv
source .venv/bin/activate
pip install -e .
tib download --output data/participant
tib verify --data data/participant
```

下载使用代码仓库锁定的提交；需要学习池时加 `--with-learning`。

[接入、续跑及评分](docs/USAGE.zh-CN.md) · [数据字段](docs/DATA.md) · [代码仓库](https://github.com/erwinmsmith/TextInsightBench) · [测评资源](https://huggingface.co/datasets/CodeSoulco/TextInsightBench-Evaluation)

## 评估与结果

本地全量检查分类、引用与算术；模型先盲检抽样原文，再评审发现质量。语义评审收费、不是全量确认，也不等于独立 ground truth。任务没有固定参考结论，按原文证据及公开规则评分。

已有三个开源 Agent 的 150 次运行全部结束：86 份有效提交、70 份数值评分、16 份证据未决、64 次未产生有效提交。配置在开发中调整过，不是控制条件一致的排行榜。[完整实验结果](docs/RESULTS.zh-CN.md)。

任务与学习池 ID 不重叠，但数据此前公开，实体和来源可共享，任务并非统计独立。原文是未经核实的作者叙述，可能含个人信息。[来源与使用条款](SOURCES.md)。
