import unittest
from unittest.mock import patch
from core.router import detect_intent

class RouterTests(unittest.TestCase):
    def test_routes(self):
        self.assertEqual(detect_intent("Summarize this paper"),"summarise")
        self.assertEqual(detect_intent("Explain the main algorithm"),"concepts")
        self.assertEqual(detect_intent("Make a presentation"),"presentation")
        self.assertEqual(detect_intent("Give me viva practice questions"),"viva_questions")
        self.assertEqual(detect_intent("Evaluate my answer"),"viva_evaluation")
        with patch("core.router.invoke_lcel", return_value="question_answer"):
            self.assertEqual(detect_intent("What did the experiment find?"),"question_answer")
