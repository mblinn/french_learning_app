import unittest
from unittest.mock import patch, MagicMock

from scripts.fetch_airtable_schema import fetch_schema, BASE_ID


class FetchSchemaTests(unittest.TestCase):
    @patch("scripts.fetch_airtable_schema.requests.get")
    def test_fetch_schema_calls_api(self, mock_get):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = {"tables": []}
        mock_get.return_value = resp

        result = fetch_schema("TOKEN")

        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        expected_url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"
        self.assertEqual(args[0], expected_url)
        self.assertEqual(kwargs["headers"], {"Authorization": "Bearer TOKEN"})
        self.assertEqual(result, {"tables": []})


if __name__ == "__main__":
    unittest.main()
