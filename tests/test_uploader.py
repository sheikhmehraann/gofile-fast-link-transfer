"""Unit tests for GoFile Uploader module."""

import pytest
from unittest.mock import MagicMock, patch
from src.gofile_transfer.uploader import GoFileUploader, GoFileResult


def test_get_best_server_fallback():
    uploader = GoFileUploader()
    with patch.object(uploader.session, "get", side_effect=Exception("API Error")):
        server = uploader.get_best_server()
        assert server == "store1"


def test_get_best_server_success():
    uploader = GoFileUploader()
    mock_res = MagicMock()
    mock_res.json.return_value = {
        "status": "ok",
        "data": {
            "servers": [
                {"name": "store5", "zone": "eu"}
            ]
        }
    }
    mock_res.raise_for_status.return_value = None

    with patch.object(uploader.session, "get", return_value=mock_res):
        server = uploader.get_best_server()
        assert server == "store5"
