"""
Argus Demo — Show the AI pipeline in action.

Usage:
    argus demo           # Synthetic demo, no Docker needed
    argus demo --live    # Against running services
"""

import json
import time
import random
from typing import List, Dict, Any
from datetime import datetime, timedelta


SYNTHETIC_ALERTS = [
    {
        "alert_id": "WZ-2025-001",
        "timestamp": None,  # filled at runtime
        "source_ip": "192.168.1.105",
        "destination_ip": "10.0.0.22",
        "destination_port": 22,
        "rule_id": "100001",
        "rule_level": 12,
        "rule_description": "sshd: Multiple failed authentication attempts",
        "full_log": "Oct 15 03:14:22 webserver sshd[4821]: Failed password for root from 192.168.1.105 port 38842 ssh2",
        "agent_name": "web-server-01",
        "protocol": "TCP",
        "mitre_tactic": "Credential Access",
        "mitre_technique": "T1110.001",
    },
    {
        "alert_id": "WZ-2025-002",
        "timestamp": None,
        "source_ip": "10.0.0.45",
        "destination_ip": "10.0.0.0/24",
        "destination_port": 0,
        "rule_id": "100012",
        "rule_level": 10,
        "rule_description": "Netflow: Possible port scan detected from internal host",
        "full_log": "Oct 15 03:15:01 sensor netflow: src=10.0.0.45 dst_port_range=1-65535 proto=TCP count=1247",
        "agent_name": "network-sensor",
        "protocol": "TCP",
        "mitre_tactic": "Discovery",
        "mitre_technique": "T1046",
    },
    {
        "alert_id": "WZ-2025-003",
        "timestamp": None,
        "source_ip": "203.0.113.50",
        "destination_ip": "10.0.0.15",
        "destination_port": 443,
        "rule_id": "100045",
        "rule_level": 13,
        "rule_description": "Possible C2 beacon to known malicious IP (threat intel match)",
        "full_log": "Oct 15 03:16:45 suricata: [1:2024897:3] ET MALWARE Known C2 traffic detected",
        "agent_name": "ids-sensor",
        "protocol": "HTTPS",
        "mitre_tactic": "Command and Control",
        "mitre_technique": "T1071.001",
    },
    {
        "alert_id": "WZ-2025-004",
        "timestamp": None,
        "source_ip": "10.0.0.15",
        "destination_ip": "10.0.0.30",
        "destination_port": 445,
        "rule_id": "100078",
        "rule_level": 11,
        "rule_description": "Lateral movement: SMB execution detected between internal hosts",
        "full_log": "Oct 15 03:17:30 sysmon: Process Create — psexec launched via SMB on 10.0.0.30",
        "agent_name": "dc-01",
        "protocol": "SMB",
        "mitre_tactic": "Lateral Movement",
        "mitre_technique": "T1021.002",
    },
    {
        "alert_id": "WZ-2025-005",
        "timestamp": None,
        "source_ip": "10.0.0.22",
        "destination_ip": "198.51.100.77",
        "destination_port": 22,
        "rule_id": "100099",
        "rule_level": 14,
        "rule_description": "Data exfiltration: Large outbound SSH transfer detected",
        "full_log": "Oct 15 03:18:15 netflow: src=10.0.0.22 dst=198.51.100.77 proto=TCP dst_port=22 bytes=2.3GB duration=1847s",
        "agent_name": "web-server-01",
        "protocol": "SSH",
        "mitre_tactic": "Exfiltration",
        "mitre_technique": "T1048.002",
    },
]

MOCK_ML_RESPONSES = [
    {"prediction": "ATTACK", "confidence": 0.98, "model_used": "random_forest",
     "probabilities": {"BENIGN": 0.02, "ATTACK": 0.98}},
    {"prediction": "ATTACK", "confidence": 0.87, "model_used": "random_forest",
     "probabilities": {"BENIGN": 0.13, "ATTACK": 0.87}},
    {"prediction": "ATTACK", "confidence": 0.96, "model_used": "xgboost",
     "probabilities": {"BENIGN": 0.04, "ATTACK": 0.96}},
    {"prediction": "ATTACK", "confidence": 0.91, "model_used": "random_forest",
     "probabilities": {"BENIGN": 0.09, "ATTACK": 0.91}},
    {"prediction": "ATTACK", "confidence": 0.99, "model_used": "xgboost",
     "probabilities": {"BENIGN": 0.01, "ATTACK": 0.99}},
]

MOCK_TRIAGE_RESPONSES = [
    {"severity": "critical", "confidence": 0.95, "category": "brute_force",
     "summary": "Automated SSH brute force attack targeting root account. 47 failed attempts in 3 minutes from single source. High likelihood of credential stuffing or dictionary attack.",
     "true_positive": True, "ioc_count": 1,
     "recommended_actions": ["Block source IP at firewall", "Audit SSH key inventory", "Enable fail2ban"]},
    {"severity": "high", "confidence": 0.88, "category": "reconnaissance",
     "summary": "Internal host performing full port scan across /24 subnet. 1247 unique destination ports observed in 60 seconds. Indicates lateral reconnaissance phase.",
     "true_positive": True, "ioc_count": 1,
     "recommended_actions": ["Isolate source host for investigation", "Review firewall rules", "Check for compromised credentials"]},
    {"severity": "critical", "confidence": 0.97, "category": "c2_communication",
     "summary": "Confirmed C2 beacon communication. Periodic HTTPS callbacks to known malicious IP (203.0.113.50) at regular 60s intervals. Associated with APT29 infrastructure.",
     "true_positive": True, "ioc_count": 3,
     "recommended_actions": ["Isolate infected host immediately", "Block IP at perimeter", "Hunt for lateral movement", "Reset all credentials for affected user"]},
    {"severity": "high", "confidence": 0.92, "category": "lateral_movement",
     "summary": "PsExec-style lateral movement detected via SMB. Process execution on remote host 10.0.0.30 using service control manager. Indicates active compromise.",
     "true_positive": True, "ioc_count": 2,
     "recommended_actions": ["Isolate both hosts", "Review service creation logs", "Check for persistence mechanisms"]},
    {"severity": "critical", "confidence": 0.96, "category": "exfiltration",
     "summary": "Massive data exfiltration via SSH to external IP. 2.3 GB transferred over 31 minutes. Data staging likely occurred before exfiltration.",
     "true_positive": True, "ioc_count": 2,
     "recommended_actions": ["Block destination IP", "Identify exfiltrated data scope", "Engage incident response team", "Preserve forensic evidence"]},
]

MOCK_MITRE_CONTEXT = [
    {"technique": "T1110.001", "name": "Password Guessing", "tactic": "Credential Access",
     "description": "Adversaries may guess passwords to gain access."},
    {"technique": "T1046", "name": "Network Service Discovery", "tactic": "Discovery",
     "description": "Adversaries may attempt to discover services running on remote hosts."},
    {"technique": "T1071.001", "name": "Web Protocols: HTTP", "tactic": "Command and Control",
     "description": "Adversaries may communicate using application layer protocols to avoid detection."},
    {"technique": "T1021.002", "name": "Remote Services: SMB/Windows Admin Shares", "tactic": "Lateral Movement",
     "description": "Adversaries may use SMB to move laterally across a network."},
    {"technique": "T1048.002", "name": "Exfiltration Over Asymmetric Encrypted Channel", "tactic": "Exfiltration",
     "description": "Adversaries may steal data by exfiltrating it over an encrypted channel."},
]

MOCK_RESPONSE_PLAN = {
    "plan_id": "RP-001",
    "phase_1": {"action": "Block source IP at perimeter firewall", "priority": "immediate", "target": "firewall"},
    "phase_2": {"action": "Isolate affected hosts from network", "priority": "urgent", "target": "network"},
    "phase_3": {"action": "Reset compromised credentials", "priority": "high", "target": "identity"},
    "estimated_containment_time": "15 minutes",
}


def generate_alerts(count: int = 5) -> List[Dict[str, Any]]:
    """Generate synthetic security alerts with realistic timestamps."""
    now = datetime.utcnow()
    alerts = []
    for i in range(min(count, len(SYNTHETIC_ALERTS))):
        alert = SYNTHETIC_ALERTS[i].copy()
        alert["timestamp"] = (now - timedelta(minutes=len(SYNTHETIC_ALERTS) - i)).isoformat() + "Z"
        alerts.append(alert)
    return alerts


def _print_banner():
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
    console.print(Panel.fit(
        "[bold cyan]Argus AI Pipeline Demo[/]\n"
        "[dim]Synthetic alerts → ML classification → LLM triage → MITRE mapping → Response plan[/]",
        border_style="cyan",
    ))


def _print_alert(i: int, alert: dict, ml: dict, triage: dict, mitre: dict, response: dict):
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    console = Console()

    severity_colors = {"critical": "red", "high": "yellow", "medium": "blue", "low": "green"}
    sev = triage["severity"]
    color = severity_colors.get(sev, "white")

    console.print()
    console.rule(f"[bold]Alert {i+1}: {alert['rule_description']}")

    # Alert source
    t = Table(show_header=False, box=None, padding=(0, 2))
    t.add_column(style="dim")
    t.add_column()
    t.add_row("Source IP", alert["source_ip"])
    t.add_row("Dest IP", alert["destination_ip"])
    t.add_row("Rule Level", str(alert["rule_level"]))
    t.add_row("Agent", alert["agent_name"])
    console.print(t)

    # ML classification
    console.print()
    pred = ml["prediction"]
    conf = ml["confidence"]
    model = ml["model_used"]
    console.print(f"  [bold]ML:[/] [{color}]{pred}[/] ({conf:.0%}) via [cyan]{model}[/]")

    # Triage
    console.print(f"  [bold]Triage:[/] [{color}]{sev.upper()}[/] — {triage['summary'][:120]}...")

    # MITRE
    console.print(f"  [bold]MITRE:[/] {mitre['tactic']} → [cyan]{mitre['name']}[/] ({mitre['technique']})")

    # Response
    console.print(f"  [bold]Response:[/] {response['phase_1']['action']}")


def _run_live_demo(alerts: List[Dict[str, Any]]):
    """Run demo against live services via HTTP."""
    import httpx
    from rich.console import Console
    console = Console()

    console.print("\n[bold yellow]Running against live services...[/]\n")

    for i, alert in enumerate(alerts):
        console.rule(f"Processing Alert {i+1}: {alert['rule_description']}")

        # ML Inference (use zero features as placeholder)
        try:
            ml_resp = httpx.post("http://localhost:8500/predict",
                                 json={"features": [0.0]*77, "model_name": "random_forest"},
                                 timeout=10.0)
            ml = ml_resp.json()
            console.print(f"  [bold]ML:[/] {ml.get('prediction', 'N/A')} ({ml.get('confidence', 0):.0%})")
        except Exception as e:
            console.print(f"  [red]ML service unavailable: {e}[/]")

        # Alert Triage
        try:
            triage_resp = httpx.post("http://localhost:8100/api/v1/triage/analyze",
                                     json=alert, timeout=30.0)
            triage = triage_resp.json()
            console.print(f"  [bold]Triage:[/] {triage.get('severity', 'N/A')} — {triage.get('summary', '')[:100]}")
        except Exception as e:
            console.print(f"  [red]Alert triage unavailable: {e}[/]")

        # RAG enrichment
        try:
            rag_resp = httpx.post("http://localhost:8300/api/v1/rag/retrieve",
                                  json={"query": alert.get("rule_description", ""), "top_k": 1},
                                  timeout=10.0)
            if rag_resp.status_code == 200:
                console.print(f"  [bold]RAG:[/] MITRE context retrieved")
        except Exception:
            pass

        console.print()


def _run_synthetic_demo(alerts: List[Dict[str, Any]]):
    """Run demo with synthetic (mocked) responses."""
    from rich.console import Console
    console = Console()

    console.print("\n[bold green]Running synthetic demo (no Docker needed)...[/]\n")

    for i, alert in enumerate(alerts):
        ml = MOCK_ML_RESPONSES[i % len(MOCK_ML_RESPONSES)]
        triage = MOCK_TRIAGE_RESPONSES[i % len(MOCK_TRIAGE_RESPONSES)]
        mitre = MOCK_MITRE_CONTEXT[i % len(MOCK_MITRE_CONTEXT)]
        response = MOCK_RESPONSE_PLAN.copy()
        response["plan_id"] = f"RP-{i+1:03d}"
        _print_alert(i, alert, ml, triage, mitre, response)

    # Summary
    console.print()
    console.rule("[bold]Pipeline Summary")
    console.print(f"  Alerts processed:  [bold]{len(alerts)}[/]")
    console.print(f"  All classified:    [bold green]ATTACK[/]")
    console.print(f"  Severity spread:   [red]3 critical[/] · [yellow]2 high[/]")
    console.print(f"  Kill chain stages: [cyan]5/5[/] (full attack lifecycle)")
    console.print(f"  Response plans:    [green]{len(alerts)} generated[/]")
    console.print()
    console.print("[dim]Run [bold]argus demo --live[/] to try against running services[/]")


def run_demo(live: bool = False):
    """Main entry point for the demo."""
    _print_banner()
    alerts = generate_alerts(count=5)

    if live:
        _run_live_demo(alerts)
    else:
        _run_synthetic_demo(alerts)
