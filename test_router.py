import unittest

from router import HeuristicRouter


class TestHeuristicRouter(unittest.TestCase):
    def setUp(self):
        self.r = HeuristicRouter()

    def test_stable_knowledge_goes_direct(self):
        self.assertEqual(self.r.route("What is the capital of France?").route, "direct")

    def test_fresh_query_searches(self):
        self.assertEqual(
            self.r.route("What is the latest pricing for OpenAI API models?").route,
            "search_and_answer",
        )

    def test_comparison_goes_deep(self):
        self.assertEqual(
            self.r.route("Compare Fireworks AI vs Baseten vs Together AI").route,
            "deep_research",
        )

    def test_fresh_comparison_goes_deep(self):
        self.assertEqual(
            self.r.route("Latest benchmarks: GPT-5 vs Gemini?").route,
            "deep_research",
        )


if __name__ == "__main__":
    unittest.main()
