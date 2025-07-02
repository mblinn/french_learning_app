import os
import sys
import unittest
import io
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from airtable_data_access import (
    fetch_flashcards,
    fetch_spaced_rep_frequencies,
    log_practice,
    log_forget,
    log_airtable_error,
    build_url,
    AIRTABLE_URL,
    SPACED_REP_URL,
    Flashcard
)


class FetchFlashcardsTests(unittest.TestCase):
    @patch("airtable_data_access.get_random_frequencies")
    @patch("airtable_data_access.fetch_spaced_rep_frequencies")
    @patch("airtable_data_access.requests.get")
    def test_query_parameters(self, mock_get, mock_spaced, mock_rand):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"records": []}
        mock_get.return_value = mock_resp

        mock_spaced.return_value = [
            (101, 1),
            (102, 1),
            (103, 1),
            (104, 1),
            (105, 1),
        ]
        mock_rand.return_value = list(range(10, 40))

        fetch_flashcards("TOKEN")

        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], AIRTABLE_URL)
        self.assertEqual(kwargs["headers"], {"Authorization": "Bearer TOKEN"})
        spaced_map = dict(mock_spaced.return_value)
        unique_randoms = [i for i in mock_rand.return_value if i not in spaced_map]
        selected = list(spaced_map.keys()) + unique_randoms[: 25 - len(spaced_map)]
        formula = "OR(" + ",".join([f'{{Frequency}} = "{i}"' for i in selected]) + ")"
        expected_params = {
            "maxRecords": 25,
            "filterByFormula": formula,
            "sort[0][field]": "Frequency",
            "sort[0][direction]": "asc",
        }
        self.assertEqual(kwargs["params"], expected_params)

    @patch(
        "airtable_data_access.get_random_frequencies", return_value=list(range(1, 26))
    )
    @patch("airtable_data_access.fetch_spaced_rep_frequencies", return_value=[])
    @patch("airtable_data_access.requests.get")
    def test_parses_flashcards(self, mock_get, mock_spaced, mock_rand):
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

        cards = fetch_flashcards("TOKEN")

        self.assertEqual(
            cards,
            [
                Flashcard(front="Bonjour", back="Hello", frequency="2", level="1"),
                Flashcard(front="", back="Empty", frequency="5", level="1"),
            ],
        )

    @patch(
        "airtable_data_access.get_random_frequencies", return_value=list(range(1, 26))
    )
    @patch("airtable_data_access.fetch_spaced_rep_frequencies", return_value=[])
    @patch("airtable_data_access.requests.get")
    def test_handles_translation_dict(self, mock_get, mock_spaced, mock_rand):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "records": [
                {
                    "fields": {
                        "french_word": "Savoir",
                        "english_translation": {
                            "state": "generated",
                            "value": "to know",
                            "isStale": False,
                        },
                        "Frequency": "7",
                    }
                },
            ]
        }
        mock_get.return_value = mock_resp

        cards = fetch_flashcards("TOKEN")

        self.assertEqual(
            cards, [Flashcard(front="Savoir", back="to know", frequency="7", level="1")]
        )

    @patch(
        "airtable_data_access.get_random_frequencies", return_value=list(range(1, 26))
    )
    @patch("airtable_data_access.fetch_spaced_rep_frequencies", return_value=[(2, 3)])
    @patch("airtable_data_access.requests.get")
    def test_assigns_levels(self, mock_get, mock_spaced, mock_rand):
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
                }
            ]
        }
        mock_get.return_value = mock_resp

        cards = fetch_flashcards("TOKEN")

        self.assertEqual(
            cards,
            [Flashcard(front="Bonjour", back="Hello", frequency="2", level="3")],
        )

    @patch("airtable_data_access.requests.post")
    @patch("airtable_data_access.requests.get")
    def test_log_practice_creates_row(self, mock_get, mock_post):
        get_resp = MagicMock()
        get_resp.raise_for_status.return_value = None
        get_resp.json.return_value = {"records": []}
        mock_get.return_value = get_resp

        post_resp = MagicMock()
        post_resp.raise_for_status.return_value = None
        mock_post.return_value = post_resp

        result = log_practice("TOKEN", "3", "2023-01-01")

        self.assertTrue(result)
        mock_get.assert_called_once()
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], SPACED_REP_URL)
        headers = {"Authorization": "Bearer TOKEN", "Content-Type": "application/json"}
        self.assertEqual(kwargs["headers"], headers)
        self.assertEqual(
            kwargs["json"],
            {"fields": {"Date": "2023-01-01", "Frequency": "3", "Level": "1"}},
        )

    @patch("airtable_data_access.requests.patch")
    @patch("airtable_data_access.requests.get")
    def test_log_practice_updates_row(self, mock_get, mock_patch):
        get_resp = MagicMock()
        get_resp.raise_for_status.return_value = None
        get_resp.json.return_value = {
            "records": [{"id": "rec123", "fields": {"Frequency": "3", "Level": 2}}]
        }
        mock_get.return_value = get_resp

        patch_resp = MagicMock()
        patch_resp.raise_for_status.return_value = None
        mock_patch.return_value = patch_resp

        result = log_practice("TOKEN", "3", "2023-01-01")

        self.assertTrue(result)
        mock_get.assert_called_once()
        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        self.assertEqual(args[0], f"{SPACED_REP_URL}/rec123")
        headers = {"Authorization": "Bearer TOKEN", "Content-Type": "application/json"}
        self.assertEqual(kwargs["headers"], headers)
        self.assertEqual(
            kwargs["json"], {"fields": {"Date": "2023-01-01", "Level": "3"}}
        )

    @patch("airtable_data_access.requests.patch")
    @patch("airtable_data_access.requests.get")
    def test_log_practice_caps_level(self, mock_get, mock_patch):
        get_resp = MagicMock()
        get_resp.raise_for_status.return_value = None
        get_resp.json.return_value = {
            "records": [{"id": "rec999", "fields": {"Frequency": "3", "Level": 5}}]
        }
        mock_get.return_value = get_resp

        patch_resp = MagicMock()
        patch_resp.raise_for_status.return_value = None
        mock_patch.return_value = patch_resp

        result = log_practice("TOKEN", "3", "2023-01-01")

        self.assertTrue(result)
        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        self.assertEqual(args[0], f"{SPACED_REP_URL}/rec999")
        self.assertEqual(
            kwargs["json"], {"fields": {"Date": "2023-01-01", "Level": "5"}}
        )

    @patch("airtable_data_access.requests.post")
    @patch("airtable_data_access.requests.get")
    def test_log_forget_creates_row(self, mock_get, mock_post):
        get_resp = MagicMock()
        get_resp.raise_for_status.return_value = None
        get_resp.json.return_value = {"records": []}
        mock_get.return_value = get_resp

        post_resp = MagicMock()
        post_resp.raise_for_status.return_value = None
        mock_post.return_value = post_resp

        result = log_forget("TOKEN", "3", "2023-01-01")

        self.assertTrue(result)
        mock_get.assert_called_once()
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], SPACED_REP_URL)
        headers = {"Authorization": "Bearer TOKEN", "Content-Type": "application/json"}
        self.assertEqual(kwargs["headers"], headers)
        self.assertEqual(
            kwargs["json"],
            {"fields": {"Date": "2023-01-01", "Frequency": "3", "Level": "1"}},
        )

    @patch("airtable_data_access.requests.patch")
    @patch("airtable_data_access.requests.get")
    def test_log_forget_updates_row(self, mock_get, mock_patch):
        get_resp = MagicMock()
        get_resp.raise_for_status.return_value = None
        get_resp.json.return_value = {
            "records": [{"id": "rec123", "fields": {"Frequency": "3", "Level": 3}}]
        }
        mock_get.return_value = get_resp

        patch_resp = MagicMock()
        patch_resp.raise_for_status.return_value = None
        mock_patch.return_value = patch_resp

        result = log_forget("TOKEN", "3", "2023-01-01")

        self.assertTrue(result)
        mock_get.assert_called_once()
        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        self.assertEqual(args[0], f"{SPACED_REP_URL}/rec123")
        headers = {"Authorization": "Bearer TOKEN", "Content-Type": "application/json"}
        self.assertEqual(kwargs["headers"], headers)
        self.assertEqual(
            kwargs["json"], {"fields": {"Date": "2023-01-01", "Level": "2"}}
        )

    @patch("airtable_data_access.requests.patch")
    @patch("airtable_data_access.requests.get")
    def test_log_forget_mins_level(self, mock_get, mock_patch):
        get_resp = MagicMock()
        get_resp.raise_for_status.return_value = None
        get_resp.json.return_value = {
            "records": [{"id": "rec999", "fields": {"Frequency": "3", "Level": 1}}]
        }
        mock_get.return_value = get_resp

        patch_resp = MagicMock()
        patch_resp.raise_for_status.return_value = None
        mock_patch.return_value = patch_resp

        result = log_forget("TOKEN", "3", "2023-01-01")

        self.assertTrue(result)
        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        self.assertEqual(args[0], f"{SPACED_REP_URL}/rec999")
        self.assertEqual(
            kwargs["json"], {"fields": {"Date": "2023-01-01", "Level": "1"}}
        )


class SpacedRepFrequencyTests(unittest.TestCase):
    @patch("airtable_data_access.requests.get")
    def test_fetch_spaced_rep_frequencies(self, mock_get):
        responses = []
        for lvl in range(1, 6):
            resp = MagicMock()
            resp.raise_for_status.return_value = None
            resp.json.return_value = {"records": [{"fields": {"Frequency": str(lvl)}}]}
            responses.append(resp)
        mock_get.side_effect = responses

        freqs = fetch_spaced_rep_frequencies("TOKEN")

        self.assertEqual(mock_get.call_count, 5)
        headers = {"Authorization": "Bearer TOKEN"}
        for i, call in enumerate(mock_get.call_args_list, start=1):
            args, kwargs = call
            self.assertEqual(args[0], SPACED_REP_URL)
            self.assertEqual(kwargs["headers"], headers)
            params = kwargs["params"]
            self.assertEqual(params["maxRecords"], 5)
            self.assertEqual(params["sort[0][field]"], "Date")
            self.assertEqual(params["sort[0][direction]"], "asc")
            self.assertIn(f"{{Level}} = '{i}'", params["filterByFormula"])

        expected = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]
        self.assertEqual(freqs, expected)


class BuildUrlTests(unittest.TestCase):
    def test_build_url_encodes_params(self):
        url = build_url("https://example.com/api", {"a": "1", "b": "x y"})
        self.assertTrue(url.startswith("https://example.com/api?"))
        self.assertIn("a=1", url)
        self.assertIn("b=x+y", url)


class LogAirtableErrorTests(unittest.TestCase):
    def test_log_airtable_error_outputs_url_and_json(self):
        payload = {"a": 1, "b": 2}
        url = "https://example.com/path"
        with patch("traceback.print_exc") as mock_trace, patch(
            "sys.stderr", new_callable=io.StringIO
        ) as fake_err:
            log_airtable_error("Test error", url, payload)
            output = fake_err.getvalue()
        self.assertIn("Test error. URL: https://example.com/path", output)
        self.assertIn('"a": 1', output)
        self.assertIn('"b": 2', output)
        mock_trace.assert_called_once()


if __name__ == "__main__":
    unittest.main()
