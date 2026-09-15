import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_tmp_dir = tempfile.mkdtemp(prefix="agrisentinel_test_")
os.environ["AGRISENTINEL_DATA_DIR"] = _tmp_dir
os.environ["AGRISENTINEL_DATABASE_URL"] = f"sqlite:///{Path(_tmp_dir, 'test.db').as_posix()}"
os.environ["AGRISENTINEL_ALLOW_GENERIC_MODEL"] = "false"  # keep tests offline/fast

from fastapi.testclient import TestClient  # noqa: E402

from app.database import init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    init_db()
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def field(client):
    resp = client.post(
        "/api/fields",
        json={
            "name": "Test Field",
            "crop_type": "corn",
            "width_m": 10,
            "length_m": 10,
            "row_spacing_m": 0.5,
            "configuration": {"rover_start": {"x": 0, "y": 0}},
        },
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def sample_image_bytes():
    import cv2
    import numpy as np

    img = np.zeros((120, 160, 3), dtype=np.uint8)
    img[:, :] = (40, 80, 120)
    cv2.circle(img, (80, 60), 20, (30, 160, 90), -1)
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return buf.tobytes()
