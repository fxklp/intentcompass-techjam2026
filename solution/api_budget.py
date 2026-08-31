"""A shared durable RMB ledger; reserve BEFORE sending, fail closed on errors."""
from __future__ import annotations

import sqlite3
import uuid
from contextlib import closing
from pathlib import Path


CAP_MICRO_RMB = 100_000_000


class BudgetUnavailable(ValueError):
    pass


class BudgetLedger:
    def __init__(self, path: Path) -> None:
        self.path = path.resolve()
        # Initialization is explicit in the probe/setup tool. Runtime never
        # silently creates a replacement budget if a ledger was moved/deleted.
        if not self.path.is_file():
            raise BudgetUnavailable("shared budget ledger not initialized")

    @staticmethod
    def initialize(path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Never overwrite or reset an existing budget.
        with path.open("xb"):
            pass
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("CREATE TABLE policy (id INTEGER PRIMARY KEY CHECK(id=1), cap INTEGER NOT NULL, blocked INTEGER NOT NULL)")
            db.execute("INSERT INTO policy VALUES (1, ?, 0)", (CAP_MICRO_RMB,))
            db.execute("CREATE TABLE calls (id TEXT PRIMARY KEY, model TEXT NOT NULL, reserved INTEGER NOT NULL CHECK(reserved>=0), charged INTEGER NOT NULL CHECK(charged>=0), status TEXT NOT NULL, prompt_tokens INTEGER, completion_tokens INTEGER)")

    def restrict(self, cap: int, provider_caps: dict[str, int]) -> None:
        """Lower ceilings in the SAME ledger, without clearing previous charges."""
        if (type(cap) is not int or not 0 < cap <= CAP_MICRO_RMB
                or set(provider_caps) != {"qwen", "deepseek"}
                or any(type(v) is not int or not 0 < v <= cap for v in provider_caps.values())):
            raise BudgetUnavailable("invalid restricted budget")
        with closing(sqlite3.connect(self.path, timeout=3)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            old_cap, blocked = db.execute("SELECT cap, blocked FROM policy WHERE id=1").fetchone()
            used = db.execute("SELECT COALESCE(SUM(charged),0) FROM calls").fetchone()[0]
            if blocked or not used <= cap <= old_cap <= CAP_MICRO_RMB:
                raise BudgetUnavailable("cannot raise or invalidate existing budget")
            db.execute("CREATE TABLE IF NOT EXISTS provider_limits (provider TEXT PRIMARY KEY, cap INTEGER NOT NULL CHECK(cap>0))")
            for provider, amount in provider_caps.items():
                old = db.execute("SELECT cap FROM provider_limits WHERE provider=?", (provider,)).fetchone()
                spent = db.execute("SELECT COALESCE(SUM(charged),0) FROM calls WHERE model LIKE ?", (provider + "%",)).fetchone()[0]
                if amount < spent or (old and amount > old[0]):
                    raise BudgetUnavailable("cannot raise or invalidate provider budget")
                db.execute("INSERT INTO provider_limits VALUES (?,?) ON CONFLICT(provider) DO UPDATE SET cap=excluded.cap", (provider, amount))
            db.execute("UPDATE policy SET cap=? WHERE id=1", (cap,))

    def reserve(self, model: str, maximum_micro_rmb: int, *, ceiling_micro_rmb: int | None = None) -> str:
        if type(maximum_micro_rmb) is not int or maximum_micro_rmb <= 0:
            raise BudgetUnavailable("invalid cost reservation")
        if ceiling_micro_rmb is not None and (type(ceiling_micro_rmb) is not int or not 0 < ceiling_micro_rmb <= CAP_MICRO_RMB):
            raise BudgetUnavailable("invalid run ceiling")
        identifier = uuid.uuid4().hex
        with closing(sqlite3.connect(self.path, timeout=3)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            policy = db.execute("SELECT cap, blocked FROM policy WHERE id=1").fetchone()
            if policy is None or policy[1] != 0 or not 0 < policy[0] <= CAP_MICRO_RMB:
                raise BudgetUnavailable("budget policy invalid or circuit blocked")
            used = db.execute("SELECT COALESCE(SUM(charged),0) FROM calls").fetchone()[0]
            if ceiling_micro_rmb is not None and used + maximum_micro_rmb > ceiling_micro_rmb:
                raise BudgetUnavailable("run spending ceiling would be exceeded")
            if used + maximum_micro_rmb > policy[0]:
                raise BudgetUnavailable("experiment budget would be exceeded")
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='provider_limits'").fetchone():
                provider = next((name for name in ("qwen", "deepseek") if model.startswith(name)), None)
                limit = db.execute("SELECT cap FROM provider_limits WHERE provider=?", (provider,)).fetchone()
                spent = db.execute("SELECT COALESCE(SUM(charged),0) FROM calls WHERE model LIKE ?", ((provider or "") + "%",)).fetchone()[0]
                if limit is None or spent + maximum_micro_rmb > limit[0]:
                    raise BudgetUnavailable("provider budget would be exceeded")
            db.execute("INSERT INTO calls VALUES (?, ?, ?, ?, 'reserved', NULL, NULL)", (identifier, model, maximum_micro_rmb, maximum_micro_rmb))
        return identifier

    def settle(self, identifier: str, micro_rmb: int, prompt: int, completion: int) -> None:
        if any(type(value) is not int or value < 0 for value in (micro_rmb, prompt, completion)):
            raise BudgetUnavailable("invalid billing usage")
        exceeded = False
        with closing(sqlite3.connect(self.path, timeout=3)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT reserved, status FROM calls WHERE id=?", (identifier,)).fetchone()
            if row is None or row[1] != "reserved":
                raise BudgetUnavailable("unknown or already settled reservation")
            exceeded = micro_rmb > row[0]
            if exceeded:
                db.execute("UPDATE policy SET blocked=1 WHERE id=1")
            db.execute("UPDATE calls SET charged=?, status=?, prompt_tokens=?, completion_tokens=? WHERE id=?", (micro_rmb, "over_reservation" if exceeded else "settled", prompt, completion, identifier))
        if exceeded:
            raise BudgetUnavailable("provider exceeded reserved bound; further calls blocked")

    def summary(self) -> dict:
        with closing(sqlite3.connect(self.path)) as db:
            cap, blocked = db.execute("SELECT cap, blocked FROM policy WHERE id=1").fetchone()
            rows = db.execute("SELECT model, status, COUNT(*), SUM(charged), SUM(prompt_tokens), SUM(completion_tokens) FROM calls GROUP BY model, status ORDER BY model,status").fetchall()
            limits = dict(db.execute("SELECT provider, cap FROM provider_limits")) if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='provider_limits'").fetchone() else {}
        return {"cap_rmb": cap/1e6, "provider_caps_rmb": {name: value/1e6 for name, value in limits.items()}, "blocked": bool(blocked), "conservative_cost_rmb": sum(row[3] for row in rows)/1e6, "groups": [{"model": row[0], "status": row[1], "calls": row[2], "cost_bound_rmb": row[3]/1e6, "prompt_tokens": row[4], "completion_tokens": row[5]} for row in rows], "note": "Peak uncached rates; credits/discounts not subtracted. Reserved unknown calls may still be billed."}
