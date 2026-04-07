import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
import types

if "moss" not in sys.modules:
    moss = types.ModuleType("moss")

    class _Dummy:
        def __init__(self, *args, **kwargs):
            pass

    moss.DocumentInfo = _Dummy
    moss.MossClient = _Dummy
    moss.MutationOptions = _Dummy
    moss.QueryOptions = _Dummy
    sys.modules["moss"] = moss

if "langgraph.graph" not in sys.modules:
    graph_module = types.ModuleType("langgraph.graph")

    class _CompiledGraph:
        def __init__(self, nodes):
            self._nodes = nodes

        def invoke(self, state):
            for name in ("detect_use_case", "search_candidates", "score_candidates", "summarize"):
                state.update(self._nodes[name](state))
            return state

    class _StateGraph:
        def __init__(self, *_args, **_kwargs):
            self._nodes = {}

        def add_node(self, name, fn, **_kwargs):
            self._nodes[name] = fn
            return self

        def add_edge(self, *_args, **_kwargs):
            return self

        def compile(self):
            return _CompiledGraph(self._nodes)

    graph_module.StateGraph = _StateGraph
    graph_module.START = "START"
    graph_module.END = "END"
    langgraph_pkg = types.ModuleType("langgraph")
    sys.modules["langgraph"] = langgraph_pkg
    sys.modules["langgraph.graph"] = graph_module


class AnalyzeAndAuditionModeTests(unittest.TestCase):
    def test_analyze_returns_structured_options(self):
        from audition.analyze import analyze_brief

        voices = [
            {
                "id": "openai:alloy",
                "name": "Alloy",
                "provider": "openai",
                "description": "Clear and balanced support voice.",
                "use_cases": ["customer_support"],
                "traits": {"warmth": 0.7, "clarity": 0.9, "authority": 0.6, "confidence": 0.7, "friendliness": 0.8, "energy": 0.5},
                "style_tags": ["conversational"],
                "personality_tags": ["friendly"],
                "effective_cost_per_min_usd": 0.015,
                "effective_latency_tier": "fast",
                "search_score": 0.8,
            },
            {
                "id": "rime:mist:bayou",
                "name": "Bayou",
                "provider": "rime",
                "description": "Warm and reassuring voice for patient conversations.",
                "use_cases": ["healthcare", "customer_support"],
                "traits": {"warmth": 0.9, "clarity": 0.7, "authority": 0.7, "confidence": 0.6, "friendliness": 0.9, "energy": 0.4},
                "style_tags": ["soothing"],
                "personality_tags": ["reassuring"],
                "effective_cost_per_min_usd": 0.03,
                "effective_latency_tier": "fastest",
                "search_score": 0.9,
            },
        ]

        with patch("audition.analyze.select_candidates", return_value=voices):
            result = analyze_brief("need a support voice for patients", num_candidates=2)

        self.assertEqual(result["use_case"], "healthcare")
        self.assertIn("best_overall", result)
        self.assertIn("best_budget", result)
        self.assertEqual(len(result["shortlist"]), 2)

    def test_human_audition_stores_clips_in_project_state_dir(self):
        from audition.audition import run_human_audition

        voices = [
            {
                "id": "openai:alloy",
                "name": "Alloy",
                "provider": "openai",
                "provider_voice_id": "alloy",
                "provider_model": "gpt-4o-mini-tts",
                "gender": "neutral",
                "description": "Clear and balanced support voice.",
                "search_score": 0.8,
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / ".voice-audition"
            with patch("audition.audition.select_candidates", return_value=voices), \
                 patch("audition.audition._generate_script_audio") as generate_mock, \
                 patch.dict("os.environ", {"VOICE_AUDITION_STATE_DIR": str(state_dir)}):
                def _fake_generate(voice, text, script_name, out_dir, client):
                    path = out_dir / f"{script_name}.mp3"
                    path.write_bytes(b"audio")
                    return path, None

                generate_mock.side_effect = _fake_generate
                result = run_human_audition("support voice", num_candidates=1)

        self.assertIn("audition_id", result)
        self.assertEqual(result["mode"], "human")
        self.assertEqual(len(result["clips"]), 3)
        self.assertTrue(all(clip["file_path"].endswith(".mp3") for clip in result["clips"]))
        self.assertIn(".voice-audition/clips/", result["clips"][0]["file_path"])
