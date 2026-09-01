# RC3 video handoff — facts to record, not fabricated output

> **Superseded.** This RC3 handoff is retained for provenance only. Do not use
> its architecture, metrics or script for the final TASK-306 video.

Use the frozen release version only after independent reproduction. Existing
Cheng storyboard `docs/submission/v2/storyboard-3min.md` in the full repository
remains historical and has not been overwritten. Reuse its story structure,
but update its old test count, timing reference, implementation status and
contribution/merge wording. No final video has been produced by this task.

## Suggested three-minute structure

| Time | Content |
| --- | --- |
| 0:00–0:20 | Problem: changing shopping intent and exact-match, early Top10 retrieval. |
| 0:20–0:40 | Actual default: structured state → in-memory FTS/BM25 → constraint/category/phrase/title ordering → guarded recovery + bounded clarification. |
| 0:40–1:40 | Record the real demo, including no preference, turn-4 override and turn-5/rank-8 hit. |
| 1:40–2:15 | Show the real full-Public result and source commit from release verification. |
| 2:15–2:40 | Explain zero runtime API tokens/cost, machine-specific resource measurements and rejected tradeoffs. |
| 2:40–3:00 | Limitations, next steps and actual team contributions. |

Start the recording by opening RELEASE-MANIFEST.json and showing source_commit,
then the command and its actual output. For direct demo commands, use a fresh
shell without experiment variables. The safer fixed-preset command is:

```text
python scripts/release_check.py
```

It prints the real demo and Public metrics, and stores full results. It does not
require Git, API keys or model files. Shorten idle waiting only, label the edit,
and keep commands and results from the same run. Do not retype console output
to make a prepared screen look executed. Never show credentials or private paths.

## Claims allowed

- The real Agent maintains explicit, replaceable preferences and handles the
  demonstrated override; the simulator, not the Agent, has the target label.
- Public HR .98, MRR .696861, MTTC 3.755, TechnicalScore .843958, if reproduced
  by the same recording release. Say Public, not official final score.
- Default is CPU-only, in-memory, no LLM model loading, zero runtime API cost.
- RC3's final policy improves overall HR/MRR/MTTC over TASK-013 on four measured
  sets, while retaining two explicitly accepted scenario MRR decreases. Do not
  claim every scenario improved. Do not mix RC1/RC2 footage, metrics or checksums
  with RC3, and do not describe repeated reproduction as a new holdout test.
- Development explored APIs/dense/multi-route methods but did not promote
  regressing candidates. That is a design decision, not a measured API gain.

Do not claim active hybrid/dense retrieval, active LLM ranking, learned guidance,
hard guaranteed constraint satisfaction, persistent personalization, real business
conversion improvements, or 100% four-pillar coverage. Explain limitations plainly.
Use the current test count produced by the full checkout; the ZIP checker is not
the entire unit suite. Do not carry over the old 37.736ms/76.583ms timing claim
as a measurement of the newest run; METHOD.md labels TASK-015's controlled
measurement: p95 102.46 ms, approximately 5.48 ms above TASK-013. It is not a
cross-platform guarantee, and the ZIP checker is not the timing benchmark.

Final upload must be **public** on YouTube, not private or unlisted, and linked
in the Devpost description. Use English narration or English translation/subtitles.
Review third-party music/logos/assets for permission. Final duration, visibility,
video URL, subtitles, source commit and checksums must be checked before submission.

Liu and Cheng report to the team lead. Neither assigns work to the other.
Wang is not assigned work in this phase. The lead decides when recording starts.
