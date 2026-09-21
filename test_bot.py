import unittest
from bot import load_faq, find_answer, FAQ_FILE


class TestFAQBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.faq = load_faq(FAQ_FILE)

    def test_faq_count(self):
        self.assertEqual(len(self.faq), 5, "В FAQ должно быть ровно 5 вопросов-ответов")

    def test_time_question(self):
        answer = find_answer("Во сколько начало репетиции?", self.faq)
        self.assertIn("10:00", answer)
        self.assertIn("18:00", answer)

    def test_team_question(self):
        answer = find_answer("Сколько человек может быть в команде?", self.faq)
        self.assertIn("от 2 до 5 человек", answer)

    def test_track_question(self):
        answer = find_answer("Какой трек и тема хакатона?", self.faq)
        self.assertIn("чат-бота", answer)

    def test_submission_question(self):
        answer = find_answer("Куда сдавать проект и какой дедлайн?", self.faq)
        self.assertIn("17:30", answer)
        self.assertIn("git", answer.lower())

    def test_prizes_question(self):
        answer = find_answer("Какие призы получат победители?", self.faq)
        self.assertIn("мерч", answer.lower())

    def test_unknown_question(self):
        answer = find_answer("Какая погода в Париже?", self.faq)
        self.assertIn("не знаю", answer.lower())

    def test_empty_query(self):
        answer = find_answer("", self.faq)
        self.assertIn("введите вопрос", answer.lower())


if __name__ == "__main__":
    unittest.main()

