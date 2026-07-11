# Research Context

AI-SOC is informed by published research on AI/ML integration in security operations. The platform implements and validates several themes from the academic literature:

- **Human-AI collaboration** rather than blind automation
- **Alert triage and summarization** using local LLMs
- **Threat-intelligence grounding** through retrieval-augmented generation
- **Feedback loops** for analyst correction and model improvement
- **Practical integration** challenges of connecting AI services to existing SIEM infrastructure

## Design Philosophy

The system follows a local-first approach: all security event data is processed through local services and Ollama-backed LLM inference rather than hosted APIs. This addresses data sovereignty concerns common in security environments.

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Classical ML over deep learning for IDS | Sub-millisecond inference, interpretable, competitive accuracy |
| Local LLM (Ollama) over cloud APIs | Data stays on-premise, no API costs, no rate limits |
| RAG over pure generation | Grounds LLM responses in verified threat intelligence |
| Microservices over monolith | Independent scaling, fault isolation, technology diversity |
| Monte Carlo simulation over single runs | Produces statistical distributions instead of anecdotal results |

## ML Approach

The intrusion detection models use classical ML (Random Forest, XGBoost, Decision Tree) rather than deep learning. This choice is driven by:

- Inference latency under 1ms (vs seconds for neural networks)
- No GPU requirement
- Interpretable feature importance
- Competitive accuracy on CICIDS2017 (99.28% for Random Forest)

## References

- CICIDS2017 dataset: https://www.unb.ca/cic/datasets/ids-2017.html
- MITRE ATT&CK: https://attack.mitre.org/
- D3FEND: https://d3fend.mitre.org/
- OWASP Top 10 for LLM Applications: https://owasp.org/www-project-top-10-for-large-language-model-applications/
