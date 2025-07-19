import unittest
import json
from unittest.mock import patch, MagicMock

from scripts.translate_words import (
    parse_frequency_range,
    fetch_french_words,
    translate_word,
    generate_image,
    upload_image_to_airtable,
    update_word_record,
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
                {"id": "rec1", "fields": {"french_word": "bonjour"}},
                {"id": "rec2", "fields": {"french_word": "chat"}},
            ]
        }
        mock_get.return_value = resp

        result = fetch_french_words("TOKEN", 1, 2)

        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], AIRTABLE_URL)
        headers = {"Authorization": "Bearer TOKEN"}
        self.assertEqual(kwargs["headers"], headers)
        params = kwargs["params"]
        self.assertIn("filterByFormula", params)
        self.assertEqual(result, [("rec1", "bonjour"), ("rec2", "chat")])


class TranslateWordTests(unittest.TestCase):
    @patch("scripts.translate_words.openai.OpenAI")
    def test_translate_word(self, mock_openai):
        # Mock the client and its chat.completions.create method
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_completion = MagicMock()
        response_json = {
            "english_word": "hello",
            "french_word": "bonjour",
            "sentence_one": "bonjour le monde",
            "sentence_two": "bonjour les amis",
            "part_of_speech": "noun",
            "gender": "N/A",
        }
        mock_completion.choices = [
            MagicMock(message=MagicMock(content=json.dumps(response_json)))
        ]
        mock_client.chat.completions.create.return_value = mock_completion

        result = translate_word("OPENAI", "hello")

        mock_openai.assert_called_once_with(api_key="OPENAI")
        mock_client.chat.completions.create.assert_called_once()
        self.assertEqual(result, response_json)


class GenerateImageTests(unittest.TestCase):
    @patch("scripts.translate_words.openai.OpenAI")
    @patch("scripts.translate_words.requests.get")
    def test_generate_image(self, mock_get, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        completion = MagicMock()
        completion.choices = [MagicMock(message=MagicMock(content="prompt"))]
        mock_client.chat.completions.create.return_value = completion

        mock_client.images.generate.return_value = MagicMock(
            data=[MagicMock(url="http://example.com/img.png")]
        )

        img_resp = MagicMock()
        img_resp.raise_for_status.return_value = None
        img_resp.content = b"imagebytes"
        mock_get.return_value = img_resp

        with patch("builtins.open", new_callable=unittest.mock.mock_open()) as m_open:
            path = generate_image("OPENAI", "cat")

        mock_get.assert_called_once_with("http://example.com/img.png")
        mock_openai.assert_any_call(api_key="OPENAI")
        mock_client.chat.completions.create.assert_called_once()
        mock_client.images.generate.assert_called_once()
        m_open.assert_called_once()
        self.assertTrue(path.endswith("cat.png"))


class UploadFunctionsTests(unittest.TestCase):
    @patch("scripts.translate_words.requests.post")
    @patch("scripts.translate_words.Image.open")
    def test_upload_image_to_airtable(self, mock_open_image, mock_post):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = {"id": "att123"}
        mock_post.return_value = resp

        mock_img = MagicMock()
        mock_open_image.return_value.__enter__.return_value = mock_img

        att_id = upload_image_to_airtable("TOKEN", "/tmp/img.png")

        mock_post.assert_called_once()
        mock_open_image.assert_called_once_with("/tmp/img.png")
        mock_img.resize.assert_called_once_with((150, 150))
        self.assertEqual(att_id, "att123")

    @patch("scripts.translate_words.requests.patch")
    def test_update_word_record(self, mock_patch):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        mock_patch.return_value = resp

        data = {
            "english_word": "cat",
            "sentence_one": "le chat dort",
            "sentence_two": "j'aime le chat",
            "gender": "masculine",
            "part_of_speech": "noun",
        }

        update_word_record("TOKEN", "rec1", data, "att1")

        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        self.assertEqual(args[0], f"{AIRTABLE_URL}/rec1")
        payload = kwargs["json"]
        self.assertEqual(
            payload,
            {
                "fields": {
                    "english_word": "cat",
                    "example_1": "le chat dort",
                    "example_2": "j'aime le chat",
                    "gender": "masculine",
                    "part_of_speech": "noun",
                    "image": [{"id": "att1"}],
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
