# GitHub collaboration setup

## Repository ownership

The repository may be owned by the team lead's personal GitHub account. Adding
the other three GitHub usernames as collaborators turns that single repository
into the team's shared source of truth; a separate “team account” is unnecessary.

Personal-account repositories have only two permission levels: owner and
collaborator. Therefore the team lead remains the integration owner and members
must not push directly to `main`, even if GitHub technically permits it.

## Initial remote setup

The integration owner pushes the accepted local history to the empty private
repository. Do not upload loose files through the browser and do not commit
`data/catalog.jsonl`.

After collaborators accept their invitations, every member runs:

```bash
git clone <team-repository-url>
cd intentcompass-techjam2026
python scripts/setup_data.py
python demo/run_demo.py
python scripts/team_gate.py
```

## Mandatory branch flow

1. Start from current `main`.
2. Create one task branch named `<lane>/TASK-<number>-short-name`.
3. Change only the task card's allowed paths.
4. Run the proof commands in the task card.
5. Push the branch and open a pull request using the repository template.
6. A different person reviews it; Liu may block missing evidence.
7. Only the integration owner merges after the `full-evaluator` check passes.

The GitHub Actions workflow downloads the catalog from the organizer, runs the
team gate plus all 200 official public sessions, and retains the evaluator JSON
for 14 days. It uses read-only repository permissions and no secrets.

## Branch-protection limitation

GitHub Free supports collaborators on private personal repositories, but branch
protection for a private repository requires GitHub Pro or a paid team plan. If
the owner has GitHub Pro (including an activated eligible student benefit), set
protection on `main` to require:

- a pull request;
- one approval;
- status check `full-evaluator`;
- resolved conversations;
- no force pushes or deletion.

If protection is unavailable, the same flow remains mandatory by team policy,
but enforcement is social: collaborators must never push to `main`, and only
the integration owner clicks Merge.
