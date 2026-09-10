# TextInsightBench

[English](README.md) | **简体中文**

TextInsightBench 用于评估 Agent 从自然语言语料中挖掘具体、有证据支持的发现。任务涵盖群组差异、时间变化和复合关联，要求量化结论、检查反例并解释不确定性。

当前私密研究版为 **v5.1**：包含 **50 道任务、24,504 篇评测文本、1,379,468 篇可选无监督学习文本**。每题最多提交 5 个发现，也可说明理由后弃答。任务和主要文档以英文为主，原始语料保持原文。

## 资源组成

| 资源 | 地址 | 内容 |
|---|---|---|
| 代码与使用说明 | [erwinmsmith/TextInsightBench](https://github.com/erwinmsmith/TextInsightBench) | 批量运行、验证、测评、题目目录、评分规则 |
| 参与者数据 | [CodeSoulco/TextInsightBench](https://huggingface.co/datasets/CodeSoulco/TextInsightBench) | 无监督文本池、50 份任务语料、格式和校验清单 |
| 组织者参考集 | [CodeSoulco/TextInsightBench-Evaluation](https://huggingface.co/datasets/CodeSoulco/TextInsightBench-Evaluation) | 50 个参考结论、定义和原文背景，仅供组织者使用 |

三个仓库初始均为私密。参与者不应获得组织者参考集；组织账号凭证可能同时读取两份数据，实际测评应使用独立环境，只挂载参与者可见文件。运行器本身不提供安全沙箱。

## 快速开始

```bash
git clone https://github.com/erwinmsmith/TextInsightBench.git
cd TextInsightBench
python -m venv .venv
source .venv/bin/activate
pip install -e '.[data]'
hf auth login
tib download --output data/participant --with-learning
tib verify --data data/participant --with-learning
tib run --data data/participant --command 'python examples/abstain_agent.py' \
  --output runs/smoke/submissions
```

示例 Agent 会对 50 题全部弃答，用于检查接口，不调用模型，也不代表基线能力。去掉下载参数 `--with-learning` 可只下载题目语料。运行时添加 `--limit 1` 可先测试一道题。

## 接入自己的 Agent

Agent 进程从标准输入读取一个 JSON，包含 `task`、完整 `documents` 和可选 `learning_directory`，向标准输出写入一份提交 JSON，日志写入标准错误。

```bash
tib run --data data/participant --command 'python my_agent.py' \
  --track unlabeled_pool --timeout 1800 --output runs/my-agent/submissions
```

`task_only` 只使用当前任务语料；`unlabeled_pool` 允许提前利用无监督文本池学习。评测前冻结全局提示词、参数和阈值；评测中可分析当前任务语料，但不可将评测反馈或当前题拟合状态带入后续题目。相同配置重新运行时，会验证并复用已成功生成的提交。

提交包括结论、可观察条件定义、全部文档的 positive/negative/unknown 划分、统计值、精确原文引用以及局限。详见 [提交格式](docs/SUBMISSIONS.md) 和 [Agent 协议](docs/AGENT_PROTOCOL.md)。

## 测评流程

```bash
tib validate --data data/participant \
  --submission runs/my-agent/submissions/amazon_beauty_group_difference_hair_tools_midrating_v5.json

# 以下在组织者的独立环境中执行
tib download --organizer --output private/evaluation
tib evaluate --data data/participant --submissions runs/smoke/submissions \
  --references private/evaluation/references.json --output runs/smoke/report.json
```

上述示例生成 JSON 和 Markdown 报告，显示 50 题有效弃答、参考覆盖率为零、发现质量为 null。程序不会给未判定的答案生成虚构分数。

对于有实质发现的答案，在环境中设置 `JUDGE_API_KEY`、`JUDGE_BASE_URL` 和 `JUDGE_MODEL`，使用支持 JSON 输出的 chat-completions 服务：

```bash
tib judge --data data/participant --submissions runs/my-agent/submissions \
  --references private/evaluation/references.json --output runs/my-agent/reviews \
  --base-url "$JUDGE_BASE_URL" --model "$JUDGE_MODEL"
tib evaluate --data data/participant --submissions runs/my-agent/submissions \
  --references private/evaluation/references.json --reviews runs/my-agent/reviews \
  --output runs/my-agent/report.json
```

`judge` 会产生所选服务的 API 费用。每份非空答案先根据完整任务语料评分，有得到支持的发现时，再调用一次参考匹配。第一阶段不提供参考答案。模型需要足够长的上下文；超限会明确失败，不截断材料。已完成的有效评审可以复用。

## 如何理解分数

发现质量满分 100：任务满足 35 分、统计有效性 25 分、证据支持 20 分、分析深度 10 分、校准与局限 10 分，再乘以支持程度系数。每题按所提交发现的质量取平均。参考覆盖率单独报告，有充分证据的新发现即使未匹配参考，也可以得到完整质量分。

弃答、缺失、无效答案和未完成语义评审均会单独记录。只有 50 题都有可用质量分时，才给出完整宏平均；条件均分会明确标为诊断值。详见 [评分规则](docs/SCORING.md) 和 [组织者使用说明](docs/ORGANIZER.md)。

组织者参考集使用维护者冻结的 AI 参考结论，未经独立事实验证。当前版本不包含、不使用文档级确认标注。它提供非穷尽的参考发现，发现质量仍由原文证据决定。

## 数据与复现

无监督池有 278 个 Parquet 分片，字段为 `doc_id`、`source`、`text`、`title`。与评测文本及参考构建文本核对后，在文档 ID、归一化文本和保守模板规则下均未发现重叠。不同任务仍可能共享实体或来源，不构成统计独立样本。

`benchmark/data.lock.json` 固定 Hugging Face 的提交版本，下载后核对 SHA-256。任务 ID 中保留旧版本后缀以维持标识稳定；整体发行版为 v5.1。数据来源、规模与使用条件见 [数据说明](docs/DATA.md) 和 [来源说明](docs/SOURCES.md)。

```bash
python -m unittest discover -s tests -v
```
