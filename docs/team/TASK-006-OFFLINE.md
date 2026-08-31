# TASK-006：离线约束与字段重排验证

## 最终结论

本轮完成，**没有获得符合不退步门槛的分数提升**。默认 integrated Agent
只启用经验证的 `constraints` 语义修复；原候选池、提问策略、检索后端不变。
四个字段排序候选均不推广，默认不读取字段缓存或分配字段 rowid 目录。
保留显式 `baseline` 开关供复现；旧 baseline/adaptive core 模式默认不变。
字段策略只保留为关闭的实验开关，不建议部署或与其他实验后端组合使用。

Public 默认结果仍为 HR 0.91 / MRR 0.624024 / MTTC 4.255 /
TechnicalScore 0.777107。此分数不是比赛总分，也不能证明隐藏集或全局最优。
本轮新增 API 调用和费用均为 0；未充值、读取密钥或修改预算账本。

## 范围与决策依据

冻结基线：`2181f9952763a01d4b6d99b1a4166a5218c77401`。
本轮只做离线实验，不读取密钥、不调用 API、不改官方数据、评分器、提问策略或候选池大小。
所有质量判断同时检查总体及四个场景的 HR、MRR、MTTC；容差保持 1e-6。
总体提升但某个场景退步不算通过。约束语义修复与分数提升分别报告。

## Public 失败归因

200 个会话中有 18 个未命中：9 个在所有轮次的候选池中均未出现目标，
另 9 个曾出现目标但没有最终命中。后者只是跨轮次可用性诊断，可能包含
意图切换前的目标出现，不能推断这些会话都能靠重排修好。
182 个命中会话中，104 个排名第 1、31 个排名第 2–3、47 个排名第 4–10。
诊断在 Agent 执行完后由测试侧读取标签；生产算法不读取目标、答案或场景标签。

## Public 完整对照

| 策略 | HR@10 | MRR | MTTC | TechnicalScore | 决策 |
| --- | --- | --- | --- | --- | --- |
| 冻结基线 | 0.910 | 0.624024 | 4.255 | 0.777107 | 对照 |
| 约束语义修复 | 0.910 | 0.624024 | 4.255 | 0.777107 | 仅有资格继续验证稳健性 |
| F1 字段证据加分 | 0.910 | 0.620782 | 4.215 | 0.776935 | 拒绝：Browsing MRR 下降 |
| F2 完整属性组优先 | 0.910 | 0.607254 | 4.135 | 0.774476 | 拒绝：Buying HR/MRR 等下降 |
| F3 只重排原 Top10 | 0.910 | 0.631337 | 4.255 | 0.779301 | 拒绝：Buying MRR 下降 |
| F4 逐短语证据严格包含才交换 | 0.910 | 0.631337 | 4.255 | 0.779301 | 拒绝：Buying MRR 下降 |

F3/F4 的 Buying MRR 从 0.613323 降为 0.613274，差值 -0.000049。
不能因差值很小而临时放宽标准，也不能只报告整体 MRR 上升。
四个字段策略均止步于 Public，不进入 Shadow，不再搜索新规则。
各策略首轮响应 p95 分别为基线 71.503ms、约束 71.2512ms、
F1 83.0627ms、F2 81.7283ms、F3 81.9275ms、F4 79.0772ms。
这些是单次探索测量，不是三轮速度验收；字段策略已因质量退步被淘汰。

## 约束修复的能力边界

仅识别显式单一颜色/材质排除，例如 `not cotton`，避免将它当作正向棉质偏好；
商品没有该字段时视为未知，不宣称满足排除条件。排序惩罚不是硬过滤，
无法保证所有被推荐商品都满足排除约束。复合否定、自由长句不在本次解析范围。

已经进入 budget 槽的 `under/below/up to` 等表达使用价格上限语义，
上限内商品不会仅因比上限更便宜而扣分；`around $100` 仍保留目标价格语义。
没有改状态解析器，因此不能宣称所有这些自然语言表达都能端到端进入 budget 槽。
这些是限定输入上的正确性改善；Public 分数完全相同，不是实测检索质量提升。

## 固定集合确认

约束候选与对照在以下每组总体及四类场景指标上均完全一致。

| 集合 | 会话数 | HR@10 | MRR | MTTC | TechnicalScore |
| --- | --- | --- | --- | --- | --- |
| Public | 200 | 0.910 | 0.624024 | 4.255 | 0.777107 |
| 既有 Shadow | 200 | 0.895 | 0.630488 | 3.805 | 0.780546 |
| 新种子合成确认集 | 200 | 0.930 | 0.666312 | 3.645 | 0.811994 |

确认种子在出结果之前固定为 `intentcompass-task006-confirmation-20260831`。
它使用同一商品目录、排除 Public 目标；不保证与此前 Shadow 目标完全互斥，
也不是官方隐藏测试集。只看聚合结果，不据此改规则。不同测试集的绝对分数
不能互相冒充提升，例如 0.93 对 0.91 不是算法增益。

速度对照采用 2181f99 原始 ranker/controller 的只读进程内加载，
其余生产源码与该提交没有变化。输出另存两模块的原始字节哈希，
因此不仅比较新代码中两个策略开关的速度，也计入新增分支的开销。

### 三轮速度验收

Windows、本机 Python 3.13.9；独立子进程顺序执行，不并行、不挑选重跑。

| 测量 | 冻结基线 | 约束修复 |
| --- | --- | --- |
| 三轮响应 p95（ms） | 72.1603 / 71.7555 / 71.1930 | 71.4605 / 71.5195 / 72.4481 |
| p95 中位数（ms） | 71.7555 | 71.5195 |
| 三轮最大峰值内存（bytes） | 452055040 | 450809856 |
| 初始化中位数（s） | 3.154317 | 3.199749 |

p95 约 -0.33%，在计时噪声量级，不宣称加速收益；通过 +5% 上限。
峰值内存没有增加，通过 +16MiB 上限。初始化约 +0.045 秒，单独披露。
六次 Public 测量的总体及场景质量指标均相同。之后只切换默认配置并增加
验证测试，没有改已测排序逻辑；默认完整门禁再次确认相同 Public 指标。

## 原始证据

忽略目录 `reports/generated/` 中保留所有原始输出，未覆盖旧实验。
JSON 含运行配置、源码/数据 SHA256 清单及运行前后清单一致性。
首批 Public 实验对应 `f8b447b`；F4 对应其后五个文件的未提交改动，
以输出中的源码字节哈希为准，不冒称 F4 来自干净提交。

| 文件 | SHA256 |
| --- | --- |
| task006-diagnosis.json | b927e731280f459feae39ed7a0941eb90ffedeebabca486353900f6898c0dbb7 |
| task006-baseline-public.json | 2d9b2c676deaabae06c374d71ac999afe333920b5046ac0321f64a6f82e5fc69 |
| task006-constraints-public.json | 9e0f23bf1b509d41e3678a806bef82e01aa48424173408a84e2da3e1f8a257ab |
| task006-field-bonus-public.json | 398beda485c7446aba7a5dea2e0fececff28944915a41807d28273559e117511 |
| task006-field-groups-public.json | b97d95927e8efbc2283ad41e8f047ff6e2a88edb36ed12c8e24e0ea1855366dd |
| task006-field-top10-public.json | d3ad406b1b3d03d3d18321cdc750e7f522971ae3b6099dc3da08bcedcd60527f |
| task006-field-dominance-public.json | 8bee708bfb5493d99647fd82d503c63585db12e945ccfe157349ec5a9c1ba38a |
| task006-baseline-shadow.json | 91757f1b202e4eb470df3500739bd9def5960cbd6c6e6aabe9fed70c9a254a15 |
| task006-constraints-shadow.json | 53ec593677015dd8121fe01dccde6220553735f868095bc8fef6b822c167b30e |
| task006-baseline-confirmation.json | c399f125d3ac60b35a2376a303d2e65e60f99433fa2a1ffbbeb9e0fbb32db772 |
| task006-constraints-confirmation.json | af79249b0e783c06c32ca037b493c266a7064da6aa996996931409aa543c5786 |
| task006-speed-baseline-1.json | fd16abb4109cf9799b2d11ab511bb40f70d2c06cb3b8211f6904f4d556016f6f |
| task006-speed-baseline-2.json | fe367b6396b113ad70154744a554429d38317aa86a46cb2c866fb7df4ea9834c |
| task006-speed-baseline-3.json | 85c0477b21d29afac6f1a7f5d45b163b56f17a7b068c0fbe993f631217af7f7d |
| task006-speed-constraints-1.json | d9cff5966f63315395e5a51e315c95c9e563a1e12846551fdb808450575e4783 |
| task006-speed-constraints-2.json | f397298a55436fe5865bad458b92ba68c8e691ed32448479f8db9a1e4d7c901b |
| task006-speed-constraints-3.json | 00b8fc08cf8e6566feffda965a026ba831ebd1ce73e1aa85ec0efe3932cfbe2a |

## 验证与交接

- 本轮专项测试 14/14 通过，含状态解析到排序、默认策略、无网络调用、fallback/reset。
- 标准环境全套 144 项：143 通过，1 项可选 ONNX smoke 因依赖环境跳过，无失败。
- `artifacts/semantic-venv` 环境 144/144 通过，真实 ONNX smoke 也通过，无跳过。
- `python scripts/team_gate.py --full-eval`：TEAM GATE PASSED。
- `python demo/run_demo.py`：意图切换后第 5 轮命中，rank 8。
- 原始实验的官方 data/evaluator/starter 哈希与最终文件一致；git diff --check 通过。
- 只修改当前本地集成分支。未 push、未新建 PR、未合并、未自审，也未运行远端 CI。

生产默认不需要 API key、显卡或语义模型依赖。队友应等队长共享本轮冻结版本，
不要用 GitHub 上旧版本冒充本轮验收。后续 Liu/macOS、Cheng/Windows 简单复现：

```text
python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py --full-eval
python demo/run_demo.py
git status --short
```

先确认没有人为设置 `INTENTCOMPASS_*` 实验环境变量。本轮未在 macOS/Linux
重跑，跨系统仍需队友验证；结果交给队长，不让队员互相转派，不给 Wang 派任务。

如需独立复核（使用新的输出文件名，不覆盖现有证据）：

```text
python -m tests.core.check_offline --policy baseline --frozen-baseline --output reports/generated/task006-review-baseline.json
python -m tests.core.check_offline --policy constraints --output reports/generated/task006-review-constraints.json
```

若要再提高分数，需要新的可泛化证据或不同方法；不能把已被否决的 tradeoff
包装为全面提升。本轮按照既定停止条件结束，不因投入时间而强行启用候选。
