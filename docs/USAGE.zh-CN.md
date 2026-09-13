# 使用指南

[English](USAGE.md) | **简体中文**

## 1. 安装与下载

按[快速开始](https://github.com/erwinmsmith/TextInsightBench/blob/main/README.zh-CN.md#快速开始)安装，命令在克隆的仓库根目录运行，需要 Python 3.10+。`pip install -e .` 安装运行器及评分器。

`tib download --output data/participant` 按 `benchmark/data.lock.json` 的提交下载全部 50 道题目及任务语料，默认不下载学习池。

使用无标签学习池：

```bash
pip install -e '.[data]'
tib download --output data/participant --with-learning
tib verify --data data/participant --with-learning
```

任务语料是 gzip JSONL，学习池是 Parquet。[字段与数量](DATA.md)。

可选测评资源：`tib download --organizer --output data/evaluation`。当前评分无需参考文件；若使用 `--references data/evaluation/references.json`，judge 和 evaluate 必须采用同一配置。

## 2. 接入 Agent

每题通过 stdin 发送一个 JSON，含完整 `task`、`corpus.path` 绝对路径、压缩格式、文档数与哈希，以及可选 `learning_directory`。原文不内联在请求中，由 Agent 自己读取探索。

stdout 只返回一个符合[提交规范](SUBMISSIONS.md)的 JSON，日志写 stderr。保留原始文档 ID 和文本，使用精确引用位置。空 findings 表示弃答，不证明语料没有发现。仓库仅带弃答接口示例，不包含挖掘求解器。

## 3. 先单题，后全量

```bash
tib run --data data/participant --command 'python my_agent.py' \
  --limit 1 --timeout 3600 --output runs/pilot/submissions

tib run --data data/participant --command 'python my_agent.py' \
  --timeout 3600 --output runs/full/submissions
```

指定题目用 `--task-id TASK_ID`；学习池赛道加 `--track unlabeled_pool`。超时按每题计。每题启动新进程，校验后保存有效提交。

相同命令与配置重复运行可复用有效提交；命令、任务选择、超时或赛道改变时使用新目录。单题试跑与全量运行不能共用同一输出目录。

运行器不是安全沙箱。自行隔离生成代码、限制网络与资源，密钥不要放进代码执行环境；语料视为不可信数据，不向求解器提供评分反馈。

## 4. 评审与评分

在本地导出 `JUDGE_API_KEY`、`JUDGE_BASE_URL`、`JUDGE_MODEL`。服务需支持 chat completions JSON 输出，接口需要时在 base URL 加 `/v1`。CLI 不会自动加载 `.env`。

```bash
tib judge --data data/participant --submissions runs/full/submissions \
  --base-url "$JUDGE_BASE_URL" --model "$JUDGE_MODEL" \
  --audit-documents 160 --max-output-tokens 12000 \
  --output runs/full/reviews
tib evaluate --data data/participant --submissions runs/full/submissions \
  --reviews runs/full/reviews --output runs/full/report.json
```

模型评审收费，运行器不自动设费用上限。可先在 judge 命令加 `--limit 1` 或 `--task-id TASK_ID` 验证成本与接口。160 篇审计至少需要 14 次盲检请求，再做结论评分；长文本及格式修复可能增加请求。弃答不调用模型。

保留 `judge_config.json` 及 `.blind.json`，相同配置可复用已完成评审；配置改变用新目录。接口失败不是零分，应修正兼容问题后续跑，不应强行修改语义标签或挑选最高分重试。

evaluate 同时写 JSON 和 Markdown，已有报告不会覆盖，重新汇总请用新文件名。它始终评估全部题目，单题试跑会将其余 49 题记为缺失。

## 5. 查看报告

| 字段 | 含义 |
|---|---|
| `scored_tasks / tasks` | 获得数值评分的覆盖情况 |
| `quality_mean` | 仅全部题目均有分数时可用 |
| `conditional_quality_mean` | 仅已评分题目的均分，必须同时报告分母 |
| `valid_submission_rate` | 有效提交比例，包含弃答 |
| `abstention_rate` | 有效但不提交发现的比例 |
| `pending_tasks` | 待评审或证据未决，查看各题状态区分 |
| `missing_tasks`、`invalid_tasks` | 缺失或校验失败 |
| `reference_coverage_mean` | 当前无固定参考结论，因此不可用 |

分数为 0–100。零分是已评审但发现不成立或未完成目标，不是缺失运行。每题平均其发现得分；任一发现未决，该题质量分为空。

保存代码提交、数据锁、Agent 提交及配置、提示词、模型 ID、预算和评审配置。严格对比前应冻结配置；已有[开发实验结果](RESULTS.zh-CN.md)不代表控制条件一致的排行榜。
