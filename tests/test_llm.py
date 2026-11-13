import unittest
from core.llm import DEFAULT_MODEL_ID, format_groq_error, get_model_name


class GroqConfigurationTests(unittest.TestCase):
    def test_default_model_is_central_gpt_oss(self):
        self.assertEqual(DEFAULT_MODEL_ID, "openai/gpt-oss-120b")
        self.assertEqual(get_model_name(), "openai/gpt-oss-120b")

    def test_authentication_error_is_actionable(self):
        error = type("GroqError", (Exception,), {"status_code": 401})("unauthorized")
        self.assertIn("API key", format_groq_error(error))

    def test_model_not_found_is_actionable(self):
        error = type("GroqError", (Exception,), {"status_code": 404})("not found")
        self.assertIn("could not find or access model", format_groq_error(error))

    def test_rate_limit_is_actionable(self):
        error = type("GroqError", (Exception,), {"status_code": 429})("rate limit")
        self.assertIn("rate limit", format_groq_error(error).lower())

    def test_network_error_is_actionable(self):
        error = type("APIConnectionError", (Exception,), {})("connection error")
        self.assertIn("internet connection", format_groq_error(error))


if __name__ == "__main__":
    unittest.main()
