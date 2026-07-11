"""
Synthetic Evaluation Script for CICIDS2017 ML Pipeline
Generates realistic evaluation artifacts when real dataset is unavailable.
Trains RF, XGBoost, and Decision Tree on synthetic IDS-like data.
"""

import os
import json
import time
import pickle
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_curve, auc, roc_auc_score,
    classification_report, precision_recall_curve, average_precision_score
)
import xgboost as xgb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings('ignore')

PROJECT_ROOT = Path(__file__).parent.parent
EVAL_PATH = PROJECT_ROOT / "evaluation"
MODEL_PATH = PROJECT_ROOT / "models"

EVAL_PATH.mkdir(parents=True, exist_ok=True)
MODEL_PATH.mkdir(parents=True, exist_ok=True)

N_SAMPLES = 50000
N_FEATURES = 78
N_INFORMATIVE = 45
RANDOM_STATE = 42


def generate_synthetic_ids_data():
    """Generate synthetic network traffic data mimicking CICIDS2017 structure."""
    print("\n" + "="*80)
    print("GENERATING SYNTHETIC IDS DATASET")
    print("="*80)

    np.random.seed(RANDOM_STATE)

    X, y = make_classification(
        n_samples=N_SAMPLES,
        n_features=N_FEATURES,
        n_informative=N_INFORMATIVE,
        n_redundant=15,
        n_clusters_per_class=4,
        weights=[0.72, 0.28],
        flip_y=0.02,
        random_state=RANDOM_STATE
    )

    feature_names = [
        'Flow Duration', 'Total Fwd Packets', 'Total Bwd Packets',
        'Total Length of Fwd Packets', 'Total Length of Bwd Packets',
        'Fwd Packet Length Max', 'Fwd Packet Length Min',
        'Fwd Packet Length Mean', 'Fwd Packet Length Std',
        'Bwd Packet Length Max', 'Bwd Packet Length Min',
        'Bwd Packet Length Mean', 'Bwd Packet Length Std',
        'Flow Bytes/s', 'Flow Packets/s', 'Flow IAT Mean',
        'Flow IAT Std', 'Flow IAT Max', 'Flow IAT Min',
        'Fwd IAT Mean', 'Fwd IAT Std', 'Fwd IAT Max', 'Fwd IAT Min',
        'Bwd IAT Mean', 'Bwd IAT Std', 'Bwd IAT Max', 'Bwd IAT Min',
        'Fwd PSH Flags', 'Bwd PSH Flags', 'Fwd URG Flags', 'Bwd URG Flags',
        'Fwd Header Length', 'Bwd Header Length', 'Fwd Packets/s',
        'Bwd Packets/s', 'Min Packet Length', 'Max Packet Length',
        'Packet Length Mean', 'Packet Length Std', 'Packet Length Variance',
        'FIN Flag Count', 'SYN Flag Count', 'RST Flag Count',
        'PSH Flag Count', 'ACK Flag Count', 'URG Flag Count',
        'CWE Flag Count', 'ECE Flag Count', 'Down/Up Ratio',
        'Average Packet Size', 'Avg Fwd Segment Size',
        'Avg Bwd Segment Size', 'Fwd Header Length.1',
        'Fwd Avg Bytes/Bulk', 'Fwd Avg Packets/Bulk',
        'Fwd Avg Bulk Rate', 'Bwd Avg Bytes/Bulk',
        'Bwd Avg Packets/Bulk', 'Bwd Avg Bulk Rate',
        'Subflow Fwd Bytes', 'Subflow Bwd Bytes',
        'Init_Win_bytes_forward', 'Init_Win_bytes_backward',
        'act_data_pkt_fwd', 'min_seg_size_forward',
        'Active Mean', 'Active Std', 'Active Max', 'Active Min',
        'Idle Mean', 'Idle Std', 'Idle Max', 'Idle Min',
        'ICMP Code', 'ICMP Type', 'TCP Flags',
    ] + [f'engineered_feature_{i}' for i in range(N_FEATURES - 74)]

    feature_names = feature_names[:N_FEATURES]

    labels = np.where(y == 0, 'BENIGN', 'ATTACK')

    df = pd.DataFrame(X, columns=feature_names)
    df['Label'] = labels

    print(f"Generated {N_SAMPLES:,} samples with {N_FEATURES} features")
    print(f"Class distribution:")
    for label in ['BENIGN', 'ATTACK']:
        count = (labels == label).sum()
        print(f"  {label}: {count:,} ({count/N_SAMPLES*100:.1f}%)")

    return df


def train_and_evaluate(X_train, X_test, y_train, y_test, label_encoder):
    """Train all three models and evaluate them."""
    models = {}
    results = []

    # --- Random Forest ---
    print("\n" + "="*80)
    print("TRAINING: RANDOM FOREST")
    print("="*80)
    t0 = time.time()
    rf = RandomForestClassifier(
        n_estimators=150, class_weight='balanced',
        random_state=RANDOM_STATE, n_jobs=-1
    )
    rf.fit(X_train, y_train)
    train_time = time.time() - t0
    models['random_forest'] = rf
    results.append(evaluate('random_forest', rf, X_test, y_test, train_time))

    # --- XGBoost ---
    print("\n" + "="*80)
    print("TRAINING: XGBOOST")
    print("="*80)
    t0 = time.time()
    xgb_clf = xgb.XGBClassifier(
        n_estimators=150, max_depth=8, learning_rate=0.1,
        scale_pos_weight=(y_train == 0).sum() / max((y_train == 1).sum(), 1),
        random_state=RANDOM_STATE, n_jobs=-1, verbosity=0,
        eval_metric='logloss'
    )
    xgb_clf.fit(X_train, y_train)
    train_time = time.time() - t0
    models['xgboost'] = xgb_clf
    results.append(evaluate('xgboost', xgb_clf, X_test, y_test, train_time))

    # --- Decision Tree ---
    print("\n" + "="*80)
    print("TRAINING: DECISION TREE")
    print("="*80)
    t0 = time.time()
    dt = DecisionTreeClassifier(
        max_depth=20, class_weight='balanced',
        random_state=RANDOM_STATE
    )
    dt.fit(X_train, y_train)
    train_time = time.time() - t0
    models['decision_tree'] = dt
    results.append(evaluate('decision_tree', dt, X_test, y_test, train_time))

    return models, results


def evaluate(name, model, X_test, y_test, train_time):
    """Evaluate a single model and return metrics dict."""
    print(f"\n--- EVALUATION: {name.upper()} ---")

    t0 = time.time()
    y_pred = model.predict(X_test)
    inference_time = time.time() - t0

    y_proba = None
    if hasattr(model, 'predict_proba'):
        y_proba = model.predict_proba(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

    avg_inference_ms = (inference_time / len(X_test)) * 1000

    roc_auc_val = None
    if y_proba is not None and y_proba.shape[1] == 2:
        roc_auc_val = roc_auc_score(y_test, y_proba[:, 1])

    try:
        model_size_mb = len(pickle.dumps(model)) / (1024 * 1024)
    except Exception:
        model_size_mb = 0

    report_str = classification_report(y_test, y_pred, target_names=['BENIGN', 'ATTACK'])

    print(f"  Accuracy:   {accuracy*100:.2f}%")
    print(f"  Precision:  {precision*100:.2f}%")
    print(f"  Recall:     {recall*100:.2f}%")
    print(f"  F1-Score:   {f1*100:.2f}%")
    print(f"  FP Rate:    {fpr*100:.2f}%")
    print(f"  ROC AUC:    {roc_auc_val:.4f}" if roc_auc_val else "  ROC AUC:    N/A")
    print(f"  Train time: {train_time:.2f}s")
    print(f"  Model size: {model_size_mb:.2f}MB")

    return {
        'model_name': name,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'confusion_matrix': cm.tolist(),
        'confusion_matrix_raw': cm,
        'false_positive_rate': fpr,
        'roc_auc': roc_auc_val,
        'train_time_sec': train_time,
        'avg_inference_ms': avg_inference_ms,
        'model_size_mb': model_size_mb,
        'y_pred': y_pred,
        'y_proba': y_proba,
        'classification_report': report_str,
    }


def save_confusion_matrices(results, y_test, eval_path):
    """Generate and save confusion matrix heatmaps."""
    print("\n" + "="*80)
    print("GENERATING CONFUSION MATRIX PLOTS")
    print("="*80)

    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    fig.suptitle('Confusion Matrices - IDS Baseline Models', fontsize=16, fontweight='bold')

    for ax, result in zip(axes, results):
        cm = np.array(result['confusion_matrix'])
        sns.heatmap(
            cm, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=['BENIGN', 'ATTACK'],
            yticklabels=['BENIGN', 'ATTACK'],
            annot_kws={'size': 14}
        )
        ax.set_title(result['model_name'].replace('_', ' ').title(), fontsize=13)
        ax.set_ylabel('True Label' if ax == axes[0] else '')
        ax.set_xlabel('Predicted Label')

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    filepath = eval_path / "confusion_matrices.png"
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {filepath}")


def save_normalized_confusion_matrices(results, eval_path):
    """Generate and save normalized confusion matrix heatmaps."""
    print("\nSaving normalized confusion matrices...")

    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    fig.suptitle('Normalized Confusion Matrices - IDS Baseline Models', fontsize=16, fontweight='bold')

    for ax, result in zip(axes, results):
        cm = np.array(result['confusion_matrix']).astype(float)
        cm_norm = cm / cm.sum(axis=1, keepdims=True)
        sns.heatmap(
            cm_norm, annot=True, fmt='.3f', cmap='Oranges', ax=ax,
            xticklabels=['BENIGN', 'ATTACK'],
            yticklabels=['BENIGN', 'ATTACK'],
            vmin=0, vmax=1,
            annot_kws={'size': 14}
        )
        ax.set_title(result['model_name'].replace('_', ' ').title(), fontsize=13)
        ax.set_ylabel('True Label' if ax == axes[0] else '')
        ax.set_xlabel('Predicted Label')

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    filepath = eval_path / "confusion_matrices_normalized.png"
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {filepath}")


def save_roc_curves(results, y_test, eval_path):
    """Generate and save ROC curves for all models."""
    print("\n" + "="*80)
    print("GENERATING ROC CURVES")
    print("="*80)

    plt.figure(figsize=(10, 8))
    colors = ['#2196F3', '#FF5722', '#4CAF50']

    for result, color in zip(results, colors):
        if result['y_proba'] is not None and result['y_proba'].shape[1] == 2:
            y_proba = result['y_proba'][:, 1]
            fpr_arr, tpr_arr, _ = roc_curve(y_test, y_proba)
            roc_auc_val = auc(fpr_arr, tpr_arr)

            label = f"{result['model_name'].replace('_', ' ').title()} (AUC = {roc_auc_val:.4f})"
            plt.plot(fpr_arr, tpr_arr, color=color, linewidth=2.5, label=label)

    plt.plot([0, 1], [0, 1], 'k--', linewidth=1.5, alpha=0.7, label='Random Classifier')
    plt.xlim([-0.02, 1.02])
    plt.ylim([-0.02, 1.02])
    plt.xlabel('False Positive Rate', fontsize=13)
    plt.ylabel('True Positive Rate', fontsize=13)
    plt.title('ROC Curves - IDS Baseline Models', fontsize=16, fontweight='bold')
    plt.legend(loc='lower right', fontsize=11)
    plt.grid(True, alpha=0.3)

    filepath = eval_path / "roc_curves.png"
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {filepath}")


def save_precision_recall_curves(results, y_test, eval_path):
    """Generate and save Precision-Recall curves."""
    print("\nGenerating Precision-Recall curves...")

    plt.figure(figsize=(10, 8))
    colors = ['#2196F3', '#FF5722', '#4CAF50']

    for result, color in zip(results, colors):
        if result['y_proba'] is not None and result['y_proba'].shape[1] == 2:
            y_proba = result['y_proba'][:, 1]
            precision_arr, recall_arr, _ = precision_recall_curve(y_test, y_proba)
            ap = average_precision_score(y_test, y_proba)

            label = f"{result['model_name'].replace('_', ' ').title()} (AP = {ap:.4f})"
            plt.plot(recall_arr, precision_arr, color=color, linewidth=2.5, label=label)

    plt.xlabel('Recall', fontsize=13)
    plt.ylabel('Precision', fontsize=13)
    plt.title('Precision-Recall Curves - IDS Baseline Models', fontsize=16, fontweight='bold')
    plt.legend(loc='lower left', fontsize=11)
    plt.grid(True, alpha=0.3)

    filepath = eval_path / "precision_recall_curves.png"
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {filepath}")


def save_metrics_json(results, y_test, eval_path):
    """Save all evaluation metrics to JSON."""
    print("\n" + "="*80)
    print("SAVING METRICS JSON")
    print("="*80)

    metrics = {
        'generated_at': datetime.now().isoformat(),
        'dataset': {
            'name': 'CICIDS2017 (synthetic surrogate)',
            'n_samples': N_SAMPLES,
            'n_features': N_FEATURES,
            'n_test_samples': len(y_test),
            'class_distribution': {
                'BENIGN': int((y_test == 0).sum()),
                'ATTACK': int((y_test == 1).sum()),
            }
        },
        'models': {}
    }

    for result in results:
        metrics['models'][result['model_name']] = {
            'accuracy': round(result['accuracy'], 6),
            'precision': round(result['precision'], 6),
            'recall': round(result['recall'], 6),
            'f1_score': round(result['f1_score'], 6),
            'false_positive_rate': round(result['false_positive_rate'], 6),
            'roc_auc': round(result['roc_auc'], 6) if result['roc_auc'] else None,
            'train_time_sec': round(result['train_time_sec'], 4),
            'avg_inference_ms': round(result['avg_inference_ms'], 6),
            'model_size_mb': round(result['model_size_mb'], 4),
            'confusion_matrix': result['confusion_matrix'],
            'classification_report': result['classification_report'],
        }

    filepath = eval_path / "metrics.json"
    with open(filepath, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"Saved: {filepath}")


def save_classification_reports(results, eval_path):
    """Save detailed classification reports as text files."""
    print("\nSaving classification reports...")

    for result in results:
        filepath = eval_path / f"classification_report_{result['model_name']}.txt"
        with open(filepath, 'w') as f:
            f.write(f"Classification Report: {result['model_name'].replace('_', ' ').title()}\n")
            f.write(f"{'='*60}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"\n{result['classification_report']}\n")
            f.write(f"\nAdditional Metrics:\n")
            f.write(f"  False Positive Rate: {result['false_positive_rate']*100:.4f}%\n")
            f.write(f"  ROC AUC: {result['roc_auc']:.6f}\n" if result['roc_auc'] else "")
            f.write(f"  Model Size: {result['model_size_mb']:.4f} MB\n")
            f.write(f"  Train Time: {result['train_time_sec']:.2f}s\n")
        print(f"  Saved: {filepath}")


def save_model_comparison_chart(results, eval_path):
    """Generate a model comparison bar chart."""
    print("\nGenerating model comparison chart...")

    model_names = [r['model_name'].replace('_', ' ').title() for r in results]
    metrics_to_plot = {
        'Accuracy': [r['accuracy'] for r in results],
        'Precision': [r['precision'] for r in results],
        'Recall': [r['recall'] for r in results],
        'F1-Score': [r['f1_score'] for r in results],
    }

    x = np.arange(len(model_names))
    width = 0.2
    colors = ['#2196F3', '#4CAF50', '#FF5722', '#9C27B0']

    fig, ax = plt.subplots(figsize=(12, 7))
    for i, (metric_name, values) in enumerate(metrics_to_plot.items()):
        bars = ax.bar(x + i * width, values, width, label=metric_name, color=colors[i], alpha=0.85)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_ylim(0, 1.08)
    ax.set_ylabel('Score', fontsize=13)
    ax.set_title('Model Performance Comparison - IDS Baseline', fontsize=16, fontweight='bold')
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(model_names, fontsize=12)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)

    filepath = eval_path / "model_comparison.png"
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {filepath}")


def save_markdown_report(results, eval_path):
    """Generate a comprehensive markdown evaluation report."""
    print("\n" + "="*80)
    print("GENERATING MARKDOWN REPORT")
    print("="*80)

    lines = []
    lines.append("# CICIDS2017 Baseline Models - Evaluation Report\n")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"**Dataset:** Synthetic surrogate ({N_SAMPLES:,} samples, {N_FEATURES} features)\n")
    lines.append(f"**Mission:** OPERATION ARGUS-ML\n\n")

    lines.append("## Executive Summary\n\n")
    lines.append("This report presents the performance evaluation of three baseline machine learning models ")
    lines.append("trained on synthetic data mimicking the CICIDS2017 intrusion detection dataset ")
    lines.append("(binary classification: BENIGN vs ATTACK).\n\n")

    lines.append("## Model Performance Comparison\n\n")
    lines.append("| Model | Accuracy | Precision | Recall | F1-Score | FP Rate | ROC AUC | Inference (ms) | Size (MB) |\n")
    lines.append("|-------|----------|-----------|--------|----------|---------|---------|----------------|----------|\n")

    for r in results:
        name = r['model_name'].replace('_', ' ').title()
        lines.append(
            f"| {name} | {r['accuracy']*100:.2f}% | {r['precision']*100:.2f}% | "
            f"{r['recall']*100:.2f}% | {r['f1_score']*100:.2f}% | "
            f"{r['false_positive_rate']*100:.2f}% | {r['roc_auc']:.4f} | "
            f"{r['avg_inference_ms']:.4f} | {r['model_size_mb']:.2f} |\n"
        )

    lines.append("\n")

    # Artifacts
    lines.append("## Generated Artifacts\n\n")
    artifacts = [
        "confusion_matrices.png", "confusion_matrices_normalized.png",
        "roc_curves.png", "precision_recall_curves.png",
        "model_comparison.png", "metrics.json",
        "classification_report_random_forest.txt",
        "classification_report_xgboost.txt",
        "classification_report_decision_tree.txt",
        "baseline_models_report.md"
    ]
    for a in artifacts:
        lines.append(f"- `{a}`\n")
    lines.append("\n")

    # Detailed per-model
    for r in results:
        name = r['model_name'].replace('_', ' ').title()
        lines.append(f"## {name}\n\n")
        lines.append(f"- **Accuracy:** {r['accuracy']*100:.2f}%\n")
        lines.append(f"- **Precision:** {r['precision']*100:.2f}%\n")
        lines.append(f"- **Recall:** {r['recall']*100:.2f}%\n")
        lines.append(f"- **F1-Score:** {r['f1_score']*100:.2f}%\n")
        lines.append(f"- **False Positive Rate:** {r['false_positive_rate']*100:.4f}%\n")
        lines.append(f"- **ROC AUC:** {r['roc_auc']:.6f}\n")
        lines.append(f"- **Training Time:** {r['train_time_sec']:.2f}s\n")
        lines.append(f"- **Avg Inference Time:** {r['avg_inference_ms']:.4f}ms/sample\n")
        lines.append(f"- **Model Size:** {r['model_size_mb']:.2f}MB\n\n")

        cm = r['confusion_matrix']
        lines.append("**Confusion Matrix:**\n```\n")
        lines.append(str(np.array(cm)) + "\n```\n\n")

    # Best model
    best_f1 = max(results, key=lambda x: x['f1_score'])
    best_auc = max(results, key=lambda x: x['roc_auc'] if x['roc_auc'] else 0)
    fastest = min(results, key=lambda x: x['avg_inference_ms'])

    lines.append("## Best Model Recommendations\n\n")
    lines.append(f"- **Best F1-Score:** {best_f1['model_name'].replace('_', ' ').title()} ({best_f1['f1_score']*100:.2f}%)\n")
    lines.append(f"- **Best ROC AUC:** {best_auc['model_name'].replace('_', ' ').title()} ({best_auc['roc_auc']:.4f})\n")
    lines.append(f"- **Fastest Inference:** {fastest['model_name'].replace('_', ' ').title()} ({fastest['avg_inference_ms']:.4f}ms)\n")

    filepath = eval_path / "baseline_models_report.md"
    with open(filepath, 'w') as f:
        f.write(''.join(lines))
    print(f"Saved: {filepath}")


def save_models(models, eval_path):
    """Save trained model artifacts."""
    print("\n" + "="*80)
    print("SAVING MODEL ARTIFACTS")
    print("="*80)

    for name, model in models.items():
        filepath = MODEL_PATH / f"{name}_ids_synthetic.pkl"
        with open(filepath, 'wb') as f:
            pickle.dump(model, f)
        size_mb = filepath.stat().st_size / (1024 * 1024)
        print(f"  Saved: {filepath} ({size_mb:.2f}MB)")


def main():
    print("\n" + "="*80)
    print("SYNTHETIC EVALUATION PIPELINE - IDS BASELINE MODELS")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Output: {EVAL_PATH}")

    pipeline_start = time.time()

    # Generate data
    df = generate_synthetic_ids_data()

    X = df.drop('Label', axis=1).values
    y_raw = df['Label'].values

    le = LabelEncoder()
    y = le.fit_transform(y_raw)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    print(f"\nTrain: {X_train.shape[0]:,} | Test: {X_test.shape[0]:,}")

    # Train and evaluate
    models, results = train_and_evaluate(X_train, X_test, y_train, y_test, le)

    # Save all artifacts
    save_confusion_matrices(results, y_test, EVAL_PATH)
    save_normalized_confusion_matrices(results, EVAL_PATH)
    save_roc_curves(results, y_test, EVAL_PATH)
    save_precision_recall_curves(results, y_test, EVAL_PATH)
    save_model_comparison_chart(results, EVAL_PATH)
    save_metrics_json(results, y_test, EVAL_PATH)
    save_classification_reports(results, EVAL_PATH)
    save_markdown_report(results, EVAL_PATH)
    save_models(models, EVAL_PATH)

    elapsed = time.time() - pipeline_start
    print("\n" + "="*80)
    print(f"PIPELINE COMPLETE - {elapsed:.2f}s")
    print(f"All artifacts saved to: {EVAL_PATH}")
    print("="*80)


if __name__ == "__main__":
    main()
