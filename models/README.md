# Pre-trained Model Artifacts

This directory contains trained ML model artifacts for the Argus Inference API.

**These files are excluded from the git repository** via `.gitignore` for security (pickle deserialization risk) and repository size reasons.

## Downloading Models

```bash
# Download from the latest GitHub Release
./download_models.sh

# Download to a custom directory
./download_models.sh --dir /path/to/models

# Download a specific release tag
./download_models.sh --tag v1.0.0
```

## Model Files

| File | Description |
|------|-------------|
| `random_forest_ids.pkl` | Random Forest classifier (CICIDS2017) |
| `xgboost_ids.pkl` | XGBoost gradient boosting classifier |
| `decision_tree_ids.pkl` | Decision Tree classifier |
| `scaler.pkl` | StandardScaler for feature normalization |
| `label_encoder.pkl` | Label encoder (BENIGN / ATTACK) |
| `feature_names.pkl` | Feature names (77 CICIDS2017 network flow features) |

## Training

To retrain models from scratch, see `ml_training/README.md` and run:

```bash
cd ml_training
python train_ids_model.py
```

This requires the CICIDS2017 dataset (see `datasets/CICIDS2017/README.md`).

## Security Note

Pickle files can execute arbitrary code when deserialized. Only load model artifacts from trusted sources. The download script fetches from the official GitHub Releases of this repository.
