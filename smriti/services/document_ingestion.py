from __future__ import annotations

import base64
import mimetypes
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from smriti.models import MemoryEntry, Persona


SUPPORTED_UPLOAD_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}


@dataclass(frozen=True)
class ExtractedDocument:
    text: str
    source_kind: str
    extraction_method: str


class DocumentIngestionError(ValueError):
    pass


class DocumentExtractor:
    def __init__(self, vision_extractor=None):
        self._vision = vision_extractor

    @property
    def vision_backend(self):
        return self._vision

    def extract(
        self,
        *,
        content: bytes,
        filename: str,
        content_type: str,
    ) -> ExtractedDocument:
        if content_type not in SUPPORTED_UPLOAD_TYPES:
            raise DocumentIngestionError("Upload a PDF or photo: PDF, PNG, JPG, JPEG, or WEBP.")

        if content_type == "application/pdf":
            text = self._extract_pdf_text(content)
            if self._is_useful_text(text):
                return ExtractedDocument(
                    text=text,
                    source_kind="pdf",
                    extraction_method="pypdf",
                )
            if not self._vision:
                raise DocumentIngestionError("This scanned PDF needs vision extraction.")
            image_bytes = self._render_first_pdf_page(content)
            text = self._extract_image_text(image_bytes, "application/png", filename)
            return ExtractedDocument(
                text=text,
                source_kind="scanned_pdf",
                extraction_method="vision",
            )

        if not self._vision:
            raise DocumentIngestionError("Photo extraction needs a vision provider.")
        text = self._extract_image_text(content, content_type, filename)
        return ExtractedDocument(
            text=text,
            source_kind="photo",
            extraction_method="vision",
        )

    def structure(
        self,
        *,
        text: str,
        persona: Persona,
        now: datetime,
        filename: str,
        source_kind: str,
        extraction_method: str,
        structurer,
    ) -> list[MemoryEntry]:
        if not self._is_useful_text(text):
            raise DocumentIngestionError("Couldn't read clearly. Try a closer, brighter photo.")

        structured = structurer.structure(
            self._prompt_text(text, filename, source_kind),
            persona,
            now,
        )
        memories = [
            item if isinstance(item, MemoryEntry) else MemoryEntry.model_validate(item)
            for item in structured
        ]
        memories = memories[:15]
        if not memories:
            memories = [
                MemoryEntry(
                    text=f"Uploaded medical document: {filename}",
                    type="document",
                    persona=persona,
                    occurred_at=now,
                    entities={},
                    raw=text[:2000],
                )
            ]

        if len(structured) > 15:
            memories.append(
                MemoryEntry(
                    text=f"Full report uploaded: {filename}",
                    type="document",
                    persona=persona,
                    occurred_at=now,
                    entities={"card_limit": 15},
                    raw=text[:4000],
                )
            )

        for memory in memories:
            memory.entities = {
                **memory.entities,
                "source_filename": filename,
                "source_kind": source_kind,
                "extraction_method": extraction_method,
                "source_text_excerpt": text[:500],
            }
            memory.raw = memory.raw or text[:2000]
        return memories

    def _extract_image_text(self, content: bytes, content_type: str, filename: str) -> str:
        data_url = _data_url(content, content_type)
        text = self._vision.extract(data_url, filename)
        if text.strip().upper() == "UNREADABLE" or not self._is_useful_text(text):
            raise DocumentIngestionError("Couldn't read clearly. Try a closer, brighter photo.")
        return text

    @staticmethod
    def _extract_pdf_text(content: bytes) -> str:
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf") as temp_pdf:
                temp_pdf.write(content)
                temp_pdf.flush()
                reader = PdfReader(temp_pdf.name)
                pages = [(page.extract_text() or "").strip() for page in reader.pages[:8]]
            return "\n\n".join(page for page in pages if page).strip()
        except (PdfReadError, OSError, ValueError):
            raise DocumentIngestionError("Couldn't read this PDF. Try a clearer PDF or photo.")

    @staticmethod
    def _render_first_pdf_page(content: bytes) -> bytes:
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "upload.pdf"
            output_prefix = Path(temp_dir) / "page"
            pdf_path.write_bytes(content)
            try:
                subprocess.run(
                    [
                        "pdftoppm",
                        "-png",
                        "-f",
                        "1",
                        "-singlefile",
                        str(pdf_path),
                        str(output_prefix),
                    ],
                    check=True,
                    capture_output=True,
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                raise DocumentIngestionError("Couldn't read this scanned PDF.")
            image_path = output_prefix.with_suffix(".png")
            if not image_path.exists():
                raise DocumentIngestionError("Couldn't read this scanned PDF.")
            return image_path.read_bytes()

    @staticmethod
    def _is_useful_text(text: str) -> bool:
        compact = " ".join(text.split())
        if len(compact) < 20:
            return False
        words = [word for word in compact.split() if any(ch.isalpha() for ch in word)]
        return len(words) >= 3

    @staticmethod
    def _prompt_text(text: str, filename: str, source_kind: str) -> str:
        return (
            "Medical document upload. Split into separate memory cards: one per medicine "
            "with dose/frequency, one per lab value, one per doctor instruction, and one "
            "per follow-up date. Use type medication, vital, visit, document, or remark. "
            "Do not interpret results. Cap important facts; preserve exact names.\n"
            f"Filename: {filename}\n"
            f"Source kind: {source_kind}\n"
            f"Extracted text:\n{text}"
        )


def _data_url(content: bytes, content_type: str) -> str:
    media_type = content_type or mimetypes.guess_type("upload")[0] or "application/octet-stream"
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{media_type};base64,{encoded}"
