# Validation summary

Full dataset generated with seed 20261022: 20 meters, 90 days, 2000 batches. Expected baseline intervals: 172800. Actual reading rows: 172800 (one missing interval and one duplicate). Eight ground-truth anomalies, seven detected, precision 1.0000, recall 0.8750, F1 0.9333. The undetected case is the meter gap at the beginning of the first day: the prototype detector scans between each meter's first and last observed timestamp. This is an identified acceptance gap, not a claim of perfect coverage.

Two independent full-size generations with identical parameters produced matching CSV SHA-256 manifests. Negative scenarios are intentionally present and must not be interpreted as clean data. Further production-hardening work is required for full foreign-key audit, generalized reconciliation, independent timezone validation, and evidence-based savings estimation.
