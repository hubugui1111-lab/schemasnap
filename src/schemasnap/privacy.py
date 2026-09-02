"""Fail-closed column-name privacy classification."""

from __future__ import annotations

import hashlib
import re
from enum import StrEnum


class PrivacyClass(StrEnum):
    STANDARD = "standard"
    SENSITIVE = "sensitive"


_SENSITIVE_PARTS = {
    "address",
    "apikey",
    "credential",
    "customerid",
    "email",
    "firstname",
    "fullname",
    "lastname",
    "name",
    "password",
    "phone",
    "secret",
    "shippingaddress",
    "ssn",
    "token",
    "userid",
    "uid",
}


def _tokens(name: str) -> tuple[set[str], str]:
    normalized = re.sub(r"[^a-z0-9]+", "_", name.casefold()).strip("_")
    parts = {part for part in normalized.split("_") if part}
    compact = normalized.replace("_", "")
    return parts, compact


def classify_column(name: str) -> PrivacyClass:
    """Classify by conservative schema-name heuristics, never by raw values."""

    parts, compact = _tokens(name)
    if parts & _SENSITIVE_PARTS or any(marker in compact for marker in _SENSITIVE_PARTS):
        return PrivacyClass.SENSITIVE
    if "id" in parts or compact.endswith("id"):
        return PrivacyClass.SENSITIVE
    return PrivacyClass.STANDARD


def query_fingerprint(query: str) -> str:
    """Return a stable one-way identifier for SQL without retaining SQL text."""

    return hashlib.sha256(query.encode("utf-8")).hexdigest()
