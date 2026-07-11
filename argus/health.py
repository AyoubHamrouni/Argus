"""
Argus Health Checks — Verify all services are running.
"""

import sys
import socket
import httpx
from pathlib import Path
from typing import List, Tuple


SERVICES = [
    ("alert-triage", 8100, "/health"),
    ("rag-service", 8300, "/health"),
    ("ml-inference", 8500, "/health"),
    ("wazuh-integration", 8002, "/health"),
    ("feedback-service", 8400, "/health"),
    ("correlation-engine", 8600, "/health"),
    ("response-orchestrator", 8800, "/health"),
    ("rule-generator", 8700, "/health"),
    ("ollama", 11434, "/api/tags"),
    ("chromadb", 8200, "/api/v1/heartbeat"),
    ("redis", 6379, None),
    ("postgres", 5432, None),
]


def _check_port(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if a TCP port is reachable."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (ConnectionRefusedError, OSError, TimeoutError):
        return False


def _check_http(url: str, timeout: float = 3.0) -> Tuple[bool, int]:
    """Check an HTTP endpoint. Returns (ok, status_code)."""
    try:
        r = httpx.get(url, timeout=timeout)
        return (r.status_code < 500, r.status_code)
    except Exception:
        return (False, 0)


def run_health_checks(fmt: str = "table"):
    """Run health checks and print results."""
    if fmt == "json":
        _run_json()
    else:
        _run_table()


def _run_table():
    try:
        from rich.console import Console
        from rich.table import Table
        from rich import box
        HAS_RICH = True
    except ImportError:
        HAS_RICH = False

    results: List[Tuple[str, int, str, str]] = []

    for name, port, path in SERVICES:
        if path is None:
            ok = _check_port("localhost", port)
            status = "UP" if ok else "DOWN"
            detail = "port open" if ok else "port closed"
        else:
            ok, code = _check_http(f"http://localhost:{port}{path}")
            if ok:
                status = "UP"
                detail = f"HTTP {code}"
            elif code > 0:
                status = "DEGRADED"
                detail = f"HTTP {code}"
            else:
                status = "DOWN"
                detail = "unreachable"

        results.append((name, port, status, detail))

    if HAS_RICH:
        console = Console()
        table = Table(title="Argus Health Check", box=box.ROUNDED)
        table.add_column("Service", style="cyan", min_width=22)
        table.add_column("Port", style="dim")
        table.add_column("Status", min_width=12)
        table.add_column("Detail", style="dim")

        up_count = 0
        for name, port, status, detail in results:
            if status == "UP":
                style = "green"
                up_count += 1
            elif status == "DEGRADED":
                style = "yellow"
            else:
                style = "red"
            table.add_row(name, str(port), f"[{style}]{status}[/]", detail)

        console.print(table)
        console.print(f"\n[bold]{up_count}/{len(results)}[/] services healthy")
    else:
        print(f"{'Service':<22} {'Port':<6} {'Status':<12} Detail")
        print("-" * 60)
        up_count = 0
        for name, port, status, detail in results:
            marker = "OK" if status == "UP" else ("!!" if status == "DEGRADED" else "XX")
            if status == "UP":
                up_count += 1
            print(f"{name:<22} {port:<6} {marker} {status:<12} {detail}")
        print(f"\n{up_count}/{len(results)} services healthy")


def _run_json():
    import json

    results = []
    for name, port, path in SERVICES:
        if path is None:
            ok = _check_port("localhost", port)
            results.append({"service": name, "port": port, "healthy": ok, "status": "UP" if ok else "DOWN"})
        else:
            ok, code = _check_http(f"http://localhost:{port}{path}")
            status = "UP" if ok else ("DEGRADED" if code > 0 else "DOWN")
            results.append({"service": name, "port": port, "healthy": ok, "status": status, "http_code": code})

    up = sum(1 for r in results if r["healthy"])
    output = {"total": len(results), "healthy": up, "services": results}
    print(json.dumps(output, indent=2))

    if up < len(results):
        sys.exit(1)
