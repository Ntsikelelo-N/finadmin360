# Model Card: Payment Delay Classifier v1.0

## Model details

- **Model type:** Gradient Boosting Classifier (scikit-learn GradientBoostingClassifier)
- **Task:** Binary classification — predict whether a supplier invoice will be paid late
- **Output:** Probability score (0–1). Score > 0.5 = predicted late payment.
- **Training date:** [Fill in your actual date]
- **Author:** [Your name]
- **MLflow experiment:** payment-delay-prediction

## Problem definition

The finance administrator needs to know — at the time an invoice arrives —
which invoices carry the highest risk of being paid late. This allows proactive
follow-up before the due date rather than reactive chasing after the fact.

## Training data

- 2 000 synthetic South African supplier invoices spanning 24 months
- Augmented with Kaggle invoice dataset
- 80/20 train/test stratified split (stratified on the is_late target)
- **IMPORTANT:** This model is trained on synthetic data only.
  It must be retrained on real historical data before use in a production environment.
  Performance on real data will differ from these metrics.

## Performance metrics (on held-out test set)

[REPLACE THESE WITH YOUR ACTUAL NUMBERS FROM MLFLOW]

| Metric | Value |
|---|---|
| Test AUC | 0.87 |
| CV AUC (5-fold mean ± std) | 0.85 ± 0.03 |
| Precision (Late class) | 0.79 |
| Recall (Late class) | 0.74 |
| F1-score (Late class) | 0.76 |
| Accuracy | 0.82 |

## Top features by importance

1. Supplier historical late payment rate (most important)
2. Log-transformed invoice amount
3. Supplier payment terms (days)
4. Invoice month (seasonality)
5. Supplier category

## Limitations

- Requires a minimum of 5 prior invoices from a supplier for reliable prediction.
  New suppliers are flagged as "insufficient history" and excluded from scoring.
- Does not account for macroeconomic events (e.g. load-shedding impact, economic downturns).
- Performance may degrade as the supplier base or payment behaviour changes over time.
  Schedule quarterly retraining.
- Trained on synthetic data — real-world performance will differ.

## Ethical considerations

- No personal data is used — only supplier-level aggregate statistics
- Protected characteristics (race, gender, location) are not used as features
- The model is a decision-support tool only — not an automated decision-maker
- Finance administrator reviews all model flags before any action is taken
- Suppliers have the right to request human review of any model-driven recommendation

## Intended use and misuse

**Intended use:** Prioritisation of invoice follow-up by the finance administrator.

**Must NOT be used for:**
- Automatically blocking or delaying payments without human review
- Credit decisions about suppliers
- Any purpose that affects a natural person without disclosure
