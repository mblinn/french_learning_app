import unittest
from unittest.mock import patch, MagicMock

from scripts.translate_words import (
    parse_frequency_range,
    fetch_words,
    translate_word,
    AIRTABLE_URL,
)


class ParseFrequencyRangeTests(unittest.TestCase):
    def test_valid_range(self):
        self.assertEqual(parse_frequency_range("1-10"), (1, 10))

    def test_invalid_format(self):
        with self.assertRaises(ValueError):
            parse_frequency_range("1to10")

    def test_start_greater_than_end(self):
        with self.assertRaises(ValueError):
            parse_frequency_range("10-1")


class FetchWordsTests(unittest.TestCase):
    @patch("scripts.translate_words.requests.get")
    def test_fetch_words(self, mock_get):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = {
            "records": [
                {"fields": {"french_word": "bonjour"}},
                {"fields": {"french_word": "chat"}},
            ]
        }
        mock_get.return_value = resp

        result = fetch_words("TOKEN", 1, 2)

        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], AIRTABLE_URL)
        headers = {"Authorization": "Bearer TOKEN"}
        self.assertEqual(kwargs["headers"], headers)
        params = kwargs["params"]
        self.assertIn("filterByFormula", params)
        self.assertEqual(result, ["bonjour", "chat"])


class TranslateWordTests(unittest.TestCase):
    @patch("scripts.translate_words.openai.ChatCompletion.create")
    def test_translate_word(self, mock_create):
        mock_create.return_value = {
            "choices": [{"message": {"content": "bonjour"}}]
        }
        result = translate_word("OPENAI", "hello")

        mock_create.assert_called_once()
        self.assertEqual(result, "bonjour")


if __name__ == "__main__":
    unittest.main()
