from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from solution.constraint_semantics import excluded_term, upper_budget, contradicts_exclusion
from solution.contracts import Candidate, PreferenceSlot
from solution.field_evidence import FieldEvidence, refine_by_dominance
from solution.ranker import rank_candidates
from solution.state import SessionState


class RankingTest(unittest.TestCase):
    def setUp(self):
        self.state = SessionState.create("fixture", {})

    def test_negative_material_not_a_positive_keyword(self):
        self.state.preferences["material"] = PreferenceSlot("material",("not cotton",),1)
        pool = [Candidate("C",0,1,"cotton shirt",40), Candidate("W",0,1,"wool shirt",40)]
        self.assertEqual(rank_candidates(pool,self.state,2,policy="baseline")[0].parent_asin,"C")
        self.assertEqual(rank_candidates(pool,self.state,2,policy="constraints")[0].parent_asin,"W")

    def test_upper_budget_and_target_budget_are_distinct(self):
        pool = [Candidate("CHEAP",0,1,"shirt",40), Candidate("NEAR",0,1,"shirt",95)]
        for value in ("under 100", "below 100", "up to 100"):
            self.state.preferences["budget"] = PreferenceSlot("budget",(value,),1)
            self.assertEqual(rank_candidates(pool,self.state,2,policy="constraints")[0].parent_asin,"CHEAP")
        self.state.preferences["budget"] = PreferenceSlot("budget",("around $100",),1)
        self.assertEqual(rank_candidates(pool,self.state,2,policy="constraints")[0].parent_asin,"NEAR")

    def test_narrow_negation_preserves_compound_ambiguity(self):
        self.assertEqual(excluded_term("without cotton"),"cotton")
        for value in ("not only cotton", "no preference", "not cotton or wool", "without compromising comfort"):
            self.assertIsNone(excluded_term(value))
        self.assertFalse(contradicts_exclusion("not cotton; wool", "cotton"))
        self.assertFalse(contradicts_exclusion("cotton-free wool", "cotton"))
        self.assertIsNone(upper_budget(("around $100",)))

    def test_missing_material_is_unknown_not_exclusion(self):
        self.state.preferences["material"] = PreferenceSlot("material",("not cotton",),1)
        pool = [Candidate("UNKNOWN",0,1,"shirt",None),Candidate("COTTON",0,1,"cotton shirt",40)]
        result = rank_candidates(pool,self.state,2,policy="constraints")
        self.assertEqual(len(result),2)
        self.assertEqual(result[0].parent_asin,"UNKNOWN")

    def test_explicit_negative_message_reaches_ranking(self):
        self.state.apply_user_message("What I need is: not cotton", 1, flexible=True)
        pool = [Candidate("C",0,1,"cotton shirt",40), Candidate("W",0,1,"wool shirt",40)]
        self.assertEqual(self.state.preferences["material"].values,("not cotton",))
        self.assertEqual(rank_candidates(pool,self.state,2,policy="constraints")[0].parent_asin,"W")

    def test_explicit_upper_budget_reaches_ranking(self):
        self.state.apply_user_message("What I need is: under 100", 1, flexible=True)
        pool = [Candidate("CHEAP",0,1,"shirt",40), Candidate("NEAR",0,1,"shirt",95)]
        self.assertEqual(self.state.preferences["budget"].values,("under 100",))
        self.assertEqual(rank_candidates(pool,self.state,2,policy="constraints")[0].parent_asin,"CHEAP")

    def test_field_evidence_beats_description_only_match(self):
        self.state.preferences["material"] = PreferenceSlot("material",("wool",),1)
        pool = [Candidate("DESC",0,1,"shirt wool",40),Candidate("FIELD",0,1,"shirt wool",40)]
        fields = {"DESC":"shirt","FIELD":"wool shirt"}
        for policy in ("field_bonus","field_groups","field_top10"):
            self.assertEqual(rank_candidates(pool,self.state,2,policy=policy,primary_fields=fields)[0].parent_asin,"FIELD")

    def test_top10_policy_preserves_membership_and_tail(self):
        self.state.preferences["material"] = PreferenceSlot("material",("wool",),1)
        pool = [Candidate(str(i),i,1,"shirt wool",40) for i in range(20)]
        base = rank_candidates(pool,self.state,20,policy="constraints")
        result = rank_candidates(pool,self.state,20,policy="field_top10",primary_fields={str(i):"wool" if i>=7 else "shirt" for i in range(20)})
        self.assertEqual({c.parent_asin for c in base[:10]},{c.parent_asin for c in result[:10]})
        self.assertEqual(base[10:],result[10:])

    def test_ordinary_positive_constraints_keep_baseline_exact(self):
        self.state.preferences["material"] = PreferenceSlot("material",("cotton",),1)
        pool = [Candidate(str(i),i,1,text,price) for i,(text,price) in enumerate([("cotton shirt",40),("blue shirt",95)])]
        self.assertEqual(rank_candidates(pool,self.state,2,policy="baseline"),rank_candidates(pool,self.state,2,policy="constraints"))

    def test_dominance_moves_only_strict_supersets(self):
        self.state.preferences["feature"] = PreferenceSlot("feature",("waterproof","lightweight"),1)
        pool=[Candidate(str(i),i,1,"shoe",40) for i in range(12)]
        fields={"0":"waterproof","1":"waterproof lightweight","2":"lightweight"}
        result=refine_by_dominance(pool,self.state,fields)
        self.assertEqual([c.parent_asin for c in result[:3]],["1","0","2"])
        self.assertEqual({c.parent_asin for c in result[:10]},{c.parent_asin for c in pool[:10]})
        self.assertEqual(result[10:],pool[10:])

    def test_dominance_keeps_partial_matches_and_incomparability(self):
        self.state.preferences={"feature":PreferenceSlot("feature",("waterproof","lightweight"),1),"material":PreferenceSlot("material",("wool",),1)}
        pool=[Candidate("A",0,1,"shoe",40),Candidate("B",1,1,"shoe",40)]
        # B has a complete material group; A has a partial feature group.
        # Group counts would favor B, but their evidence is incomparable.
        self.assertEqual(refine_by_dominance(pool,self.state,{"A":"waterproof","B":"wool"}),pool)
        self.assertEqual(refine_by_dominance(pool,self.state,{}),pool)


class FieldStorageTest(unittest.TestCase):
    def test_fields_reuse_existing_sqlite_and_cache_clears(self):
        from solution.retrieval.index import FTS5CatalogIndex
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"catalog.jsonl"
            products=[{"parent_asin":str(i),"title":"shirt","features":["wool"],"description":["not primary"],"categories":[]} for i in range(270)]
            path.write_text("".join(json.dumps(p)+"\n" for p in products),encoding="utf-8",newline="\n")
            index=FTS5CatalogIndex(path)
            try:
                fields=FieldEvidence(index.connection)
                result=fields.get([str(i) for i in range(270)])
                self.assertEqual(len(result),270)
                self.assertLessEqual(len(fields.cache),256)
                self.assertIn("wool",result["1"])
                self.assertNotIn("not primary",result["1"])
                self.assertIs(fields.connection,index.connection)
                fields.close()
                self.assertFalse(fields.cache)
                self.assertFalse(fields.rowids)
            finally:
                index.close()


class DefaultIntegrationTest(unittest.TestCase):
    def test_default_uses_constraint_fix_without_field_index_or_network(self):
        from starter.agent import Agent
        from tests.core.test_agent import CATALOG
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"catalog.jsonl"
            path.write_text("".join(json.dumps(p)+"\n" for p in CATALOG),encoding="utf-8",newline="\n")
            environment={"INTENTCOMPASS_AGENT_MODE":"integrated","INTENTCOMPASS_RETRIEVAL":"baseline","INTENTCOMPASS_SEMANTIC":"off","INTENTCOMPASS_LLM_ALLOW_NETWORK":"0"}
            with patch.dict(os.environ,environment), patch("solution.chat_reranker.chat_post") as network:
                os.environ.pop("INTENTCOMPASS_OFFLINE_RANKING",None)
                agent=Agent(path)
                try:
                    self.assertEqual(agent._core._adaptive.offline_ranking,"constraints")
                    self.assertIsNone(agent._core._adaptive.field_evidence)
                    agent.reset("one",{})
                    with patch("solution.adaptive.rank_candidates",wraps=rank_candidates) as ranking:
                        agent.respond("one","I'm looking for shoes.",1,10)
                        self.assertEqual(ranking.call_args.kwargs["policy"],"constraints")
                    network.assert_not_called()
                finally:
                    agent.close()

    def test_constraint_candidate_preserves_no_match_fallback_and_reset(self):
        from starter.agent import Agent
        from tests.core.test_agent import CATALOG
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"catalog.jsonl"
            path.write_text("".join(json.dumps(p)+"\n" for p in CATALOG),encoding="utf-8",newline="\n")
            environment={"INTENTCOMPASS_AGENT_MODE":"integrated","INTENTCOMPASS_RETRIEVAL":"baseline","INTENTCOMPASS_SEMANTIC":"off","INTENTCOMPASS_LLM_ALLOW_NETWORK":"0","INTENTCOMPASS_OFFLINE_RANKING":"constraints"}
            with patch.dict(os.environ,environment):
                agent=Agent(path)
                try:
                    outputs=[]
                    for _ in range(2):
                        agent.reset("one",{})
                        outputs.append(agent.respond("one","zzzxxyyqqq",1,10))
                        self.assertTrue(agent._core._adaptive.sessions["one"].last_trace["retrieval"]["fallback_used"])
                    self.assertEqual(outputs[0],outputs[1])
                    self.assertEqual([p["parent_asin"] for p in outputs[0]["recommendations"]],agent._core._retriever.index.fallback_ids[:10])
                finally:
                    agent.close()


if __name__ == "__main__":
    unittest.main()
