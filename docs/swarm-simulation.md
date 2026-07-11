# Swarm Simulation

The correlation engine includes a multi-agent attack simulation framework. It uses LLM-powered agents to model attacker behavior and evaluate defensive strategies through Monte Carlo simulation.

## How It Works

The simulator deploys hierarchical agent swarms against a modeled infrastructure:

- **Leader agents** (LLM-powered) make strategic attack decisions based on observed infrastructure state
- **Follower agents** (rule-based) explore probabilistic variations of the leader's strategy
- **Defender agents** (LLM-powered) simulate SOC analyst, incident responder, and threat hunter archetypes

By running many simulations across attacker/defender archetypes, the system produces statistical distributions rather than single-path results.

## Architecture

```
┌─────────────────────────────────────────────┐
│              Simulation Engine               │
│                                              │
│  ┌──────────┐    ┌──────────┐               │
│  │ Attacker │    │ Defender │               │
│  │ Archetype│    │ Archetype│               │
│  └────┬─────┘    └────┬─────┘               │
│       │               │                     │
│  ┌────▼─────┐    ┌────▼─────┐               │
│  │  Leader  │    │  Leader  │               │
│  │  (LLM)   │    │  (LLM)   │               │
│  └────┬─────┘    └────┬─────┘               │
│       │               │                     │
│  ┌────▼─────┐    ┌────▼─────┐               │
│  │Followers │    │Followers │               │
│  │ (rules)  │    │ (rules)  │               │
│  └──────────┘    └──────────┘               │
│                                              │
│         Monte Carlo Aggregation              │
└─────────────────────────────────────────────┘
```

## Archetypes

### Attackers

| Archetype | Strategy |
|-----------|----------|
| Opportunist | Exploits any available vulnerability |
| APT | Persistent, stealthy, multi-stage attacks |
| Ransomware | Rapid encryption and extortion |
| Insider | Legitimate access abuse |

### Defenders

| Archetype | Strategy |
|-----------|----------|
| SOC Analyst | Monitors alerts, investigates anomalies |
| Incident Responder | Contains and eradicates threats |
| Threat Hunter | Proactively searches for hidden threats |

## Running Simulations

### Single Campaign

```bash
curl -X POST "http://localhost:8600/api/v1/correlation/simulate?timesteps=3"
```

### Swarm Simulation

```bash
# Start a swarm run
curl -X POST "http://localhost:8600/api/v1/correlation/simulate/swarm/start?swarm_size=100&monte_carlo_runs=5&timesteps=6"

# Poll status
curl "http://localhost:8600/api/v1/correlation/simulate/swarm/{swarm_id}/status"

# Fetch results
curl "http://localhost:8600/api/v1/correlation/simulate/swarm/{swarm_id}/result"
```

### Environment Setup

Simulations can use environments loaded from Wazuh inventory data:

```bash
curl "http://localhost:8600/api/v1/correlation/simulate/environment/from-wazuh"
```

## Results

Simulation output includes:

- **Host risk heatmaps** — Per-host compromise probability
- **Attack path frequencies** — Which paths attackers take most often
- **Confidence intervals** — Statistical bounds on predictions
- **Defense effectiveness** — How much each defensive measure reduces risk
- **Unique attack paths** — Number of distinct attack strategies discovered

## Key Findings

From the included experiment artifacts (`services/correlation-engine/experiments_v3/`):

| Metric | Result |
|--------|--------|
| Total agent runs | 37,575 |
| Unique attack paths | 18 |
| Model-scale effect | 14B model found more paths than 3B |
| Defender impact | 44% overall compromise reduction |
| Monitored hosts | 93% compromise reduction |

## Limitations

- Results are directional research evidence, not validated forecasts
- Has not been benchmarked against real red-team outcomes
- Environment models are simplified representations
- LLM reasoning depth is the binding constraint, not agent count

## Experiment Artifacts

Raw experiment data is stored in `services/correlation-engine/experiments_v3/` with per-run metrics, host risk scores, and attacker path logs.
