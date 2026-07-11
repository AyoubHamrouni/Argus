# ML Models

## Overview

Argus uses trained machine learning models for network intrusion detection on the CICIDS2017 dataset. The models perform binary classification (BENIGN vs ATTACK) on network flow data using 77 extracted features.

## Model Performance

| Model | Accuracy | Precision | Recall | F1-Score | FPR | Inference Time |
|-------|----------|-----------|--------|----------|-----|----------------|
| Random Forest | 99.28% | 99.29% | 99.28% | 99.28% | 0.25% | 0.0008ms |
| XGBoost | 99.21% | 99.23% | 99.21% | 99.21% | 0.09% | 0.0003ms |
| Decision Tree | 99.10% | 99.13% | 99.10% | 99.11% | 0.24% | 0.0002ms |

## Trained Artifacts

All model files are stored in `models/`:

| File | Description |
|------|-------------|
| `random_forest_ids.pkl` | Random Forest classifier |
| `xgboost_ids.pkl` | XGBoost gradient boosting classifier |
| `decision_tree_ids.pkl` | Decision Tree classifier |
| `scaler.pkl` | StandardScaler for feature normalization |
| `label_encoder.pkl` | Label encoder for target classes |
| `feature_names.pkl` | Ordered feature names (77 features) |

To download pre-trained models:

```bash
./models/download_models.sh
```

## CICIDS2017 Dataset

The Canadian Institute for Cybersecurity Intrusion Detection System 2017 dataset captures 5 days of network traffic including benign activity and 15 attack types:

- **DoS/DDoS**: GoldenEye, Hulk, Slowloris, SlowHTTPTest, Heartbleed
- **Brute Force**: FTP-Patator, SSH-Patator
- **Web Attacks**: SQL Injection, XSS
- **Infiltration**: Infiltration attacks
- **Port Scan**: Network reconnaissance
- **DDoS**: Distributed denial of service

**Dataset statistics:**

| Metric | Value |
|--------|-------|
| Total flows | 2,830,743 |
| Benign flows | 2,273,097 (80.3%) |
| Attack flows | 557,646 (19.7%) |
| Features per flow | 84 raw → 77 after preprocessing |
| Attack categories | 15 |

## Preprocessing Pipeline

1. Drop non-informative columns (flow IDs, timestamps)
2. Replace infinite values with NaN, then fill with column medians
3. Encode labels: `BENIGN` → 0, all attack types → 1
4. Select 77 features (drop low-variance and highly correlated features)
5. Apply StandardScaler normalization

## Training

```bash
cd ml_training
pip install -r requirements.txt
python train_ids_model.py
```

This produces all `.pkl` artifacts in `models/`.

## Inference API

The ML Inference service loads trained models and exposes a REST API:

```bash
# Start the service
cd ml_training
uvicorn inference_api:app --host 0.0.0.0 --port 8500

# Classify a flow
curl -X POST http://localhost:8500/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [0.0] * 77, "model_name": "random_forest"}'
```

The `features` array must contain exactly 77 values in the order defined by `models/feature_names.pkl`.

## Retraining

The retraining pipeline (`services/retraining/`) supports champion/challenger model promotion:

1. Collect analyst feedback from the Feedback Service
2. Retrain models on updated labeled data
3. Evaluate challenger against champion
4. Promote if challenger improves metrics
5. Reload inference service with new artifacts

## Future Work

- Multi-class classification (15 attack types instead of binary)
- Adversarial robustness evaluation
- Feature engineering for encrypted traffic
- Online learning for concept drift detection
