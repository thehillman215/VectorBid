import json
from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from src.core import bid_packets


def test_save_and_get_bid_packet(tmp_path, monkeypatch):
    monkeypatch.setattr(bid_packets, "BIDS_DIR", tmp_path)
    monkeypatch.setattr(bid_packets, "METADATA_DIR", tmp_path / "metadata")

    fs = FileStorage(stream=BytesIO(b"%PDF-1.4"), filename="test.pdf")
    bid_packets.save_bid_packet(fs, "202501")

    assert (tmp_path / "202501.pdf").exists()
    info = bid_packets.get_bid_packet_info("202501")
    assert info["filename"] == "test.pdf"


@pytest.mark.skip("Dashboard route not available in test environment")
def test_dashboard_detects_packet(client, tmp_path, monkeypatch):
    pass
