import unittest
from unittest.mock import patch, MagicMock
from backend.cli.app import chat, edit, doctor


class TestCliAppFunctions(unittest.TestCase):
    @patch('backend.cli.app.get_config')
    def test_chat(self, mock_get_config):
        # Mocking the get_config function to return a dummy config
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config
        # Calling the chat function with mocked arguments
        result = chat(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        # Assert that the function executed without errors
        self.assertIsNone(result)

    @patch('backend.cli.app.get_config')
    def test_edit(self, mock_get_config):
        # Similar mocking for the edit function
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config
        result = edit(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        self.assertIsNone(result)

    @patch('backend.cli.app.get_config')
    def test_doctor(self, mock_get_config):
        # Similar mocking for the doctor function
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config
        result = doctor(MagicMock())
        self.assertIsNone(result)