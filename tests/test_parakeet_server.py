from fastapi.testclient import TestClient

from local_stt import parakeet_server


class FakeParakeetModel:
    def transcribe(self, files):
        assert len(files) == 1
        return ["Papa took medicine."]


def test_parakeet_server_transcribes_audio(monkeypatch):
    monkeypatch.setattr(parakeet_server, "load_model", lambda: FakeParakeetModel())
    client = TestClient(parakeet_server.app)

    response = client.post(
        "/transcribe",
        files={"file": ("note.webm", b"audio", "audio/webm")},
    )

    assert response.status_code == 200
    assert response.json() == {"text": "Papa took medicine."}


def test_parakeet_server_rejects_non_audio_upload(monkeypatch):
    monkeypatch.setattr(parakeet_server, "load_model", lambda: FakeParakeetModel())
    client = TestClient(parakeet_server.app)

    response = client.post(
        "/transcribe",
        files={"file": ("note.txt", b"not audio", "text/plain")},
    )

    assert response.status_code == 415


def test_parakeet_server_health_does_not_load_model():
    client = TestClient(parakeet_server.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
