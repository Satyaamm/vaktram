"""PII detection + redaction for transcripts and summaries.

Default redactor uses regex (fast, no extra deps). Enterprise orgs that flip
the `dlp` feature on get the Presidio-backed redactor with broader entity
coverage (PERSON, LOCATION, MEDICAL_LICENSE, etc.).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Order matters: more specific first.
_DEFAULT_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("EMAIL", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("PHONE", re.compile(r"\+?\d[\d\s\-().]{7,}\d")),
    ("CREDIT_CARD", re.compile(r"\b(?:\d[ -]*?){13,16}\b")),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("IP", re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")),
]


@dataclass
class RedactionResult:
    text: str
    entities: list[tuple[str, str]]  # (type, original)


def redact(text: str, *, use_presidio: bool = False) -> RedactionResult:
    if use_presidio:
        try:
            return _redact_presidio(text)
        except Exception as e:  # noqa: BLE001
            logger.warning("Presidio failed, falling back to regex DLP: %s", e)
    return _redact_regex(text)


def _redact_regex(text: str) -> RedactionResult:
    entities: list[tuple[str, str]] = []
    out = text
    for label, pat in _DEFAULT_PATTERNS:
        for m in pat.finditer(out):
            entities.append((label, m.group(0)))
        out = pat.sub(f"[{label}]", out)
    return RedactionResult(out, entities)


def _redact_presidio(text: str) -> RedactionResult:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine

    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()
    results = analyzer.analyze(text=text, language="en")
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    entities = [(r.entity_type, text[r.start : r.end]) for r in results]
    return RedactionResult(anonymized.text, entities)
