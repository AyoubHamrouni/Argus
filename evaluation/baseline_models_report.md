# CICIDS2017 Baseline Models - Evaluation Report
**Generated:** 2026-07-11 04:16:59
**Dataset:** Synthetic surrogate (50,000 samples, 78 features)
**Mission:** OPERATION ARGUS-ML

## Executive Summary

This report presents the performance evaluation of three baseline machine learning models trained on synthetic data mimicking the CICIDS2017 intrusion detection dataset (binary classification: BENIGN vs ATTACK).

## Model Performance Comparison

| Model | Accuracy | Precision | Recall | F1-Score | FP Rate | ROC AUC | Inference (ms) | Size (MB) |
|-------|----------|-----------|--------|----------|---------|---------|----------------|----------|
| Random Forest | 89.93% | 90.08% | 89.93% | 89.50% | 29.00% | 0.9543 | 0.0069 | 93.35 |
| Xgboost | 92.83% | 92.80% | 92.83% | 92.81% | 13.38% | 0.9662 | 0.0013 | 1.46 |
| Decision Tree | 73.91% | 74.04% | 73.91% | 73.97% | 44.98% | 0.6576 | 0.0003 | 0.61 |

## Generated Artifacts

- `confusion_matrices.png`
- `confusion_matrices_normalized.png`
- `roc_curves.png`
- `precision_recall_curves.png`
- `model_comparison.png`
- `metrics.json`
- `classification_report_random_forest.txt`
- `classification_report_xgboost.txt`
- `classification_report_decision_tree.txt`
- `baseline_models_report.md`

## Random Forest

- **Accuracy:** 89.93%
- **Precision:** 90.08%
- **Recall:** 89.93%
- **F1-Score:** 89.50%
- **False Positive Rate:** 29.0028%
- **ROC AUC:** 0.954268
- **Training Time:** 3.47s
- **Avg Inference Time:** 0.0069ms/sample
- **Model Size:** 93.35MB

**Confusion Matrix:**
```
[[2022  826]
 [ 181 6971]]
```

## Xgboost

- **Accuracy:** 92.83%
- **Precision:** 92.80%
- **Recall:** 92.83%
- **F1-Score:** 92.81%
- **False Positive Rate:** 13.3778%
- **ROC AUC:** 0.966210
- **Training Time:** 6.94s
- **Avg Inference Time:** 0.0013ms/sample
- **Model Size:** 1.46MB

**Confusion Matrix:**
```
[[2467  381]
 [ 336 6816]]
```

## Decision Tree

- **Accuracy:** 73.91%
- **Precision:** 74.04%
- **Recall:** 73.91%
- **F1-Score:** 73.97%
- **False Positive Rate:** 44.9789%
- **ROC AUC:** 0.657628
- **Training Time:** 3.47s
- **Avg Inference Time:** 0.0003ms/sample
- **Model Size:** 0.61MB

**Confusion Matrix:**
```
[[1567 1281]
 [1328 5824]]
```

## Best Model Recommendations

- **Best F1-Score:** Xgboost (92.81%)
- **Best ROC AUC:** Xgboost (0.9662)
- **Fastest Inference:** Decision Tree (0.0003ms)
