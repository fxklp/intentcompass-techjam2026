# RC3 release requirements audit — 2026-08-31

This is a technical/claim audit, not an organizer certification. Current sources:

- [Track 4 statement, sections 4.2–4.6](https://bytedance.larkoffice.com/wiki/GdYFwzWNLiREsSkuIjZcDznInWc), read in the browser, showing an August 31 update.
- [Official submission rules](https://github.com/TechJam2026/techjam-conversational-search/blob/main/docs/submission_rules.md), read live August 31.
- [Devpost requirements](https://tiktoktechjam2026.devpost.com/) and [rules](https://tiktoktechjam2026.devpost.com/rules), read live August 31.

The checked-in participant rules are preserved as historical source files.
Current GitHub rules explicitly permit a non-LLM approach and optional APIs,
with no common hardware/time limit. Offline fallback is optional officially;
we choose an entirely offline default. The final package is released after the
Devpost deadline; use the frozen submitted commit and unchanged final evaluator.

## Contract, scope and data

| Requirement | Evidence / disposition |
| --- | --- |
| Python Agent/reset/respond, natural message, allowed clarification field | Thin adapter retained; checker validates every Public response. |
| Maximum 10 turns, valid unique Top10 IDs, override scoring eligibility | Original evaluator/contract untouched; tests and actual demo. |
| Frozen 50,000-item catalog, no invented ASINs or data mutation | Official setup checksums; runtime before/after hashes; payload validation. |
| Released Public sessions and original scorer | Public data/evaluator source unchanged from runtime freeze. |
| Text/metadata/dialog only; no UI, foundational training or heavy DB | Default has none; one in-memory FTS index, no model loading. |
| Environment, model choice, latency, tokens, cost, fallback disclosure | README and METHOD.md distinguish runtime from development experiments. |
| Reproduce from delivered files | Allowlisted ZIP + manifest + fresh-environment release checker. Final measured result is in the team handoff, not presumed here. |
| Private/final evaluation | Not run; no access or invented score. Freeze first, evaluate released package later. |

## Four-pillar feature coverage is not all green

| Track 4.2 feature | Actual default status |
| --- | --- |
| Buying/Browsing split | Rule-derived routing labels exist; separate precision/dense engines are not active. Partial. |
| Multi-route keyword/category/vector + LLM ranking | Lexical FTS, constraints, category/full-phrase/title evidence and guarded terminal recovery active. These are NOT dense or separate simultaneous retrieval engines. Dense, multi-route and LLM experiments disabled. Not covered by default. |
| Information accumulation / intent replacement | Implemented in structured slots; reset/override tests and demo. |
| Over-generality retrieval cutoff / proactive clarification | Structured questions plus an earlier eligible `other` question after three no-preference replies; not a learned question policy or full lexical cutoff. Partial. |
| Personalized context distillation | Bounded context and updated session-local profile export. No persistent cross-session model. Partial. |
| Workflow re-orchestration / self-evolving guidance | Explicit workflow state exists, but frozen retrieval/question policy remains conservative. Partial. |
| HR/MRR/MTTC evaluation | Full Public measurement; no claim of official final performance. |

The website's ambitious pipeline wording and the explicit permission for non-LLM
methods must not be collapsed into "every feature is mandatory" or "every feature
is complete." Full four-pillar coverage is not claimed. If the organizer treats
the richer pipeline as a must-have rather than a scoring direction, ask for a
clarification before representing the release as fully compliant. Do not silently
enable rejected experiments to make the architecture diagram look complete.

## Deliverables and pending actions

| Item | Status |
| --- | --- |
| README: overview, setup, reproduction, limitations, contributions | Prepared in English for this release. |
| Written Devpost description: problem, tools, APIs, libraries, data/assets | METHOD/README provide facts; form completion and final review remain pending. |
| Public repository containing the frozen commit | Current local commit must be shared/pushed and publicly accessible before submission. Not done by building a ZIP. |
| Public three-minute YouTube end-to-end video | Pending. Backend API/CLI walkthrough is explicitly accepted. |
| English submission or English translation | English project documents prepared; check final narration/subtitles and form. |
| Third-party rights / no unauthorized logos, music or assets | No new media added. Team must check final video and attribution. No legal clearance claimed. |
| Team registration, eligibility, representative, submitted form | User-owned checks; not inferred from code or old registration activity. |
| New macOS/Windows independent reproduction | Pending Liu/Cheng; all communication through the lead. |

## Scoring and deadline caution

The Track 4 table lists 35% Technical Execution, 20% Innovation, 20% Impact,
15% Feasibility and 10% final-event Presentation. Devpost legal rules instead
say four Stage Two criteria are equally weighted. This source discrepancy is
recorded, not silently resolved; seek organizer confirmation if using weights.
No definitive total-score prediction is issued from these conflicting weights.

Technical evidence is strongest in reproducibility and constraints/state handling;
innovation, full pipeline coverage and real-user impact remain weaker. The old
66/90 internal estimate is not an official score and is not upgraded because
packaging exists. RC3 Public TechnicalScore .843958 is a separate benchmark composite.
The accepted final policy improves overall metrics but retains two disclosed
synthetic-scenario MRR decreases; see METHOD.md. Do not claim all-scenario
non-regression or use packaging as a new quality experiment.

Devpost currently gives **September 1, 2026, 12:00 noon GMT+8** as the submission
deadline, not midnight. The submitted commit is frozen then. Do not change the
solution after inspecting final labels; retain complete results, commit and
environment details. Publishing/submitting is still a separate authorized action.
