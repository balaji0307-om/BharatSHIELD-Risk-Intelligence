"""
BharatSHIELD - End-to-end Model Training Orchestrator.

Runs the full ML pipeline:
  1. Load raw data
  2. Preprocess (clean, encode, scale)
  3. Engineer features (transaction, velocity, behavioural)
  4. Split (train / val / test - stratified)
  5. Train and compare models (LR, RF, XGBoost)
  6. Find optimal threshold
  7. Evaluate on held-out test set
  8. Serialize model + feature_config.json

Usage:
    python ml/train_model.py
    python ml/train_model.py --data-path data/raw/transactions.csv --model-dir ml/models
"""

import os
import sys
import argparse
import time
import datetime
import json
import logging

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so ml.src.* imports work regardless
# of the working directory.
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.src.data.load_data import load_dataset, get_feature_columns, get_target_column
from ml.src.data.preprocess import preprocess_data, encode_categoricals, scale_features
from ml.src.data.split_data import split_dataset
from ml.src.features.transaction_features import engineer_transaction_features
from ml.src.features.velocity_features import engineer_velocity_features
from ml.src.features.behavioural_features import engineer_behavioural_features
from ml.src.models.train import train_pipeline, save_model
from ml.src.models.evaluate import evaluate_model, find_optimal_threshold, save_evaluation_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def _section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def main() -> None:
    parser = argparse.ArgumentParser(description="BharatSHIELD Model Training Pipeline")
    parser.add_argument("--data-path", type=str, default="data/raw/transactions.csv",
                        help="Path to raw transaction CSV (relative to project root)")
    parser.add_argument("--model-dir", type=str, default="ml/models",
                        help="Directory to save trained model and config")
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    # Resolve paths relative to project root
    data_path = os.path.join(PROJECT_ROOT, args.data_path) if not os.path.isabs(args.data_path) else args.data_path
    model_dir = os.path.join(PROJECT_ROOT, args.model_dir) if not os.path.isabs(args.model_dir) else args.model_dir
    os.makedirs(model_dir, exist_ok=True)

    _section("BharatSHIELD - Model Training Pipeline")
    pipeline_start = time.time()

    # ------------------------------------------------------------------
    # Step 1: Load Data
    # ------------------------------------------------------------------
    _section("Step 1 / 8 - Loading Data")
    step_t = time.time()
    try:
        df = load_dataset(data_path)
        print(f"  Loaded {len(df):,} transactions from {data_path}")
    except (FileNotFoundError, ValueError) as exc:
        logger.warning(f"Could not load dataset ({exc}). Generating synthetic data first...")
        print("  -> Running scripts/generate_demo_data.py ...")
        gen_script = os.path.join(PROJECT_ROOT, "scripts", "generate_demo_data.py")
        os.system(f'"{sys.executable}" "{gen_script}"')
        df = load_dataset(data_path)
        print(f"  Loaded {len(df):,} transactions after generation")

    fraud_count = int(df[get_target_column()].sum())
    fraud_rate = fraud_count / len(df)
    print(f"  Fraud: {fraud_count:,} ({fraud_rate:.2%})  |  Legit: {len(df) - fraud_count:,}")
    print(f"  [Duration: {time.time() - step_t:.1f}s]")

    # ------------------------------------------------------------------
    # Step 2: Preprocess
    # ------------------------------------------------------------------
    _section("Step 2 / 8 - Preprocessing")
    step_t = time.time()
    df = preprocess_data(df)
    df = encode_categoricals(df)
    print(f"  Columns after encoding: {len(df.columns)}")
    print(f"  [Duration: {time.time() - step_t:.1f}s]")

    # ------------------------------------------------------------------
    # Step 3: Feature Engineering
    # ------------------------------------------------------------------
    _section("Step 3 / 8 - Feature Engineering")
    step_t = time.time()
    df = engineer_transaction_features(df)
    df = engineer_velocity_features(df)
    df = engineer_behavioural_features(df)
    new_cols = [c for c in df.columns if c not in get_feature_columns()]
    print(f"  Added {len(new_cols)} engineered features")
    print(f"  Total columns: {len(df.columns)}")
    print(f"  [Duration: {time.time() - step_t:.1f}s]")

    # ------------------------------------------------------------------
    # Step 4: Split
    # ------------------------------------------------------------------
    _section("Step 4 / 8 - Train / Val / Test Split")
    step_t = time.time()
    target_col = get_target_column()
    feature_cols = [c for c in df.columns
                    if c not in [target_col, "transaction_id", "merchant_id", "timestamp"]]

    X_train, X_val, X_test, y_train, y_val, y_test = split_dataset(
        df, feature_cols, target_col, test_size=0.15, val_size=0.15,
        random_state=args.random_state,
    )
    print(f"  Train: {len(X_train):,}  |  Val: {len(X_val):,}  |  Test: {len(X_test):,}")
    print(f"  Train fraud rate: {y_train.mean():.2%}")
    print(f"  [Duration: {time.time() - step_t:.1f}s]")

    # Scale features (fit on train, transform val/test)
    X_train, scaler = scale_features(X_train, feature_cols)
    X_val, _ = scale_features(X_val, feature_cols, scaler=scaler)
    X_test, _ = scale_features(X_test, feature_cols, scaler=scaler)

    # ------------------------------------------------------------------
    # Step 5: Train & Compare Models
    # ------------------------------------------------------------------
    _section("Step 5 / 8 - Training & Model Comparison")
    step_t = time.time()
    trained_feature_names = list(X_train.columns)
    best_model, comparison_results, best_model_name = train_pipeline(
        X_train, y_train, X_val, y_val, trained_feature_names, model_dir,
    )

    print("\n  Model Comparison:")
    print(f"  {'Model':<25} {'F1':>8} {'Precision':>10} {'Recall':>8} {'AUC-ROC':>8} {'Latency':>10}")
    print(f"  {'-'*25} {'-'*8} {'-'*10} {'-'*8} {'-'*8} {'-'*10}")
    for name, metrics in comparison_results.items():
        marker = " [WINNER]" if name == best_model_name else ""
        print(f"  {name:<25} {metrics['f1']:>8.4f} {metrics['precision']:>10.4f} "
              f"{metrics['recall']:>8.4f} {metrics['auc_roc']:>8.4f} "
              f"{metrics.get('inference_latency_sec', 0):>9.4f}s{marker}")
    print(f"\n  [Selected]: {best_model_name}")
    print(f"  [Duration: {time.time() - step_t:.1f}s]")

    # ------------------------------------------------------------------
    # Step 6: Optimal Threshold
    # ------------------------------------------------------------------
    _section("Step 6 / 8 - Threshold Optimization")
    step_t = time.time()
    optimal_threshold = find_optimal_threshold(best_model, X_val, y_val, metric="f1")
    print(f"  Optimal threshold (F1): {optimal_threshold:.3f}")
    print(f"  [Duration: {time.time() - step_t:.1f}s]")

    # ------------------------------------------------------------------
    # Step 7: Evaluate on Test Set
    # ------------------------------------------------------------------
    _section("Step 7 / 8 - Test-Set Evaluation")
    step_t = time.time()
    test_metrics = evaluate_model(best_model, X_test, y_test, threshold=optimal_threshold)

    print(f"\n  Precision:       {test_metrics['precision']:.4f}")
    print(f"  Recall:          {test_metrics['recall']:.4f}")
    print(f"  F1 Score:        {test_metrics['f1_score']:.4f}")
    print(f"  Accuracy:        {test_metrics['accuracy']:.4f}")
    print(f"  AUC-ROC:         {test_metrics['auc_roc']:.4f}")
    print(f"  AUC-PR:          {test_metrics['auc_pr']:.4f}")
    print(f"  False Positive:  {test_metrics['false_positive_rate']:.4f}")
    print(f"  Fraud Detection: {test_metrics['fraud_detection_rate']:.4f}")
    print(f"\n  Confusion Matrix: {test_metrics['confusion_matrix']}")
    print(f"\n{test_metrics['classification_report']}")
    print(f"  [Duration: {time.time() - step_t:.1f}s]")

    # ------------------------------------------------------------------
    # Step 8: Save Model + Config
    # ------------------------------------------------------------------
    _section("Step 8 / 8 - Saving Artifacts")
    step_t = time.time()
    model_path = os.path.join(model_dir, "fraud_model.pkl")

    feature_config = {
        "model_version": "1.0.0",
        "model_name": best_model_name,
        "training_date": datetime.datetime.now().isoformat(),
        "dataset_info": {
            "total_samples": len(df),
            "fraud_rate": float(fraud_rate),
            "train_size": len(X_train),
            "val_size": len(X_val),
            "test_size": len(X_test),
        },
        "feature_names": trained_feature_names,
        "evaluation_metrics": {
            k: v for k, v in test_metrics.items()
            if not isinstance(v, str)  # exclude classification_report string
        },
        "model_comparison": comparison_results,
        "selected_model_reason": (
            f"{best_model_name} achieved the highest F1 score ({comparison_results[best_model_name]['f1']:.4f}) "
            f"on the validation set while maintaining competitive precision/recall balance and low inference latency."
        ),
        "threshold": optimal_threshold,
    }

    save_model(best_model, model_path, feature_config)
    save_evaluation_report(test_metrics, os.path.join(model_dir, "evaluation_report.json"))

    # Also save the scaler for inference
    import joblib
    joblib.dump(scaler, os.path.join(model_dir, "scaler.pkl"))

    print(f"  Model:       {model_path}")
    print(f"  Config:      {os.path.join(model_dir, 'feature_config.json')}")
    print(f"  Scaler:      {os.path.join(model_dir, 'scaler.pkl')}")
    print(f"  Eval report: {os.path.join(model_dir, 'evaluation_report.json')}")
    print(f"  [Duration: {time.time() - step_t:.1f}s]")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    _section("TRAINING COMPLETE")
    total_time = time.time() - pipeline_start
    print(f"  Total pipeline time: {total_time:.1f}s")
    print(f"  Selected model:      {best_model_name}")
    print(f"  Optimal threshold:   {optimal_threshold:.3f}")
    print(f"  Test F1:             {test_metrics['f1_score']:.4f}")
    print(f"  Test AUC-ROC:        {test_metrics['auc_roc']:.4f}")
    print(f"  Fraud detection:     {test_metrics['fraud_detection_rate']:.4f}")
    print(f"  False positive rate: {test_metrics['false_positive_rate']:.4f}")
    print(f"\n  All artifacts saved to: {model_dir}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
