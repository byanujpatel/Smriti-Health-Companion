from __future__ import annotations

import os
import tempfile
from functools import lru_cache

from fastapi import FastAPI, File, HTTPException, UploadFile, status


DEFAULT_MODEL = "nvidia/parakeet-tdt-0.6b-v2"
app = FastAPI(title="Smriti Local Parakeet STT", version="0.1.0")


@lru_cache(maxsize=1)
def load_model():
    try:
        import nemo.collections.asr as nemo_asr
    except ImportError as error:
        raise RuntimeError(
            "NeMo ASR is not installed. Install it with: "
            "uv pip install 'nemo_toolkit[asr]'"
        ) from error

    model_name = os.getenv("PARAKEET_STT_MODEL", DEFAULT_MODEL)
    return nemo_asr.models.ASRModel.from_pretrained(model_name)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "model": os.getenv("PARAKEET_STT_MODEL", DEFAULT_MODEL),
    }


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)) -> dict[str, str]:
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload an audio file.",
        )

    suffix = _suffix(file.filename)
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix) as temp_audio:
            temp_audio.write(await file.read())
            temp_audio.flush()
            result = load_model().transcribe([temp_audio.name])[0]
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    return {"text": _text_from_result(result)}


def _suffix(filename: str | None) -> str:
    if not filename or "." not in filename:
        return ".webm"
    extension = filename.rsplit(".", 1)[-1].lower()
    if not extension.isalnum():
        return ".webm"
    return f".{extension}"


def _text_from_result(result) -> str:
    if isinstance(result, str):
        return result.strip()
    text = getattr(result, "text", None)
    if text:
        return str(text).strip()
    return str(result).strip()
