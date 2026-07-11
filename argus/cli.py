import click
import subprocess
import sys
import os
import json
import time
from pathlib import Path

COMPOSE_DIR = Path(__file__).parent.parent / "docker-compose"
AI_COMPOSE = COMPOSE_DIR / "ai-services.yml"
SIEM_COMPOSE = COMPOSE_DIR / "phase1-siem-core.yml"
SIEM_WINDOWS_COMPOSE = COMPOSE_DIR / "phase1-siem-core-windows.yml"
MONITORING_COMPOSE = COMPOSE_DIR / "monitoring-stack.yml"

@click.group()
@click.version_option(package_name="argus")
def main():
    """Argus — AI-Augmented SOC platform."""
    pass

@main.command()
@click.option("--live", is_flag=True, help="Run against live services")
def demo(live):
    """Run a demo of the AI pipeline."""
    from .demo import run_demo
    run_demo(live=live)

@main.command()
@click.option("--profile", type=click.Choice(["ai", "full", "minimal"]), default="ai",
              help="Deployment profile: ai (AI services only), full (SIEM+AI+monitoring), minimal (quickstart)")
@click.option("-d", "--detach", is_flag=True, default=True, help="Run in detached mode")
def up(profile, detach):
    """Start Argus services."""
    from rich.console import Console
    console = Console()

    compose_files = []
    if profile == "ai":
        compose_files = [str(AI_COMPOSE)]
    elif profile == "minimal":
        compose_files = [str(SIEM_COMPOSE), str(AI_COMPOSE)]
    elif profile == "full":
        compose_files = [str(SIEM_COMPOSE), str(AI_COMPOSE), str(MONITORING_COMPOSE)]

    console.print(f"[bold cyan]Starting Argus ({profile} profile)...[/]")

    cmd = ["docker", "compose"]
    for f in compose_files:
        cmd.extend(["-f", f])
    cmd.extend(["up", "-d" if detach else "--abort-on-container-exit"])

    result = subprocess.run(cmd, cwd=str(Path(__file__).parent.parent))
    if result.returncode == 0:
        console.print("[bold green]Argus is running![/]")
        _print_service_urls(profile)
    else:
        console.print("[bold red]Failed to start services.[/]")
        sys.exit(1)

@main.command()
@click.option("--profile", type=click.Choice(["ai", "full", "minimal"]), default="ai")
@click.option("-v", "--volumes", is_flag=True, help="Also remove volumes")
def down(profile, volumes):
    """Stop Argus services."""
    from rich.console import Console
    console = Console()

    compose_files = []
    if profile == "ai":
        compose_files = [str(AI_COMPOSE)]
    elif profile == "minimal":
        compose_files = [str(SIEM_COMPOSE), str(AI_COMPOSE)]
    elif profile == "full":
        compose_files = [str(SIEM_COMPOSE), str(AI_COMPOSE), str(MONITORING_COMPOSE)]

    cmd = ["docker", "compose"]
    for f in compose_files:
        cmd.extend(["-f", f])
    cmd.append("down")
    if volumes:
        cmd.append("-v")

    subprocess.run(cmd, cwd=str(Path(__file__).parent.parent))
    console.print("[bold yellow]Argus stopped.[/]")

@main.command()
@click.argument("service", required=False)
def logs(service):
    """Tail service logs."""
    cmd = ["docker", "compose", "-f", str(AI_COMPOSE), "logs", "-f"]
    if service:
        cmd.append(service)
    subprocess.run(cmd, cwd=str(Path(__file__).parent.parent))

@main.command()
def status():
    """Show service health status."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="Argus Service Status")
    table.add_column("Service", style="cyan")
    table.add_column("Port", style="green")
    table.add_column("Status", style="bold")

    services = [
        ("alert-triage", "8100"),
        ("rag-service", "8300"),
        ("ml-inference", "8500"),
        ("wazuh-integration", "8002"),
        ("feedback-service", "8400"),
        ("correlation-engine", "8600"),
        ("response-orchestrator", "8800"),
        ("rule-generator", "8700"),
        ("ollama", "11434"),
        ("chromadb", "8200"),
    ]

    import httpx
    for name, port in services:
        try:
            r = httpx.get(f"http://localhost:{port}/health", timeout=2.0)
            status_text = "[green]UP[/]" if r.status_code == 200 else f"[red]HTTP {r.status_code}[/]"
        except Exception:
            status_text = "[red]DOWN[/]"
        table.add_row(name, port, status_text)

    console.print(table)

@main.command()
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def health(fmt):
    """Run health checks against all services."""
    from .health import run_health_checks
    run_health_checks(fmt=fmt)

@main.command()
def deploy():
    """Run the full deployment script."""
    deploy_script = Path(__file__).parent.parent / "deploy-argus.sh"
    if not deploy_script.exists():
        deploy_script = Path(__file__).parent.parent / "deploy-argus.ps1"

    if deploy_script.suffix == ".ps1":
        subprocess.run(["pwsh", str(deploy_script)])
    else:
        subprocess.run([str(deploy_script)])

@main.command("test-data")
@click.option("--count", default=5, help="Number of alerts to generate")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def test_data(count, output):
    """Generate synthetic test alerts."""
    from .demo import generate_alerts
    import json

    alerts = generate_alerts(count=count)

    if output:
        Path(output).write_text(json.dumps(alerts, indent=2))
        click.echo(f"Generated {count} alerts → {output}")
    else:
        click.echo(json.dumps(alerts, indent=2))

def _print_service_urls(profile):
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="Service URLs")
    table.add_column("Service", style="cyan")
    table.add_column("URL", style="green")
    table.add_column("Docs", style="blue")

    urls = [
        ("Alert Triage", "http://localhost:8100", "/docs"),
        ("RAG Service", "http://localhost:8300", "/docs"),
        ("ML Inference", "http://localhost:8500", "/docs"),
        ("Wazuh Integration", "http://localhost:8002", "/docs"),
        ("Feedback Service", "http://localhost:8400", "/docs"),
        ("Correlation Engine", "http://localhost:8600", "/docs"),
        ("Response Orchestrator", "http://localhost:8800", "/docs"),
        ("Rule Generator", "http://localhost:8700", "/docs"),
    ]

    if profile in ("ai", "full"):
        urls.append(("Grafana", "http://localhost:3000", ""))

    for name, url, docs in urls:
        table.add_row(name, url, f"{url}{docs}" if docs else "")

    console.print(table)

if __name__ == "__main__":
    main()
