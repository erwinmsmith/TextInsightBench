# TextInsightBench

[English](README.md) | **简体中文**

TextInsightBench 面向自然语言数据挖掘 Agent，共 **50 道开放探索任务、435,000 篇任务文本、944,468 篇无标签学习文本**。每题 5,000 或 10,000 篇文本，最多提交 3 个不重复的发现。题目给出研究目标，不指定要发现的文本现象、比较组或时间切点；任何分析方法均可使用。

## 数据与仓库

代码与使用说明在 [GitHub](https://github.com/erwinmsmith/TextInsightBench)，语料与题目在 [参与者数据集](https://huggingface.co/datasets/CodeSoulco/TextInsightBench)，评分协议与参考可用性说明在 [测评资源](https://huggingface.co/datasets/CodeSoulco/TextInsightBench-Evaluation)。三个仓库均公开，名称始终为 TextInsightBench，使用提交哈希标识精确快照。

| 来源 | 任务数 | 任务文本 | 无标签学习文本 |
|---|---:|---:|---:|
| Amazon Beauty | 13 | 130,000 | 330,885 |
| App Reviews | 13 | 65,000 | 1,660 |
| CFPB | 12 | 120,000 | 483,788 |
| NHTSA | 12 | 120,000 | 128,135 |
| 合计 | 50 | 435,000 | 944,468 |

任务包括 20 道群体差异、15 道时间变化、15 道复合关联。Agent 必须探索语料、自选分析范围、定义可观察现象，并对选定范围内所有文本给出正例、负例或未知判断，不能只挑几段引文推断总体比例。还需要解释反例、元数据构成、未知判断和结论适用边界。

## 运行

```bash
git clone https://github.com/erwinmsmith/TextInsightBench.git
cd TextInsightBench
python -m venv .venv
source .venv/bin/activate
pip install -e '.[data]'
tib download --output data/participant
tib verify --data data/participant
tib run --data data/participant --command 'python my_agent.py' \
  --timeout 3600 --output runs/my-agent/submissions
```

默认即完整探索挑战，不需要 difficulty 参数。学习赛道下载时加 `--with-learning`，运行时加 `--track unlabeled_pool`。示例 `examples/abstain_agent.py` 仅用于接口测试，不代表挖掘效果。

Agent 从标准输入接收任务和本地压缩 JSONL 文件路径，自行读取、检索、索引和分析；向标准输出返回 JSON，日志输出到标准错误。详见英文 [接口](docs/AGENT_PROTOCOL.md) 与 [提交格式](docs/SUBMISSIONS.md)。

## 测评与分数

本地验证器全量重算选定范围内的分母、统计、缺失边界、分层对比及集中度，核对完整文档划分和原文引用。语义评分使用配置的模型服务，会产生 API 费用：

```bash
tib judge --data data/participant --submissions runs/my-agent/submissions \
  --base-url "$JUDGE_BASE_URL" --model "$JUDGE_MODEL" \
  --audit-documents 160 --output runs/my-agent/reviews
tib evaluate --data data/participant --submissions runs/my-agent/submissions \
  --reviews runs/my-agent/reviews --output runs/my-agent/report.json
```

密钥通过本地环境变量 `JUDGE_API_KEY` 提供。评审按提交状态分层抽样、补充全语料抽样，并检查引文。**算术检查是全量的，语义检查是抽样的**，不是全量语义确认，也不增加独立验证阶段。

发现得分为 `支持系数 × (15 + 25S + 20E + 30D + 10C)`，分别关注统计有效性、证据支持、实质分析深度、校准。未完成任务或重复发现记零；证据不足保留未决。必须同时报告有效率、已评分覆盖、弃答、缺失和无效数量，不能用少数已评分任务的均分代表全量成绩。

## 参考答案状态

本次改变了题目含义，**没有把旧 50 条参考结论冒充成新题的 ground truth**。旧结论保留在历史提交中，当前测评资源明确记载固定参考结论为 0。新题按语料证据与公开评分规范评价，参考覆盖率不可用，而不是 0 分。这不是已经完成了 50 条新标注答案的声明。

不增加独立验证集。新任务文本来自此前公开的学习池，不能声称未见；当前任务与剩余学习池文档不重叠，但来源和实体可共享，任务并非统计独立。尚未运行真实 Agent 对照实验，因此不宣称已实证证明某个难度水平。旧成绩不能与当前任务直接比较。

详见 [挑战设计](docs/DIFFICULTY.md)、[评分](docs/SCORING.md)、[数据](docs/DATA.md)、[来源与条款](docs/SOURCES.md)。正文英文为主，原始文本保持不变。
