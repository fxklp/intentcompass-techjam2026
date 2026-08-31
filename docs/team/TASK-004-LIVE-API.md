# TASK-004：真实 API 测试与本机收尾记录

日期：2026-08-31。主线算法未被云端模型替换；没有推送、合并或给 Wang 派任务。
软件功能和受控环境下的门禁满足本地交接条件，不等于正式提交审批或全局最优证明。

## 结论与边界

- 默认仍为 `integrated + baseline retrieval + semantic off`：无网络、无密钥可运行。
- 五个 API 模型均已发生真实调用；不是只做 mock 测试。
- Qwen Max 在固定 12 个公开场景中改善排序，但明显增加单轮延迟，因此不按本轮约束推广。
- DeepSeek Flash / Pro 有场景质量退化；两款 Qwen Flash 的严格筛选中断，不提供虚构完整分数。
- 停止增加付费试验，不继续调参，不对没有通过筛选的 API 候选运行全量 Public / Shadow。
- 保留可选模型实现和负结果；不能把可选 dense、cross-encoder 或 API 描述成默认算法的成绩来源。

## 账户与费用

密钥仅从队长指定的本地文件读入测试进程，不复制到仓库、报告或命令参数中。
文件里的 Qwen endpoint 是新加坡，已用完整密钥验证该地域的模型权限。
北京免费额度不能套用到新加坡；未假设存在可用赠送额度。

同一个原有账本 `artifacts/api-budget/task004.sqlite3` 保留所有历史条目，并收紧为：

| 项目 | 人民币 |
| --- | ---: |
| 总硬上限 | 43.97 |
| Qwen 硬上限 | 20.00 |
| DeepSeek 硬上限 | 23.97 |
| 全部试验保守费用（含未知请求预留） | 7.011455 |
| Qwen 分项保守费用 | 3.729677 |
| DeepSeek 分项保守费用 | 3.281778 |

共有 281 个账本请求条目，276 个有已返回 usage，5 个保留未知费用预留。
条目数不等于成功排序次数，也不证明每个请求都到达了服务器。
DeepSeek 官方余额接口实测从 23.97 变为 23.05，余额差 0.92；赠送余额为零。
Qwen 的实际账单未读取，不能用保守估计冒充实际扣费。
计费采用保守非缓存价；缓存与平台优惠可使实际费用更低。未充值、未自动重试。

价格与端点依据：
[Qwen 价格](https://help.aliyun.com/zh/model-studio/model-pricing)、
[Qwen 地域说明](https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope)、
[DeepSeek 价格](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)。

## 固定小样本对照：不能与 200 条全量分数混比

固定取 Public 每种场景最先出现的三条，共 12 条，选择先于模型调用。
此样本四场景等量，不代表正式 40/40/15/5 的总体分布。非思考模式，最多 20 个候选。
完整对照使用短整数序号，由程序映射回真实 ASIN；必须是完整、唯一、合法的排列。
不能自动补齐缺项、删除重复项后冒充有效模型输出。

| 模型 / 对照 | HR@10 | MRR | MTTC | TechnicalScore | p95 毫秒 | 结论 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 同样本离线对照 | .916667 | .713889 | 6.333333 | .765834 | 各次约 81–101 | 比较基准 |
| Qwen 3.8 Max | .916667 | .850000 | 6.166667 | .810000 | 2193.50 | 73 次有效排序；质量无场景退化，但延迟退化 |
| DeepSeek V4 Flash | .916667 | .750000 | 6.250000 | .778334 | 1870.76 | 74 次有效排序；Buying MTTC 6.666667→7 |
| DeepSeek V4 Pro | .916667 | .705556 | 6.500000 | .760000 | 2669.83 | 77 次有效排序；总体及 Buying 有退化 |
| Qwen 3.8 Flash | — | — | — | — | 3041.48（中断前） | 25 次有效排序后传输失败，中断 |
| Qwen 3.7 Flash | — | — | — | — | 1706.76（中断前） | 4 次有效排序后序号校验失败，中断 |

Qwen Max 的准确配对基线 p95 为 101.318 ms；不能称其速度也改善。
短序号协议提高了部分模型的可运行性，但 Qwen 3.7 Flash 仍有格式失败，因此不声称普遍改进。
最初的诊断还包括沙箱网络限制、点分段密钥被旧规则截断及 Windows 输入编码问题。
这些诊断报告保留，不算成功模型评测。对应问题已修复并补测试。

实测 API 源码固定在 `8a8270ab1c1742fb73e3c661b70c19ca23ee2da9`。
随后仅修正了防御性计费档位的 32K/256K 十进制边界；本次请求未触及该档位。
最终摘要分别核对 API 历史提交、当前离线运行时和冻结数据，不伪装成同一版本的原始证据。

## 全量默认方案复核

| 集合 | HR@10 | MRR | MTTC | TechnicalScore |
| --- | ---: | ---: | ---: | ---: |
| Public，200 条 | .910000 | .624024 | 4.255 | .777107 |
| Shadow，200 条 | .895000 | .630488 | 3.805 | .780546 |

总体和所有场景均与冻结基线相同。Shadow 是团队合成鲁棒性集，不是官方 800 条私有评测。
Demo 仍为 intent override 后第 5 轮命中、排名 8。未修改 evaluator、catalog、public labels、
评分公式、starter 接口或原 demo 断言。

最终验证：语义依赖环境 **118/118 tests OK**，full team gate 通过；
不安装 ONNX 的标准 Python 环境同样执行 118 项，117 项通过、1 项可选真实模型 smoke 跳过。
`git diff --check` 无问题；真实密钥内容扫描在跟踪文件中匹配数为零。
这些是本机 Windows 证据，不冒充新一轮 macOS/Linux CI 或队友审核结果。

### 两套速度结果都保留

1. 未限定 CPU 的三轮交替测试：平均响应中位数 45.444767→35.077099 ms，
   但 p95 101.4532→114.7739 ms，**未通过**原定 5% 容差。
   文件 `task004-postapi-*.json`；失败摘要未删除。
2. 预先选择首个可用逻辑 CPU（mask=1），只绑定基准子进程，不修改其他应用；
   相同 CPU 上三轮交替测试：平均 41.622191→25.211809 ms，
   p95 86.0441→79.0409 ms；p99 123.1334→122.1074 ms。
   此受控比较通过，不能推断所有调度条件下都更快。
3. 受控峰值内存中位数 444321792→454361088 bytes，增加约 9.57 MiB，
   在预先声明的 +16 MiB 审查范围内；冷启动 3.010872→3.278660 秒。
   不声称每一个资源指标都改善。

测速和最终软件源码快照：`edbc3873f77c22afa493e6650a3f55e0cd4b82c3`。
后续仅文档提交不改变上述运行时。两套数据支持“受控条件下可交接”，
不支持“未经限定的尾延迟必然改善”。队友复现应保留这个限制。

验证所有记录与当前源码：

```text
python -m tests.core.summarize_live --prefix task004-controlled
```

默认不加 `--prefix` 会核对那组未固定 CPU 的结果，并因其 p95 退化返回非零；这是预期。
不要删除记录、改大容差或重新贴上通过标签。

## 严格模拟评审（非官方分数）

依据 [官方赛题](https://bytedance.larkoffice.com/wiki/GdYFwzWNLiREsSkuIjZcDznInWc)
及 [官方模型/提交政策](https://github.com/TechJam2026/techjam-conversational-search/blob/main/docs/submission_rules.md)。

| 评分项 | 模拟分数 | 主要依据与扣分 |
| --- | ---: | --- |
| Technical Execution | 29/35 | 接口、状态覆盖、回退及真实 LLM 路径可验证；默认质量无新增收益，私有成绩未知 |
| Innovation & Problem Insight | 12/20 | 有约束状态、上下文管理及可组合检索；主要仍是成熟方法，复杂路线未带来全面收益 |
| Impact & Relevance | 12/20 | 电商场景与可复现效果明确；缺真实用户和业务收益证据 |
| Feasibility & Practicality | 13/15 | 无网默认、内存内检索、费用硬上限；调度敏感性及新版本跨系统独立复现仍欠缺 |
| Presentation & Communication | 未评 /10 | 仅 Final Event；不凭空给视频或现场展示分 |

已评部分合计 **66/90**。这是主观严格预演，不是官方通过线；TechnicalScore 也不是总成绩。
不因接入付费 API 自动增加创新或影响力分数。

遵守文本输入、静态只读商品库、最多 10 轮、合法 ASIN 和 headless 接口；
没有 UI、多模态、基础模型训练、重型外部向量数据库或隐藏标签访问。
模型网络依赖及离线回退必须披露，官方最终评分可能禁网。

## 队长交接

Wang 不派任务。Liu（macOS）和 Cheng（Windows）只需在共享冻结版本准备好后做简单复现，
汇报给队长，不互相转派任务。当前只是本机提交，尚未把新分支推送给她们。

```text
python -m unittest discover -s tests -p "test_*.py"
python scripts/team_gate.py --full-eval
python demo/run_demo.py
git status --short
```

无 API key 或大模型安装要求；无 ONNX 环境时可跳过明确标注的可选真实模型 smoke。
回报 SHA、测试数量/skip、门禁结果、Public 指标、demo turn/rank、工作区状态即可。
全部工作已按本轮不退化约束停止扩展；正式书面材料、YouTube 视频和远端提交状态未在此批准。
