import json

from app.export.storage import _compute_hash, write_artifact
from app.models import BidLayerArtifact, Filter, Layer


def _sample_artifact():
    return BidLayerArtifact(
        airline="UAL",
        format="PBS2",
        month="2024-01",
        layers=[
            Layer(
                n=1,
                filters=[Filter(type="PairingId", op="IN", values=["P1"])],
                prefer="YES",
            )
        ],
        lint={"errors": [], "warnings": []},
        export_hash="WRONGHASH",
    )


def test_write_artifact_recomputes_hash(tmp_path):
    artifact = _sample_artifact()
    path = write_artifact(artifact, tmp_path)

    # Exported file should have recomputed hash and matching filename
    data = json.loads(path.read_text())
    expected_hash = _compute_hash(data)
    assert data["export_hash"] == expected_hash
    assert path.name == f"{expected_hash}.json"
