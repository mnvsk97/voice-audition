import unittest
from unittest.mock import MagicMock, patch

from enrichment.sync import sync_azure, sync_google


def _mock_response(payload):
    resp = MagicMock()
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    return resp


class SyncProviderTests(unittest.TestCase):
    def test_sync_azure_skips_without_credentials(self):
        with patch.dict("os.environ", {}, clear=True), patch("enrichment.sync.httpx.get") as get_mock:
            voices = sync_azure()

        self.assertEqual(voices, [])
        get_mock.assert_not_called()

    def test_sync_azure_maps_voices(self):
        payload = [
            {
                "Name": "Microsoft Server Speech Text to Speech Voice (en-US, JennyNeural)",
                "DisplayName": "Jenny",
                "LocalName": "Jenny",
                "ShortName": "en-US-JennyNeural",
                "Gender": "Female",
                "Locale": "en-US",
                "LocaleName": "English (United States)",
                "StyleList": ["assistant", "cheerful"],
                "RolePlayList": ["Narrator", "CustomerService"],
                "SampleRateHertz": "24000",
                "VoiceType": "Neural",
                "Status": "GA",
                "WordsPerMinute": "152",
            }
        ]
        with patch.dict(
            "os.environ",
            {"AZURE_SPEECH_KEY": "key", "AZURE_SPEECH_REGION": "eastus"},
            clear=True,
        ), patch("enrichment.sync.httpx.get", return_value=_mock_response(payload)) as get_mock:
            voices = sync_azure()

        self.assertEqual(len(voices), 1)
        voice = voices[0]
        self.assertEqual(voice["provider"], "azure")
        self.assertEqual(voice["provider_voice_id"], "en-US-JennyNeural")
        self.assertEqual(voice["name"], "Jenny")
        self.assertEqual(voice["gender"], "female")
        self.assertEqual(voice["language"], "en")
        self.assertEqual(voice["provider_model"], "Neural")
        self.assertIn("conversational", voice["style_tags"])
        self.assertIn("upbeat", voice["style_tags"])
        self.assertIn("storytelling", voice["use_cases"])
        self.assertIn("customer_support", voice["use_cases"])
        get_mock.assert_called_once()

    def test_sync_google_skips_without_credentials(self):
        with patch.dict("os.environ", {}, clear=True), patch("enrichment.sync.httpx.get") as get_mock:
            voices = sync_google()

        self.assertEqual(voices, [])
        get_mock.assert_not_called()

    def test_sync_google_maps_voices(self):
        payload = {
            "voices": [
                {
                    "name": "en-US-Neural2-A",
                    "ssmlGender": "FEMALE",
                    "languageCodes": ["en-US", "es-ES"],
                    "naturalSampleRateHertz": 24000,
                }
            ]
        }
        with patch.dict(
            "os.environ",
            {"GOOGLE_ACCESS_TOKEN": "token"},
            clear=True,
        ), patch("enrichment.sync.httpx.get", return_value=_mock_response(payload)) as get_mock:
            voices = sync_google()

        self.assertEqual(len(voices), 1)
        voice = voices[0]
        self.assertEqual(voice["provider"], "google")
        self.assertEqual(voice["provider_voice_id"], "en-US-Neural2-A")
        self.assertEqual(voice["name"], "en-US-Neural2-A")
        self.assertEqual(voice["gender"], "female")
        self.assertEqual(voice["language"], "en-US")
        self.assertEqual(voice["provider_model"], "Neural2")
        self.assertEqual(voice["additional_languages"], ["es-ES"])
        self.assertEqual(voice["provider_metadata"]["natural_sample_rate_hertz"], 24000)
        get_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
