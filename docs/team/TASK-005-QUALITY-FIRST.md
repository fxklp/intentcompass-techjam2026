# TASK-005：质量优先的按需 API 对照实验

日期：2026-08-31。范围：本机实现、有限真实调用、回归验证；未推送、合并或指派队友。

## 当前结论

**“API 的 HR、MRR、MTTC 三项全面优于强离线版”尚未实现。**
本轮没有 API 候选取得无退化的质量增益，因此不扩大付费全量评测、不启用候选。
默认仍为 `integrated / baseline / semantic off`，无网络、密钥或模型下载要求。
这不是算法的理论最优证明，也不是最终参赛提交批准。

原 TASK-004 全调用 Qwen Max 在 12 条样本中提高 MRR/MTTC、HR 持平的证据仍然保留。
本轮的调用压缩没有保住那组收益；不能据此断言 Qwen 没有价值或所有 API 路线都失败。
本轮没有完成任何 API 版 Public 200 / Shadow 200 验证，没有得到官方私有成绩。

## 已核查的官方政策

[当前官方提交规则](https://github.com/TechJam2026/techjam-conversational-search/blob/main/docs/submission_rules.md)
明确允许在参赛者自己的环境中联网调用 API，离线回退不是官方强制要求；没有统一的
CPU、内存或单轮响应时限。旧版 `docs/submission_rules.md` 与 TASK-004 报告中的
“最终评测可能禁网”属于历史快照，不应作为当前规则引用；没有改写官方快照文件。

[当前评分说明](https://github.com/TechJam2026/techjam-conversational-search/blob/main/docs/competition_specification.md)
说明延迟/token 属于可行性，不直接改变核心 TechnicalScore。MTTC 是轮数，不是秒数。
API 依赖、费用、token、延迟及回退必须披露。最终评测必须使用截止提交时冻结的
代码、提示词、索引和模型配置，不能看最终测试结果后再改方案。

本轮团队自定 p95 <=3 秒、请求硬截止 8 秒、峰值内存增量 <=64 MiB，允许 API
相对离线变慢。最终质量门槛仍是总体 HR/MRR 严格增加、MTTC 严格降低，同时无
分场景退化。初筛只要求不退化且至少一项改善，不代表最终通过。

## 实现边界

- 保留原离线检索、状态更新、追问、评分及默认推荐顺序。
- API 只收到当前安全上下文和当前候选的公开商品文本；精简文本保留标题前缀及
  显式需求对应的片段。没有隐藏答案、sample_id 路由或跨会话答案缓存。
- 按需调用、会话内精确输入缓存、最多三次请求尝试；reset 清除本会话缓存，
  改变偏好或候选文本/顺序使缓存失效。缓存命中不冒充新增 token 消耗。
- 返回完整合法整数序号排列，由本地映射回真实 ASIN；不自动修补伪造/缺失 ID。
- 没有 FTS 命中时保留原确定性 popularity fallback，不让 API 重排覆盖它。
- 所有请求沿用原持久账本，每次调用在同一数据库事务中检查总上限、平台上限和
  本次实验上限。未知费用继续保留预留，失败不自动重试。
- 基线与候选在独立子进程中跑同一官方 evaluator；报告保留失败、回退、真实调用率、
  全体响应及实际 API 响应的 p95。整轮熔断或预算不足的结果不得推广为模型收益。
- 新模块没有依赖、训练、UI、外部向量数据库；官方 evaluator/data/接口未改动。

## 固定 12 条筛选结果

选择为 Public 每种场景最先出现的三条；四类等量，不等于正式 40/40/15/5 分布。
所有配对离线对照为 HR 0.916667、MRR 0.713889、MTTC 6.333333、TechnicalScore 0.765834。
下表为原始 JSON 的阅读摘要，JSON 与校验值才是证据。

| 候选 | 有效排序/尝试 | HR | MRR | MTTC | 实际调用 p95 ms | 本次保守费用 RMB | 决策 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen Max demand20 | 12/12 | .916667 | .713889 | 6.333333 | 2088.26 | .536953 | 三项持平，不扩大 |
| Qwen Max demand40 | 10/10 | .916667 | .672222 | 5.750000 | 2945.54 | .660421 | MRR 下降，停止宽池方向 |
| Qwen Max demand20early | 10/11 | .916667 | .713889 | 6.333333 | 4230.92 | .664830 | 传输失败后熔断，不能代表完整模型质量 |
| DeepSeek Flash demand20early | 27/27 | .916667 | .713889 | 6.333333 | 1899.31 | .237150 | 三项持平，不扩大 |

demand20 为两类明确属性后重排20个候选、每个最多480字符；demand40 为40个候选、
320字符。第一阶段结果出来后，只追加了一个事先写明的通用修正：一类明确属性也可
触发调用（demand20early），其他条件不变。没有继续搜索提示词、阈值或 Shadow 标签。

demand40 的 Browsing MRR 从 .733333 降到 .566667；Buying MTTC 从 6.666667 降到
4.333333。不能只报告后一项优势。Qwen early 发生一次 `transport_failed`，之后
35 次响应因熔断使用离线结果；具体根因未获 HTTP 状态证实，不冒称平台故障。
其全部响应 p95 虽为1818.31ms，但真实调用 p95 为4230.92ms，因此仍未过延迟门槛。

## 费用

本轮60次请求尝试，59次有效排序；新增保守费用 **2.099354 RMB**。
原账本累计从7.011455变为 **9.110809 RMB**（含未知请求费用预留）。
Qwen累计5.591881，DeepSeek累计3.518928；总/平台硬上限仍为43.97 /20 /23.97。
余额不足没有触发停止；停止原因是未通过预定质量/有效运行门槛，不是预算耗尽。
以上不是平台实际账单，本轮未重新读取平台余额，未充值或重置账本。

[Qwen区域价格](https://help.aliyun.com/zh/model-studio/model-pricing) 与
[DeepSeek价格](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/) 已复核；仍按
保守非缓存价预留，未假设新加坡有北京免费额度。真实密钥不进入仓库/报告。

## 原始证据与版本

以下文件位于忽略的 `reports/generated/`；保留原始字节，不能覆盖旧实验。
每个实验 JSON 含前后 source SHA256 inventory、选样摘要、配置、账本前后值及
独立 baseline/candidate PID。Public 会话结果保存在 JSON；Shadow 不向算法侧输出目标。

| 文件 | SHA256 |
| --- | --- |
| task005-offline-baseline.json | 5175d6d48b2ea00406e87febb66f26912ec5ae370f061265df219db19ef48987 |
| task005-demand20-screen.json | 4986bd35129477d3ed6010bc2c1d5f1379d86a83eec5318f2cb1232f0dd2732a |
| task005-demand40-screen.json | 172633e5d7bfc555ea1bfb651099a41c4662c818baeece3ad309403f6def8d5c |
| task005-demand20early-max-screen.json | f93a644568fe96c5aa86de8daee102afb2f9d1814646448588df919a7ab8a72a |
| task005-demand20early-deepseek-screen.json | 0986373c453a4dca35b3d461fd4c17815eeac4ea64265a9d10d9a89d18e56562 |
| task005-final-shadow.json | a0e2c01a92fd5783732889c066e2a9feba4b39ff3b27cba547dbfb6abcda7f98 |

强离线初始快照：`2a039c00eb28e5e33ba019ad2c24e43bf0f26820`。
两组初筛源码：`ad9aa4685bcb17c34a9e5a8c54fe396029febb39`。
两组 early 源码：`e2a56775fd277ba54ebb81130e37a3e6b7953b72`。
之后只增加生命周期/并发预算测试及本报告，不改变已测运行时。

## 全量默认路径回归与交接

已重新运行 full team gate，输出 TEAM GATE PASSED。标准 Python 环境130项测试中
129通过、1项可选 ONNX 真实模型 smoke 跳过；没有失败。
默认Public 200：HR .91、MRR .624024、MTTC 4.255、TechnicalScore .777107，
总体和各场景与冻结基线一致。Demo：override 后第5轮命中、rank 8。
默认Shadow 200：HR .895、MRR .630488、MTTC 3.805、TechnicalScore .780546，
总体和各场景无退化。它是此前已使用的团队合成鲁棒性集，不是官方私有测试集。
独立可选依赖环境（`artifacts/semantic-venv`）也通过130/130测试，包括真实ONNX smoke，
没有跳过。默认部署仍不依赖该环境。

候选未推广，不因新增API代码给模拟评审自动加分。上一轮严格预演66/90的主要
扣分仍存在：没有新增可靠质量收益、私有效果未知、缺真实业务验证；展示10分未评。
本轮能证明的是按需调用和成本/失败处理可测试，不能证明整体方案已经最优。

当前仅本地分支，尚未提供远端新SHA，暂不让队友测试GitHub旧版来冒充本轮验收。
待队长决定共享冻结版本后，Liu/macOS和Cheng/Windows仅需复现，汇报给队长；
不给Wang派任务，不让队员彼此转派：

```text
python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py --full-eval
python demo/run_demo.py
git status --short
```

复现默认版不需要任何API key。不要为普通复现运行带 `--live` 的付费实验命令。
