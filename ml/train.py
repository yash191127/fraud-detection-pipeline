"""Train a supervised fraud model (Gradient Boosting) on the transactions CSV.

File location:  ml/data/creditcard.csv
Run from the project root:   python ml/train.py
Outputs:
  ml/models/fraud_model.pkl   the trained model + decision threshold
  ml/data/holdout.csv         transactions the model NEVER saw (used by producer.py)
"""
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, precision_recall_curve, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "creditcard.csv"
HOLDOUT_PATH = ROOT / "data" / "holdout.csv"
MODEL_PATH = ROOT / "models" / "fraud_model.pkl"

NUMERIC = [
    "transaction_amount", "transaction_hour", "card_present", "customer_age",
    "account_age_days", "credit_limit", "credit_score", "num_cards_held",
    "transactions_last_1h", "transactions_last_24h", "transactions_last_7d",
    "amount_last_1h", "amount_last_24h", "days_since_last_transaction",
    "distance_from_home_km", "distance_from_last_tx_km", "international_transaction",
    "high_risk_country", "amount_vs_avg_ratio", "used_chip", "used_pin", "is_weekend",
    "avg_transaction_amount_30d", "std_transaction_amount_30d",
    "num_declined_last_30d", "num_chargebacks_ever",
]
CATEGORICAL = ["merchant_category", "transaction_channel", "device_type", "email_domain"]
FEATURES = NUMERIC + CATEGORICAL
# is_fraud, fraud_type and fraud_amount_lost are answers, so they are NOT used as inputs.


def build_model() -> Pipeline:
    prep = ColumnTransformer([
        ("num", SimpleImputer(strategy="median"), NUMERIC),
        ("cat", Pipeline([
            ("fill", SimpleImputer(strategy="constant", fill_value="unknown")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), CATEGORICAL),
    ])
    return Pipeline([
        ("prep", prep),
        ("clf", HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.08, class_weight="balanced", random_state=42,
        )),
    ])


def main() -> None:
    if not DATA_PATH.exists():
        sys.exit(f"Dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df):,} transactions, {int(df['is_fraud'].sum()):,} fraud ({df['is_fraud'].mean():.2%})")

    # 70% learn, 15% choose the alert threshold, 15% final exam (never seen before)
    train, rest = train_test_split(df, test_size=0.30, stratify=df["is_fraud"], random_state=42)
    val, test = train_test_split(rest, test_size=0.50, stratify=rest["is_fraud"], random_state=42)

    model = build_model()
    model.fit(train[FEATURES], train["is_fraud"])

    # Pick the probability cut-off that gives the best balance of precision and recall.
    p_val = model.predict_proba(val[FEATURES])[:, 1]
    prec, rec, thr = precision_recall_curve(val["is_fraud"], p_val)
    f1 = 2 * prec[:-1] * rec[:-1] / np.clip(prec[:-1] + rec[:-1], 1e-9, None)
    threshold = float(thr[int(np.argmax(f1))])

    p_test = model.predict_proba(test[FEATURES])[:, 1]
    pred = (p_test >= threshold).astype(int)
    print(f"\nResults on {len(test):,} transactions the model never saw:")
    print(f"  Fraud caught (recall):       {recall_score(test['is_fraud'], pred):.1%}")
    print(f"  Flags that were real fraud:  {precision_score(test['is_fraud'], pred, zero_division=0):.1%}")
    print(f"  ROC-AUC:                     {roc_auc_score(test['is_fraud'], p_test):.3f}")
    print(f"  PR-AUC:                      {average_precision_score(test['is_fraud'], p_test):.3f}")
    print(f"  Alert threshold:             {threshold:.3f}")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "numeric": NUMERIC, "categorical": CATEGORICAL, "threshold": threshold}, MODEL_PATH)
    test.to_csv(HOLDOUT_PATH, index=False)
    print(f"\nSaved model to {MODEL_PATH}")
    print(f"Saved unseen transactions to {HOLDOUT_PATH}")


if __name__ == "__main__":
    main()
