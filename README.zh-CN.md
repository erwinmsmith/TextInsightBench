# TextInsightBench

[English](README.md) | **简体中文**

面向 Agent 的自然语言数据挖掘 benchmark：探索语料、发现有价值的现象、量化差异，并检验原文是否支持结论。不限定分析方法。

**50 道任务 · 435,000 篇任务文本 · 944,468 篇无标签学习文本**

每题提供 5,000 或 10,000 篇文本及研究目标，不预先指定要发现的现象。Agent 自行选择分析条件、人群与比较对象，最多提交 3 个不重复的发现，并提供文档分类、原文引用、统计量、反例及局限。

## 入口

| 资源 | 内容 |
|---|---|
| [参与者数据](https://huggingface.co/datasets/CodeSoulco/TextInsightBench) | 题目、任务语料、可选无标签学习池及输出结构 |
| [测评资源](https://huggingface.co/datasets/CodeSoulco/TextInsightBench-Evaluation) | 公开评分说明与参考可用性记录 |
| [使用指南](docs/USAGE.zh-CN.md) | 下载、接入 Agent、续跑及生成报告 |
| [实验结果](docs/RESULTS.zh-CN.md) | 三个开源 Agent 的全量测试、覆盖情况及局限 |

三个仓库均公开。名称统一为 TextInsightBench；用代码提交及 [data.lock.json](benchmark/data.lock.json) 中的数据提交固定实验快照。

## 快速开始

需要 Python 3.10 或更新版本：

```bash
git clone https://github.com/erwinmsmith/TextInsightBench.git
cd TextInsightBench
python -m venv .venv
source .venv/bin/activate
pip install -e .

# 下载全部任务语料；无需账号和模型密钥。
tib download --output data/participant
tib verify --data data/participant

# 仅测试接口：对全部 50 题弃答，不调用模型。
tib run --data data/participant --command 'python examples/abstain_agent.py' \
  --output runs/smoke/submissions
tib evaluate --data data/participant --submissions runs/smoke/submissions \
  --output runs/smoke/report.json
```

示例会得到 50 次弃答、质量分为空。这表示接口可用，不代表挖掘效果。

## 接入与评分

每题启动一个独立进程，通过 stdin 接收 JSON：完整题目、本地压缩语料的绝对路径、可选学习目录。stdout 只返回一个符合规范的提交 JSON，日志写 stderr。语料如何探索与建模由 Agent 决定。

```bash
tib run --data data/participant --command 'python my_agent.py' \
  --timeout 3600 --output runs/my-agent/submissions

# 在本地导出 JUDGE_API_KEY、JUDGE_BASE_URL、JUDGE_MODEL，勿提交密钥。
tib judge --data data/participant --submissions runs/my-agent/submissions \
  --base-url "$JUDGE_BASE_URL" --model "$JUDGE_MODEL" \
  --audit-documents 160 --output runs/my-agent/reviews
tib evaluate --data data/participant --submissions runs/my-agent/submissions \
  --reviews runs/my-agent/reviews --output runs/my-agent/report.json
```

默认 `task_only` 只使用题目语料；使用无标签池时，下载加 `--with-learning`，运行加 `--track unlabeled_pool`。评测前冻结全局提示词、参数与阈值；允许题内探索，不允许在题间传递评分反馈。

本地校验完整分类、引用位置与全量算术；付费模型先在不看 Agent 结论和标签的情况下检查抽样原文，再评估发现质量。证据分歧限制评分，证据未决保持空值。

单个发现得分为 `support × (15 + 25S + 20E + 30D + 10C)`，四维分别为统计有效性、证据支持、分析深度与校准。**分数必须与已评分数、未决数、无效数、缺失数和弃答数一起报告。**

[详细使用与续跑](docs/USAGE.zh-CN.md) · [输入协议](docs/AGENT_PROTOCOL.md) · [提交格式](docs/SUBMISSIONS.md) · [评分规范](docs/SCORING.md)

## 已有实验

三个开源 Agent 各运行 50 题，共 **150 次运行已结束**：86 份有效提交，70 份有数值评分，16 份证据未决，64 次未产生有效提交。各 Agent 的已评分均分为 11.95–19.57 / 100。

这是运行配置曾调整的开发实验，**不是严格控制条件的排行榜**。完整统计与限制见[实验结果](docs/RESULTS.zh-CN.md)。

## 数据与评测边界

语料来自 Amazon Beauty、Android App Reviews、CFPB 和 NHTSA，包含 20 道群体差异、15 道时间变化、15 道复合关联任务。可选学习池不带标签。

开放发现任务**没有固定参考结论**。测评仓库提供参考可用性记录，不是 50 份标注答案；根据语料证据及公开规则评分，参考覆盖率不可用。

算术全量校验，语义抽样评审，模型可能判断错误。数据此前公开，不是未见测试集；任务与学习池文档 ID 不重叠，但来源及实体可共享，任务不具备统计独立性。运行器本身不是安全沙箱。

[数据组成](docs/DATA.md) · [挑战要求](docs/DIFFICULTY.md) · [校验范围](docs/VERIFICATION.md) · [来源条款](docs/SOURCES.md)
