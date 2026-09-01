# RC3 independent acceptance / 队员测试指令

Liu: macOS. Cheng: Windows 11. Both report only to the team lead. Do not assign
each other tasks, edit code, merge/push, or start video recording before approval.
Wang has no task in this phase. Use the SAME ZIP and external SHA256 supplied by
the lead; the ZIP cannot contain its own final checksum.

## 1. Verify ZIP before extracting / 先核对压缩包

Place `intentcompass-rc3.zip` in a convenient folder and open a terminal there.
The calculated hash must match the lead's separate message; stop on mismatch.
Do not reuse RC1/RC2 folders or copy any old Python files into RC3.

Windows PowerShell:

```powershell
Get-FileHash -LiteralPath '.\intentcompass-rc3.zip' -Algorithm SHA256
```

macOS Terminal:

```sh
shasum -a 256 intentcompass-rc3.zip
```

## 2. Fresh folder, then run / 新目录解压并运行

Only continue after the ZIP checksum matches. Use Python 3.12 or 3.13 with
SQLite FTS5. Do not install API/model dependencies; no API key or GPU is needed.
If the Python command is unavailable or reports another version, report that
to the lead instead of letting an agent alter your environment automatically.

Windows PowerShell:

```powershell
$rc3Dir = Join-Path (Get-Location) ('intentcompass-rc3-test-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
Expand-Archive -LiteralPath '.\intentcompass-rc3.zip' -DestinationPath $rc3Dir
Set-Location -LiteralPath $rc3Dir
python --version
python -B scripts/setup_data.py
python -B scripts/release_check.py
```

macOS Terminal:

```sh
rc3_dir="$(mktemp -d ./intentcompass-rc3-test.XXXXXX)"
unzip -q intentcompass-rc3.zip -d "$rc3_dir"
cd "$rc3_dir"
python3 --version
python3 -B scripts/setup_data.py
python3 -B scripts/release_check.py
```

Data setup needs network once. You may instead copy ONLY the previously verified
`data/catalog.jsonl` into the new `data/` folder, then run setup_data.py to check
its hash. Never copy solution/starter/evaluator/scripts from another version.
The release check itself forbids network calls and ignores inherited experiment
settings in its own process; it does not change the parent shell environment.
No Git executable or repository checkout is needed for the extracted ZIP.

## 3. Expected result / 预期结果

- `RELEASE CHECK PASSED`
- Demo: `OFFICIAL HIT after intent override`, first hit turn 5, rank 8.
- Public N=200; HR@10=.98; MRR=.696861; MTTC=3.755;
  local TechnicalScore=.843958; model tokens=0; network attempts=0.
- The evidence directory printed at the end contains `results.json` and
  `verification.json`. The latter records Python executable/version/platform,
  `release_id=intentcompass-rc3`, source commit, final algorithm commit and hashes.

This checks Public reproduction, not hidden-data scoring or contest submission.
Do not adjust assertions or copy another person's outputs if a check fails.
Preserve the traceback and send it to the lead without editing the package.

## 4. Return to the lead / 回传材料

Send the lead, not the other teammate:

1. Actual ZIP SHA256.
2. OS and Python version; whether the terminal or coding agent ran the command.
3. `RELEASE CHECK PASSED` and Demo turn/rank, or the full error text.
4. The SAME run's `results.json` and `verification.json` as files.

Two screenshots without JSON are not complete evidence. JSON may contain local
filesystem paths; send privately to the lead, not to the public repository/video.
Do not expose keys. Keep the untouched ZIP and test folder until signoff.
