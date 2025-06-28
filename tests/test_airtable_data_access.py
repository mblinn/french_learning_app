import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from airtable_data_access import fetch_flashcards, AIRTABLE_URL
from flashcards import Flashcard


class FetchFlashcardsTests(unittest.TestCase):
    @patch('airtable_data_access.requests.get')
    def test_query_parameters(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"records": []}
        mock_get.return_value = mock_resp

        fetch_flashcards('TOKEN')

        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], AIRTABLE_URL)
        self.assertEqual(kwargs['headers'], {'Authorization': 'Bearer TOKEN'})
        formula = "OR(" + ",".join([f"{{Frequency}} = \"{i}\"" for i in range(1, 21)]) + ")"
        expected_params = {
            'maxRecords': 20,
            'filterByFormula': formula,
            'sort[0][field]': 'Frequency',
            'sort[0][direction]': 'asc',
        }
        self.assertEqual(kwargs['params'], expected_params)

    @patch('airtable_data_access.requests.get')
    def test_parses_flashcards(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "records": [
                {"fields": {"french_word": "Bonjour", "english_word": "Hello"}},
                {"fields": {"french_word": "", "english_word": "Empty"}},
            ]
        }
        mock_get.return_value = mock_resp

        cards = fetch_flashcards('TOKEN')

        self.assertEqual(cards, [Flashcard(front="Bonjour", back="Hello"), Flashcard(front="", back="Empty")])


if __name__ == '__main__':
    unittest.main()
