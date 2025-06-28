import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from airtable_data_access import (
    fetch_flashcards,
    log_practice,
    fetch_levels,
    update_level,
    AIRTABLE_URL,
    SPACED_REP_URL,
)
from flashcards import Flashcard


class FetchFlashcardsTests(unittest.TestCase):
    @patch('airtable_data_access.fetch_levels', return_value={})
    @patch('airtable_data_access.get_random_frequencies')
    @patch('airtable_data_access.requests.get')
    def test_query_parameters(self, mock_get, mock_rand, mock_levels):
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

    @patch('airtable_data_access.fetch_levels', return_value={'2': 1, '5': 1})
    @patch('airtable_data_access.get_random_frequencies', return_value=list(range(1, 21)))
    @patch('airtable_data_access.requests.get')
    def test_parses_flashcards(self, mock_get, mock_rand, mock_levels):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "records": [
                {
                    "fields": {
                        "french_word": "Bonjour",
                        "english_translation": {"value": "Hello"},
                        "Frequency": "2",
                    }
                },
                {
                    "fields": {
                        "french_word": "",
                        "english_translation": {"value": "Empty"},
                        "Frequency": "5",
                    }
                },
            ]
        }
        mock_get.return_value = mock_resp

        cards = fetch_flashcards('TOKEN')

        self.assertEqual(
            cards,
            [
                Flashcard(front="Bonjour", back="Hello", frequency="2", level=1),
                Flashcard(front="", back="Empty", frequency="5", level=1),
            ],
        )

    @patch('airtable_data_access.fetch_levels', return_value={'7': 1})
    @patch('airtable_data_access.get_random_frequencies', return_value=list(range(1, 21)))
    @patch('airtable_data_access.requests.get')
    def test_handles_translation_dict(self, mock_get, mock_rand, mock_levels):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "records": [
                {
                    "fields": {
                        "french_word": "Savoir",
                        "english_translation": {"state": "generated", "value": "to know", "isStale": False},
                        "Frequency": "7",
                    }
                },
            ]
        }
        mock_get.return_value = mock_resp

        cards = fetch_flashcards('TOKEN')

        self.assertEqual(cards, [Flashcard(front="Savoir", back="to know", frequency="7", level=1)])

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


class LevelsTests(unittest.TestCase):
    @patch('airtable_data_access.requests.get')
    def test_fetch_levels(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            'records': [
                {'fields': {'Frequency': '1', 'level': 3}, 'id': 'rec1'},
                {'fields': {'Frequency': '2'}, 'id': 'rec2'},
            ]
        }
        mock_get.return_value = mock_resp

        result = fetch_levels('TOKEN', ['1', '2', '3'])

        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], SPACED_REP_URL)
        formula = "OR(" + ",".join([f"{{Frequency}} = '{i}'" for i in ['1', '2', '3']]) + ")"
        self.assertEqual(kwargs['params'], {'filterByFormula': formula})
        self.assertEqual(kwargs['headers'], {'Authorization': 'Bearer TOKEN'})
        self.assertEqual(result, {'1': 3, '2': 1})

    @patch('airtable_data_access.requests.patch')
    @patch('airtable_data_access.requests.get')
    def test_update_level_increment(self, mock_get, mock_patch):
        get_resp = MagicMock()
        get_resp.raise_for_status.return_value = None
        get_resp.json.return_value = {
            'records': [{'id': 'rec1', 'fields': {'level': 2}}]
        }
        mock_get.return_value = get_resp

        patch_resp = MagicMock()
        patch_resp.raise_for_status.return_value = None
        mock_patch.return_value = patch_resp

        new_level = update_level('TOKEN', '10', 1)

        mock_get.assert_called_once()
        mock_patch.assert_called_once()
        patch_args, patch_kwargs = mock_patch.call_args
        self.assertEqual(patch_args[0], f"{SPACED_REP_URL}/rec1")
        self.assertEqual(patch_kwargs['json'], {'fields': {'level': 3}})
        self.assertEqual(new_level, 3)

    @patch('airtable_data_access.requests.patch')
    @patch('airtable_data_access.requests.get')
    def test_update_level_caps(self, mock_get, mock_patch):
        get_resp = MagicMock()
        get_resp.raise_for_status.return_value = None
        get_resp.json.return_value = {
            'records': [{'id': 'rec1', 'fields': {'level': 5}}]
        }
        mock_get.return_value = get_resp

        new_level = update_level('TOKEN', '10', 1)

        mock_patch.assert_not_called()
        self.assertEqual(new_level, 5)


if __name__ == '__main__':
    unittest.main()
