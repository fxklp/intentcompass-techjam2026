# TASK-007：冻结候选版复现与录制交接

本轮只封装，不调整算法。此文件是测试指令，不等于测试已通过或已完成提交。
以指挥官交接时提供的 ZIP SHA256、RELEASE-MANIFEST.json 内完整 source_commit
及实际 verification.json 为证据；不要用 GitHub 旧分支代表这一版。

## 队长先做

把同一个 `intentcompass-rc1.zip` 连同独立提供的 SHA256 发给 Liu 和 Cheng。
这是带版本清单的完整源码包，不是互相拷贝散文件。解压到新的目录，不覆盖
任何人的工作区。ZIP 不含密钥、模型、缓存或商品目录；初次准备数据需要网络。
若改为 GitHub 共享，先推送并确认同一个提交可访问；本任务未自动推送/合并。

## 转发 Liu：macOS 简单复现

请仅测试，不改代码、不指定下一位队员、不审核自己代码。使用 Python 3.12/3.13：

```text
shasum -a 256 intentcompass-rc1.zip
```

与队长提供的哈希核对后，解压进入目录：

```text
python3 scripts/setup_data.py
python3 scripts/release_check.py
```

## 转发 Cheng：Windows 简单复现，然后准备视频

先只测试，不改算法或尝试 API，PowerShell 执行：

```powershell
Get-FileHash .\intentcompass-rc1.zip -Algorithm SHA256
```

核对后解压到新目录，进入目录执行：

```text
python scripts/setup_data.py
python scripts/release_check.py
```

不要在压缩文件预览窗口内直接运行；不要把包叠加解压到旧仓库。
无需安装 ONNX、Torch、Qwen/DeepSeek SDK，也不需要把任何密钥发给其他人。

## 两人分别向队长回报

1. OS/Python 版本；RELEASE-MANIFEST.json 中的完整 source_commit。
2. ZIP 哈希是否一致，数据校验是否成功。
3. `RELEASE CHECK PASSED` 是否出现；如失败，停止，不自行改测试或代码。
4. Public：HR .91、MRR .624024、MTTC 4.255、TechnicalScore .777107。
5. Demo：first hit turn 5、rank 8；network_attempts 0。
6. 回传本次新生成目录内的 verification.json 和 results.json 给队长。

这是紧凑发布包验收，不是完整 Git 仓库全部 unittest；不要把两者测试数混用。
这些标准只适用于当前 Public 集，未来官方 final 集不能用这些固定分数验收。

## 录制启动条件

两人复现无阻塞问题后，由队长通知 Cheng 开始正式录制。可先整理现有 storyboard，
正式录屏必须用此次核验的同一源码版本。采用 docs/release/VIDEO-HANDOFF.md，
尤其更新旧性能数值和测试数。只展示实际启用的离线能力；不要声称 dense/LLM
实验处于默认路径，也不要把 TechnicalScore 当赛事总分。

Wang 本阶段没有任务。所有测试/录制进展通过队长传递。

## 不属于本地通过的事项

macOS/Linux 新版本复现、GitHub 公共冻结提交、最终英文 Devpost 描述、公开三分钟
YouTube 视频、最终表单提交及官方 final 评估仍需各自证据。规则权重冲突和
四大支柱能力边界见 docs/release/REQUIREMENTS.md。不要将任何待办标为已完成。
