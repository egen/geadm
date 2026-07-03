"""Filter builders, entry normalization and tail formatting for geadm logs."""

from types import SimpleNamespace

import pytest

from geadm.commands import logs


# ---- filters -----------------------------------------------------------------


def test_connector_filter_uses_encoded_log_name():
    f = logs.connector_filter("proj", None, None, "1h")
    assert 'logName="projects/proj/logs/discoveryengine.googleapis.com%2Fconnector_activity"' in f
    assert "timestamp>=" in f


def test_connector_filter_datastore_and_severity():
    f = logs.connector_filter("proj", "my-ds", "error", "1h")
    assert 'jsonPayload.LogMetadata.name:"my-ds"' in f
    assert "severity>=ERROR" in f


def test_connector_filter_rejects_bad_severity():
    with pytest.raises(ValueError):
        logs.connector_filter("proj", None, "LOUD", "1h")


def test_user_filter_single_user():
    f = logs.user_filter("proj", "a@b.com", "24h")
    assert 'jsonPayload.userIamPrincipal="a@b.com"' in f
    assert "gemini_enterprise_user_activity" in f
    assert "protoPayload" not in f  # platform logs have no protoPayload


@pytest.mark.parametrize("email", [None, "*", "all"])
def test_user_filter_all_users_omits_principal(email):
    f = logs.user_filter("proj", email, "24h")
    assert "userIamPrincipal" not in f


def test_base_clauses_have_no_timestamp():
    assert not any("timestamp" in c for c in logs.user_base_clauses("p", "a@b.com"))
    assert not any(
        "timestamp" in c for c in logs.connector_base_clauses("p", None, "ERROR")
    )


# ---- normalization -------------------------------------------------------------


def _entry(payload, severity="INFO"):
    return SimpleNamespace(
        payload=payload,
        severity=severity,
        log_name="projects/p/logs/x",
        timestamp=None,
        insert_id="abc",
        resource=SimpleNamespace(type="consumed_api", labels={"service": "s"}),
    )


def test_normalize_streamassist_with_parts_prompt_and_reply():
    row = logs._normalize_entry(
        _entry(
            {
                "logMetadata": {"methodName": "StreamAssist", "name": "projects/p/x"},
                "request": {"query": {"parts": [{"text": "hi"}, {"text": "there"}]}},
                "serviceTextReply": "Hello back",
                "userIamPrincipal": "a@b.com",
            }
        )
    )
    assert row["message"] == "StreamAssist: hi there"
    assert row["reply"] == "Hello back"
    assert row["user"] == "a@b.com"


def test_normalize_query_text_shape():
    row = logs._normalize_entry(
        _entry(
            {
                "logMetadata": {"methodName": "StreamAssist"},
                "request": {"query": {"text": "plain prompt"}},
            }
        )
    )
    assert row["message"] == "StreamAssist: plain prompt"


def test_normalize_modelarmor_user_prompt_data():
    row = logs._normalize_entry(
        _entry(
            {
                "logMetadata": {"methodName": "ModelArmorAudit"},
                "request": {"userPromptData": {"text": "bad prompt"}},
            },
            severity="WARNING",
        )
    )
    assert row["message"] == "ModelArmorAudit: bad prompt"


def test_normalize_connector_capital_log_metadata():
    row = logs._normalize_entry(
        _entry({"LogMetadata": {"name": "projects/p/locations/g/collections/c/dataConnector"}})
    )
    assert row["entity_name"].endswith("dataConnector")


def test_normalize_text_payload():
    row = logs._normalize_entry(_entry("plain text line"))
    assert row["message"] == "plain text line"


# ---- tail formatting -----------------------------------------------------------


def test_short_resource_trims_boilerplate():
    assert (
        logs._short_resource(
            "projects/1/locations/global/collections/default_collection/engines/e1/servingConfigs/s"
        )
        == "e1/servingConfigs/s"
    )
    assert logs._short_resource("projects/1/locations/global") is None
    assert (
        logs._short_resource("projects/1/locations/global/collections/mine/dataConnector")
        == "collections/mine/dataConnector"
    )
    assert logs._short_resource(None) is None


def test_snippet_collapses_and_truncates():
    assert logs._snippet("a\nb\n  c", 100) == "a b c"
    long = "word " * 100
    out = logs._snippet(long, 50)
    assert len(out) <= 50 and out.endswith("…")
    assert logs._snippet(None, 10) is None


def test_short_time():
    assert logs._short_time(None) == "--:--:--"
    out = logs._short_time("2026-07-03T16:36:50.829010+00:00")
    assert len(out) == 8 and out.count(":") == 2
