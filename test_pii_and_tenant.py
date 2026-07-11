#!/usr/bin/env python3
"""
Verification test: PII Redaction & Multi-Tenant Isolation
AI-Augmented SOC — Enterprise Refactoring

Tests:
1. PII redaction strips emails, hashes, and URL passwords from alert fields
2. organization_id is carried through the full ingestion pipeline
3. query_alerts enforces tenant isolation (one tenant can't see another's data)

Usage:
    python3 test_pii_and_tenant.py [--triage-url http://localhost:8000] [--feedback-url http://localhost:8001]

Requirements:
    pip install httpx pytest
"""

import argparse
import sys
import json
import time
import uuid
import httpx

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
INFO = "\033[94m[INFO]\033[0m"

results = []


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    msg = f"{status} {name}"
    if detail:
        msg += f"\n       {detail}"
    print(msg)
    results.append((name, condition))
    return condition


# ---------------------------------------------------------------------------
# 1. Unit test: pii_redaction module (no network required)
# ---------------------------------------------------------------------------

def test_pii_redaction_unit():
    print("\n=== 1. Unit: pii_redaction module ===")
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "services/alert-triage"))

    try:
        from pii_redaction import redact_text, redact_alert_pii
    except ImportError as e:
        check("pii_redaction import", False, str(e))
        return

    # Email
    out = redact_text("Login from user admin@corp.com failed")
    check("EMAIL redacted", "[REDACTED_EMAIL]" in out, repr(out))

    # MD5 hash
    out = redact_text("Hash: aabbccddeeff00112233445566778899")
    check("MD5 hash redacted", "[REDACTED_HASH]" in out, repr(out))

    # URL password
    out = redact_text("Connected to ftp://admin:supersecret@192.168.1.10")
    check("URL password redacted", "[REDACTED_PASSWORD]" in out, repr(out))

    # SSN
    out = redact_text("Employee SSN: 123-45-6789 appeared in log")
    check("SSN redacted", "[REDACTED_SSN]" in out, repr(out))

    # Dict redaction
    alert_dict = {
        "alert_id": "test-001",
        "raw_log": "user=bob@example.com hash=aabbccddeeff00112233445566778899",
        "rule_description": "Auth failure",
    }
    redacted = redact_alert_pii(alert_dict)
    check("raw_log field redacted in dict",
          "[REDACTED_EMAIL]" in redacted["raw_log"] and "[REDACTED_HASH]" in redacted["raw_log"],
          repr(redacted["raw_log"]))
    check("rule_description unchanged (no PII)", redacted["rule_description"] == "Auth failure")
    check("alert_id unchanged", redacted["alert_id"] == "test-001")


# ---------------------------------------------------------------------------
# 2. Integration tests against live services
# ---------------------------------------------------------------------------

def test_triage_async(triage_url: str, api_key: str = ""):
    print("\n=== 2. Integration: alert-triage /analyze (async 202) ===")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    alert_id = f"test-{uuid.uuid4().hex[:8]}"

    payload = {
        "alert_id": alert_id,
        "rule_description": "SSH brute force from admin@evil.com hash=aabbccddeeff00112233445566778899",
        "rule_level": 10,
        "source_ip": "10.0.0.1",
        "organization_id": "tenant-A",
        "raw_log": "Failed password for user: root@evil.com from 10.0.0.1 port 22 via ssh",
    }

    try:
        r = httpx.post(f"{triage_url}/analyze", json=payload, headers=headers, timeout=10)
        check("POST /analyze returns 202", r.status_code == 202,
              f"Got {r.status_code}: {r.text[:200]}")
        if r.status_code != 202:
            return None

        body = r.json()
        check("Response contains job_id", "job_id" in body, str(body))
        check("Response status is 'queued'", body.get("status") == "queued", str(body))
        return body.get("job_id"), alert_id

    except httpx.ConnectError:
        check("POST /analyze (connection)", False, f"Could not connect to {triage_url}")
        return None


def test_job_status(triage_url: str, job_id: str, api_key: str = "", wait_secs: int = 30):
    print(f"\n=== 3. Integration: GET /api/v1/triage/status/{job_id} ===")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    for attempt in range(wait_secs):
        try:
            r = httpx.get(f"{triage_url}/api/v1/triage/status/{job_id}", headers=headers, timeout=10)
            if r.status_code == 200:
                body = r.json()
                status = body.get("status")
                if status in ("completed", "failed"):
                    check("Job completed via status endpoint", status == "completed",
                          f"status={status}, error={body.get('error')}")
                    if status == "completed":
                        check("Result contains triage data", body.get("result") is not None)
                    return body
                print(f"  {INFO} Job status: {status} (waiting...)", end="\r")
                time.sleep(1)
            else:
                check("GET /api/v1/triage/status returns 200", False,
                      f"Got {r.status_code}: {r.text[:200]}")
                return None
        except httpx.ConnectError:
            check("GET status (connection)", False, f"Could not connect to {triage_url}")
            return None

    check("Job completed within timeout", False, f"Timed out after {wait_secs}s")
    return None


def test_multitenant_isolation(feedback_url: str, api_key: str = ""):
    print("\n=== 4. Integration: Multi-tenant organization_id isolation ===")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    tenant_a_id = f"test-tenant-A-{uuid.uuid4().hex[:6]}"
    tenant_b_id = f"test-tenant-B-{uuid.uuid4().hex[:6]}"

    # Store an alert for tenant A
    alert_a = {
        "alert_id": tenant_a_id,
        "timestamp": "2025-01-01T00:00:00",
        "organization_id": "tenant-ALPHA",
        "ai_severity": "high",
        "rule_description": "Tenant A alert",
        "rule_level": 10,
    }
    alert_b = {
        "alert_id": tenant_b_id,
        "timestamp": "2025-01-01T00:00:00",
        "organization_id": "tenant-BETA",
        "ai_severity": "low",
        "rule_description": "Tenant B alert",
        "rule_level": 3,
    }

    try:
        ra = httpx.post(f"{feedback_url}/alerts", json=alert_a, headers=headers, timeout=10)
        rb = httpx.post(f"{feedback_url}/alerts", json=alert_b, headers=headers, timeout=10)
        check("Store tenant-A alert", ra.status_code == 200, f"Got {ra.status_code}: {ra.text[:100]}")
        check("Store tenant-B alert", rb.status_code == 200, f"Got {rb.status_code}: {rb.text[:100]}")

        # Query with tenant-A filter — should NOT see tenant-B's alert
        r = httpx.get(f"{feedback_url}/alerts",
                      params={"organization_id": "tenant-ALPHA"}, headers=headers, timeout=10)
        check("GET /alerts with org filter returns 200", r.status_code == 200, f"{r.status_code}")
        if r.status_code == 200:
            body = r.json()
            ids_returned = [a["alert_id"] for a in body.get("alerts", [])]
            check("tenant-A alert visible under its org filter", tenant_a_id in ids_returned, str(ids_returned))
            check("tenant-B alert NOT visible under tenant-A filter",
                  tenant_b_id not in ids_returned, str(ids_returned))

        # Query with tenant-B filter — should NOT see tenant-A's alert
        r2 = httpx.get(f"{feedback_url}/alerts",
                       params={"organization_id": "tenant-BETA"}, headers=headers, timeout=10)
        if r2.status_code == 200:
            body2 = r2.json()
            ids2 = [a["alert_id"] for a in body2.get("alerts", [])]
            check("tenant-A alert NOT visible under tenant-B filter",
                  tenant_a_id not in ids2, str(ids2))

    except httpx.ConnectError:
        check("Feedback service connection", False, f"Could not connect to {feedback_url}")


def test_roi_metrics(feedback_url: str, api_key: str = ""):
    print("\n=== 5. Integration: GET /roi/metrics ===")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    try:
        r = httpx.get(f"{feedback_url}/roi/metrics", headers=headers, timeout=10)
        check("GET /roi/metrics returns 200", r.status_code == 200, f"Got {r.status_code}: {r.text[:200]}")
        if r.status_code == 200:
            body = r.json()
            check("Has total_alerts_processed", "total_alerts_processed" in body, str(body.keys()))
            check("Has accuracy_rate key", "accuracy_rate" in body)
            check("Has alerts_by_severity", "alerts_by_severity" in body)
            print(f"  {INFO} ROI data: {json.dumps(body, indent=2)}")
    except httpx.ConnectError:
        check("GET /roi/metrics (connection)", False, f"Could not connect to {feedback_url}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI_SOC verification tests")
    parser.add_argument("--triage-url", default="http://localhost:8000", help="Alert-triage service URL")
    parser.add_argument("--feedback-url", default="http://localhost:8001", help="Feedback service URL")
    parser.add_argument("--api-key", default="", help="Bearer API key (if auth enabled)")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests (no network)")
    parser.add_argument("--wait-secs", type=int, default=30, help="Seconds to wait for async job")
    args = parser.parse_args()

    # Always run unit tests
    test_pii_redaction_unit()

    if not args.unit_only:
        job = test_triage_async(args.triage_url, args.api_key)
        if job:
            job_id, alert_id = job
            test_job_status(args.triage_url, job_id, args.api_key, args.wait_secs)

        test_multitenant_isolation(args.feedback_url, args.api_key)
        test_roi_metrics(args.feedback_url, args.api_key)

    # Summary
    print("\n" + "=" * 50)
    passed = sum(1 for _, ok in results if ok)
    failed = sum(1 for _, ok in results if not ok)
    print(f"Results: {passed} passed, {failed} failed out of {len(results)} checks")
    if failed:
        print(f"\n{FAIL} Failed checks:")
        for name, ok in results:
            if not ok:
                print(f"  - {name}")
        sys.exit(1)
    else:
        print(f"{PASS} All checks passed!")
        sys.exit(0)
