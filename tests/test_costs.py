import unittest
import types
import sys

from click.testing import CliRunner

from audition.costs import calculate_voice_costs as shared_calculate_voice_costs
from cli.main import main


class _FakeFastMCP:
    def __init__(self, *args, **kwargs):
        self._tools = {}

    def tool(self, fn):
        self._tools[fn.__name__] = fn
        return fn

    def run(self):
        return None


sys.modules.setdefault("fastmcp", types.SimpleNamespace(FastMCP=_FakeFastMCP))

from mcp.server import calculate_voice_costs


class CostSurfaceTests(unittest.TestCase):
    def test_shared_cost_calculator_returns_comparison(self):
        result = shared_calculate_voice_costs(100000)

        self.assertEqual(result["minutes_per_month"], 100000)
        self.assertEqual(result["cheapest_api"]["provider"], "deepgram")
        self.assertEqual(result["cheapest_self_hosted"]["model"], "piper")
        self.assertEqual(result["cheapest_api"]["monthly_cost_usd"], 1000.0)
        self.assertEqual(result["cheapest_self_hosted"]["monthly_cost_usd"], 5.0)

    def test_cli_costs_command_uses_shared_calculator(self):
        runner = CliRunner()

        result = runner.invoke(main, ["costs", "100000"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Deepgram", result.output)
        self.assertIn("Piper", result.output)
        self.assertIn("$1,000.00/mo", result.output)
        self.assertIn("$5.00/mo", result.output)

    def test_mcp_cost_tool_matches_shared_calculator(self):
        self.assertEqual(calculate_voice_costs(100000), shared_calculate_voice_costs(100000))


if __name__ == "__main__":
    unittest.main()
