from __future__ import annotations

import io
import subprocess
import tempfile
from pathlib import Path
from typing import BinaryIO

from .orchestrator import analyze_text
from .utils import extract_domains, extract_emails, extract_institution_candidates, extract_phone_numbers

try:
    import speech_recognition as sr
except ImportError:  # pragma: no cover
    sr = None

try:
    import pytesseract
except ImportError:  # pragma: no cover
    pytesseract = None

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None


def _bytes(data: bytes | BinaryIO) -> bytes:
    return data if isinstance(data, bytes) else data.read()


def transcribe_audio(data: bytes | BinaryIO, suffix: str = ".wav") -> str:
    audio_bytes = _bytes(data)
    if sr is None:
        raise RuntimeError("Audio transcription requires SpeechRecognition. Install it or configure a transcription provider.")
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / f"input{suffix.lower()}"
        wav = Path(tmp) / "input.wav"
        source.write_bytes(audio_bytes)
        if source.suffix == ".mp3":
            subprocess.run(["ffmpeg", "-y", "-i", str(source), str(wav)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            wav = source
        recognizer = sr.Recognizer()
        with sr.AudioFile(str(wav)) as audio_file:
            audio = recognizer.record(audio_file)
        return recognizer.recognize_google(audio)


def extract_image_text(data: bytes | BinaryIO) -> str:
    if Image is None or pytesseract is None:
        raise RuntimeError("Image OCR requires Pillow and pytesseract.")
    image = Image.open(io.BytesIO(_bytes(data)))
    return pytesseract.image_to_string(image)


def extract_pdf_text(data: bytes | BinaryIO) -> str:
    pdf_bytes = _bytes(data)
    text = ""
    if PdfReader is not None:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if text.strip():
        return text
    raise RuntimeError("PDF text extraction found no embedded text. Provide OCR-capable PDF processing in production image.")


def extracted_identity_summary(text: str) -> dict:
    return {
        "domains": extract_domains(text),
        "phone_numbers": extract_phone_numbers(text),
        "emails": extract_emails(text),
        "institutions": extract_institution_candidates(text, ["State Bank of India", "SBI", "Central Bureau of Investigation", "CBI", "Police", "Cyber Police"]),
    }


def analyze_audio(data: bytes | BinaryIO, suffix: str = ".wav", case_id: str | None = None) -> dict:
    transcript = transcribe_audio(data, suffix=suffix)
    return analyze_text(transcript, case_id=case_id)


def analyze_image(data: bytes | BinaryIO, case_id: str | None = None) -> dict:
    text = extract_image_text(data)
    return analyze_text(text, case_id=case_id)


def analyze_pdf(data: bytes | BinaryIO, case_id: str | None = None) -> dict:
    text = extract_pdf_text(data)
    return analyze_text(text, case_id=case_id)
