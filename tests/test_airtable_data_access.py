import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from airtable_data_access import (
    fetch_flashcards,
    log_practice,
    AIRTABLE_URL,
    SPACED_REP_URL,
)
from flashcards import Flashcard


class FetchFlashcardsTests(unittest.TestCase):
    @patch('airtable_data_access.get_random_frequencies')
    @patch('airtable_data_access.requests.get')
    def test_query_parameters(self, mock_get, mock_rand):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"records": []}
        mock_get.return_value = mock_resp

        mock_rand.return_value = list(range(10, 30))

        fetch_flashcards('TOKEN')

        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], AIRTABLE_URL)
        self.assertEqual(kwargs['headers'], {'Authorization': 'Bearer TOKEN'})
        formula = "OR(" + ",".join([f"{{Frequency}} = \"{i}\"" for i in mock_rand.return_value]) + ")"
        expected_params = {
            'maxRecords': 20,
            'filterByFormula': formula,
            'sort[0][field]': 'Frequency',
            'sort[0][direction]': 'asc',
        }
        self.assertEqual(kwargs['params'], expected_params)

    @patch('airtable_data_access.get_random_frequencies', return_value=list(range(1, 21)))
    @patch('airtable_data_access.requests.get')
    def test_parses_flashcards(self, mock_get, mock_rand):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "records": [
                {"fields": {"french_word": "Bonjour", "english_translation": "Hello", "Frequency": "2"}},
                {"fields": {"french_word": "", "english_translation": "Empty", "Frequency": "5"}},
            ]
        }
        mock_get.return_value = mock_resp

        cards = fetch_flashcards('TOKEN')

        self.assertEqual(
            cards,
            [
                Flashcard(front="Bonjour", back="Hello", frequency="2"),
                Flashcard(front="", back="Empty", frequency="5"),
            ],
        )

    @patch('airtable_data_access.requests.post')
    def test_log_practice(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        result = log_practice('TOKEN', '3', '2023-01-01')

        self.assertTrue(result)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], SPACED_REP_URL)
        headers = {
            'Authorization': 'Bearer TOKEN',
            'Content-Type': 'application/json'
        }
        self.assertEqual(kwargs['headers'], headers)
        self.assertEqual(
            kwargs['json'],
            {'fields': {'Date': '2023-01-01', 'Frequency': '3'}}
        )


if __name__ == '__main__':
    unittest.main()
