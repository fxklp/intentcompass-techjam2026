# ADR-0012: authorized local integration, CPU semantics, bounded API costs

Date: 2026-08-31. Decision owner: team lead (explicit conversation authority).

## Context and ownership

The lead requested local end-to-end implementation while Wang is unavailable.
TASK-004 supersedes the previous retrieval/core lane separation for this branch
only. Shared official interfaces and evaluator/data remain frozen. Existing
baseline, DualRoute, and TASK-003 evidence remain reproducible and unmodified.

## Models and dependencies (before installation)

Use pretrained inference, not training or full-parameter fine tuning. Text only.
Optional CPU dependencies: NumPy, ONNX Runtime 1.29.0 (MIT), tokenizers 0.23.1
(Apache-2.0). Install into a dedicated virtual environment, never the user's
global environment. Default lexical inference needs only Python stdlib.

Optional assets, both Apache-2.0, from their authors' Hugging Face repositories:

- sentence-transformers/all-MiniLM-L6-v2, revision
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`;
  `onnx/model_quint8_avx2.onnx`, tokenizer, license.
- cross-encoder/ms-marco-MiniLM-L6-v2, revision
  `233902d25c440f23af6f7d6e94d2946bac0bee0a`;
  `onnx/model_quint8_avx2.onnx`, tokenizer, license.

Rationale: actual learned text semantics on this CPU without a GPU, remote
code, training, a service, or an industrial vector database. Each quantized
model is approximately 23 MB. 50,000 x 384 float32 catalog vectors require
76.8 MB; exact search is in RAM. Catalog-derived cache stays ignored with
model/catalog/file hashes. Runtime never downloads missing assets and falls
back to lexical retrieval. A setup script explicitly downloads pinned assets
and builds the cache; assets are not committed. Download/inference API cost $0;
local time/memory and quality must be measured before recommending enablement.

## APIs and prices

Sources checked 2026-08-31:
https://help.aliyun.com/zh/model-studio/model-pricing
https://help.aliyun.com/zh/model-studio/new-free-quota
https://api-docs.deepseek.com/zh-cn/quick_start/pricing/

China Beijing Qwen free allocations are account/model specific and expire.
DeepSeek can debit granted balance first, but no universally free API is
promised. Web-chat access does not establish free API access. Check credentials
and region before a real request. No account signup, payment, or automatic topup.

Budget conservatively uses undiscounted/cache-miss peak RMB per million tokens:
Qwen3.8-Flash 1/3 input/output; Qwen3.8-Max 12/36;
Qwen3.7-Flash 0.2/0.8 for <=32k input; DeepSeek-V4-Flash 3/9;
DeepSeek-V4-Pro 9/27. Only verified Beijing Qwen pricing is initially allowed.
Input is bounded; thinking is disabled; output capped. Reserved maximum cost
counts against the same RMB100 ledger even when credits may cover it. The
ledger is local and cannot account for unrelated programs spending the same
account. This task's requests must all use it. Failed/unknown billing is not
reported as free. Calls stop before the authorized cap; no background retries.

Model requests carry only bounded public candidate text and current safe
context, never keys in logs or hidden labels. Validate exact ID permutations,
usage and completion; invalid/timeout output preserves offline results.

## Acceptance and rollback

Fixed experiment order and non-regression gates are in TASK-004. Optional
features are not evidence of quality improvement. Maintain the reviewed
offline route if measured quality, speed, or reliability worsens. Disable all
optional model flags to roll back; no data migration is required.
