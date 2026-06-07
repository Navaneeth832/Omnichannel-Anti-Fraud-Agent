from __future__ import annotations

import re
from typing import Iterable, List
from urllib.parse import urlparse


_WHITESPACE_RE = re.compile(r"\s+")
_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"
)
_DOMAIN_RE = re.compile(
    r"(?:(?:https?://)?(?:www\.)?)"
    r"((?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,})(?:/[^\s<>'\"]*)?",
    re.IGNORECASE,
)
_PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{4}(?!\d)"
)


def normalize_text(value: str) -> str:
    return _WHITESPACE_RE.sub(" ", value or "").strip().lower()


def normalize_identity(value: str) -> str:
    normalized = normalize_text(value)
    normalized = re.sub(r"[^a-z0-9]+", "", normalized)
    return normalized


def dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        if not item:
            continue
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def extract_emails(text: str) -> List[str]:
    return dedupe_preserve_order(
        match.group(0)
        for match in re.finditer(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            text or "",
        )
    )


def extract_domains(text: str) -> List[str]:
    domains = []
    raw_text = text or ""
    for match in _DOMAIN_RE.finditer(raw_text):
        domain = match.group(1).lower().rstrip(".,;:!?)\"]}'")
        domains.append(domain)
    for email in extract_emails(raw_text):
        domains.append(email.split("@", 1)[1].lower())
    normalized = []
    for domain in domains:
        try:
            parsed = urlparse(f"https://{domain}")
            host = parsed.hostname or domain
        except ValueError:
            host = domain
        host = host.lower()
        if host.startswith("www."):
            host = host[4:]
        normalized.append(host)
    return dedupe_preserve_order(normalized)


def extract_phone_numbers(text: str) -> List[str]:
    numbers = []
    for match in _PHONE_RE.finditer(text or ""):
        raw = match.group(0)
        digits = re.sub(r"\D", "", raw)
        if len(digits) < 7 or len(digits) > 15:
            continue
        if digits in {"0000000", "00000000", "000000000", "0000000000"}:
            continue
        cleaned = f"+{digits}" if raw.startswith("+") else digits
        numbers.append(cleaned)
    return dedupe_preserve_order(numbers)


def infer_channels(text: str) -> List[str]:
    content = normalize_text(text)
    channels = []
    channel_map = [
        ("whatsapp", ["whatsapp", "wa "]),
        ("sms", ["sms", "text message"]),
        ("phone", ["phone call", "voice call", "dial", "call "]),
        ("email", ["email", "mail", "inbox"]),
        ("video", ["video call", "video arrest", "zoom", "meet"]),
        ("website", ["website", "link", "url", "domain", "site"]),
    ]
    for channel, tokens in channel_map:
        if any(token in content for token in tokens):
            channels.append(channel)
    return dedupe_preserve_order(channels)


def extract_institution_candidates(text: str, aliases: Iterable[str]) -> List[str]:
    content = normalize_text(text)
    candidates = []
    for alias in aliases:
        alias_normalized = normalize_text(alias)
        if not alias_normalized:
            continue
        if alias_normalized in content:
            candidates.append(alias)
    return dedupe_preserve_order(candidates)
