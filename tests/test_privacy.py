from __future__ import annotations

import json

import pytest

from schemasnap.models import SourceDescriptor
from schemasnap.privacy import PrivacyClass, classify_column, query_fingerprint
from schemasnap.profile import profile_dataframe


@pytest.mark.parametrize(
    "name",
    [
        "email",
        "customer_email_address",
        "full_name",
        "user_id",
        "account_uid",
        "phone_number",
        "shipping_address",
        "ssn",
        "api_token",
        "password_hash",
    ],
)
def test_sensitive_column_names_fail_closed(name: str) -> None:
    assert classify_column(name) is PrivacyClass.SENSITIVE


def test_query_fingerprint_never_returns_sql() -> None:
    query = "SELECT * FROM customers WHERE email = 'private@example.test'"
    fingerprint = query_fingerprint(query)

    assert len(fingerprint) == 64
    assert query not in fingerprint
    assert fingerprint == query_fingerprint(query)


def test_sensitive_values_never_enter_snapshot_json() -> None:
    import polars as pl

    frame = pl.DataFrame(
        {
            "user_id": ["usr-secret-1", "usr-secret-2"],
            "email": ["alice@example.test", "bob@example.test"],
            "full_name": ["Alice Private", "Bob Private"],
            "segment": ["enterprise-secret-label", "consumer-secret-label"],
        }
    )
    snapshot = profile_dataframe(frame, SourceDescriptor(kind="csv", label="customers.csv"))
    encoded = snapshot.to_json()
    payload = json.loads(encoded)

    for secret in (
        "usr-secret-1",
        "usr-secret-2",
        "alice@example.test",
        "bob@example.test",
        "Alice Private",
        "Bob Private",
        "enterprise-secret-label",
        "consumer-secret-label",
    ):
        assert secret not in encoded

    by_name = {column["name"]: column for column in payload["columns"]}
    assert by_name["email"]["privacy"] == "sensitive"
    assert "numeric" not in by_name["user_id"]
    assert "category" not in by_name["email"]
    assert by_name["segment"]["category"]["cardinality"] == 2
