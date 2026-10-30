# Smart Energy Analytics & Waste Detection

A reproducible, fully synthetic manufacturing energy analytics system built using Python, SQL, and Streamlit.

The project generates industrial energy telemetry, production records, weather observations, electricity tariffs, and machine lifecycle events. It identifies energy waste and data-quality anomalies, evaluates detection performance against separate ground-truth labels, and presents energy analytics through an interactive dashboard.

**Project type:** Synthetic-data analytics prototype  
**Dataset:** 20 meters, 90 days, 15-minute intervals  
**Technology:** Python, Pandas, SQLite, Streamlit, Pytest  
**Data source:** Fully synthetic; no external datasets

> **Disclaimer:** This project is a demonstration prototype and is not intended for real industrial control or operational decisions.

## 1. Project Objectives

The project aims to:

- Generate realistic, reproducible industrial energy data.
- Model relationships between plants, meters, machines, production batches, shifts, tariffs, and weather.
- Detect energy waste and data-quality issues.
- Validate power-to-energy conversions and meter-machine assignments.
- Reconcile interval readings against reported daily meter totals.
- Generate recommendations with estimated energy and cost savings where supported.
- Evaluate anomaly detection using independent ground-truth labels.
- Visualize energy consumption and production efficiency.

## 2. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Synthetic data generation and anomaly detection |
| Pandas | Data processing and analysis |
| CSV and JSON | Dataset storage and metadata |
| SQLite | Relational schema definition |
| Streamlit | Interactive analytics dashboard |
| Pytest | Automated testing |
| Git and GitHub | Version control and project submission |

## 3. Project Structure

```text
smart-energy-analytics/
│
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
│
├── src/
│   ├── generator.py
│   └── analyze.py
│
├── data/
│   ├── Plant.csv
│   ├── Meter.csv
│   ├── Machine.csv
│   ├── MeterMachine.csv
│   ├── EnergyReading.csv
│   ├── ProductionBatch.csv
│   ├── Shift.csv
│   ├── Tariff.csv
│   ├── WeatherObservation.csv
│   ├── MaintenanceEvent.csv
│   ├── Recommendation.csv
│   ├── MeterSummary.csv
│   ├── StateEvent.csv
│   ├── ground_truth.csv
│   ├── ground_truth.json
│   ├── source_manifest.json
│   └── checksums.json
│
├── sql/
│   └── schema.sql
│
├── docs/
│   ├── data_dictionary.md
│   └── validation_summary.md
│
└── tests/
    └── test_project.py
```

## 4. Installation and Setup

### Prerequisites

- Python 3.10 or later
- pip
- Git (optional for local execution)

### Step 1: Clone the repository

```bash
git clone https://github.com/BhavanaMuvvala/smart-energy-analytics-waste-detection.git
cd smart-energy-analytics-waste-detection
```

### Step 2: Create a virtual environment

On Windows:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

On macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### Step 3: Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 4: Generate the dataset

```bash
python -m src.generator --out data --meters 20 --days 90 --batches 2000 --seed 20261022
```

This generates the synthetic datasets, ground-truth labels, metadata, and checksums.

### Step 5: Run anomaly detection

```bash
python -m src.analyze --data data
```

### Step 6: Run automated tests

```bash
python -m pytest -q
```

### Step 7: Launch the dashboard

```bash
python -m streamlit run app.py
```

Open the local URL displayed in the terminal, usually `http://localhost:8501`.

### Optional smoke test

For a smaller dataset, run:

```bash
python -m src.generator --out data_small --meters 20 --days 9 --batches 100 --seed 20261022
```

The current anomaly configuration requires at least seven meters and nine days.

## 5. Data Model

The project contains 13 entities:

| Entity | Purpose |
|---|---|
| Plant | Manufacturing facility information |
| Meter | Energy meter details |
| Machine | Manufacturing equipment and rated power |
| MeterMachine | Time-effective meter-to-machine assignments |
| EnergyReading | Interval-level energy and power measurements |
| ProductionBatch | Production activities and output |
| Shift | Manufacturing shift schedules |
| Tariff | Time-dependent electricity rates |
| WeatherObservation | Ambient temperature observations |
| MaintenanceEvent | Equipment maintenance history |
| Recommendation | Suggested actions and estimated savings |
| MeterSummary | Reported daily energy consumption |
| StateEvent | Machine operating-state transitions |

### Entity Relationships

- One plant has multiple meters, machines, shifts, tariffs, and weather observations.
- Meters are associated with machines through the `MeterMachine` relationship table.
- One meter has multiple energy readings and daily summaries.
- One machine has multiple production batches, maintenance events, and state transitions.
- Each production batch belongs to a machine and shift.
- Energy readings may reference production batches.
- Energy readings reference their applied electricity tariffs.
- Recommendations reference meters and supporting evidence.

The SQL schema is available in `sql/schema.sql`.

Detailed field definitions and validation expectations are available in `docs/data_dictionary.md`.

## 6. Synthetic Data Generation

The dataset is generated using a deterministic random seed.

### Default Configuration

| Parameter | Value |
|---|---:|
| Plants | 1 |
| Meters | 20 |
| Machines | 21 |
| Duration | 90 days |
| Reading interval | 15 minutes |
| Expected meter intervals | 172,800 |
| Production batches | 2,000 |
| Weather observations | 8,640 |
| Daily meter summaries | 1,800 |
| Recommendations | 7 |
| Ground-truth anomaly cases | 8 |

### Generation Logic

The generator models machine energy consumption using operating state, machine-specific baseline power, ambient temperature, and seeded random variation.

A machine is considered `running` when an associated production batch is active and `idle` otherwise.

Normal running power is approximately 72% of its baseline, while idle power is approximately 12%.

Temperatures above 29°C introduce an additional cooling-related load.

Weather observations follow daily and seasonal patterns with seeded random noise.

All generated timestamps use UTC ISO 8601 format.

## 7. Energy Calculations

Power is measured in kilowatts (kW).

Energy consumption is measured in kilowatt-hours (kWh).

The relationship is:

**Energy (kWh) = Power (kW) × Duration (hours)**

For a 15-minute reading:

**Energy (kWh) = Power (kW) × 0.25**

For example, a machine consuming 20 kW over 15 minutes uses:

`20 × 0.25 = 5 kWh`

The anomaly detector uses this relationship to identify inconsistent energy measurements.

## 8. Anomaly Detection

The generator deliberately injects eight anomaly cases.

| Anomaly | Description | Detection Approach |
|---|---|---|
| Meter gap | Missing 15-minute reading | Compare actual timestamps with expected intervals |
| Peak spike | Excessive instantaneous power demand | Check against a configured power threshold |
| High idle | Excessive energy consumption during idle state | Check idle-state power against a threshold |
| Unit confusion | kW value incorrectly recorded as kWh | Compare energy with power × interval duration |
| Hierarchy violation | Reading references an incorrectly assigned machine | Validate effective meter-machine assignment |
| Duplicate reading | Repeated meter/timestamp record | Detect duplicate interval keys |
| Tariff mismatch | Incorrect tariff assigned to a reading | Compare applied tariff with expected tariff window |
| Meter total mismatch | Incorrect reported daily energy total | Reconcile reported and calculated daily consumption |

### Independent Detection

Anomaly labels are stored in:

- `data/ground_truth.csv`
- `data/ground_truth.json`

The `EnergyReading.csv` file does not contain an `issue_type` column.

The detector identifies anomalies from operational measurements, timestamps, relationships, and tariff assignments rather than reading ground-truth labels.

### Tariff Validation Limitation

The detector checks whether an energy reading's `applied_tariff_id` matches the expected tariff for its timestamp.

The injected case is labelled `tariff_timezone_mismatch`, but the current implementation establishes only that the tariff assignment is incorrect. It does not independently prove that a timezone conversion caused the error.

## 9. Evaluation Results

The anomaly detector was evaluated against the eight deliberately injected ground-truth cases.

### Verified Results

```json
{
  "ground_truth": 8,
  "predictions": 8,
  "true_positive": 8,
  "false_positive": 0,
  "false_negative": 0,
  "precision": 1.0,
  "recall": 1.0,
  "f1": 1.0
}
```

| Metric | Result |
|---|---:|
| Ground-truth anomalies | 8 |
| Correct detections | 8 |
| False positives | 0 |
| False negatives | 0 |
| Precision | 100% |
| Recall | 100% |
| F1-score | 100% |

These results apply to the eight injected synthetic anomaly cases. They do not demonstrate equivalent accuracy on unseen industrial datasets.

## 10. Energy Waste Recommendations

The project generates seven recommendations associated with the injected meter-level anomaly cases.

Recommendations include:

- Issue type
- Meter identifier
- Evidence reading identifier
- Baseline energy consumption
- Estimated avoidable energy
- Applicable electricity tariff
- Estimated monetary savings
- Recommendation status

Estimated savings cost is calculated as:

**Expected savings cost = Expected savings (kWh) × Tariff rate**

The current implementation quantifies an estimated avoidable energy amount for the high-idle anomaly.

Other anomaly types use zero direct energy savings rather than assuming that correcting a data-quality issue necessarily reduces energy consumption.

Savings are illustrative estimates and have not been validated through real operational interventions.

## 11. Interactive Dashboard

The Streamlit dashboard provides visual summaries of the generated dataset.

Its features include:

- Daily energy consumption trends
- Meter-wise energy consumption
- Production energy intensity
- Energy waste recommendations

Production energy intensity is calculated as energy consumed divided by production output.

Run the dashboard using:

```bash
python -m streamlit run app.py
```

## 12. Reproducibility

The generator accepts configurable parameters for meters, days, batches, and random seed.

The default seed is `20261022`.

To verify reproducibility, generate the same dataset twice:

```bash
python -m src.generator --out data_run1 --meters 20 --days 90 --batches 2000 --seed 20261022
python -m src.generator --out data_run2 --meters 20 --days 90 --batches 2000 --seed 20261022
```

Then compare the generated checksums:

```python
import json
from pathlib import Path

first = json.loads(
    Path("data_run1/checksums.json").read_text()
)

second = json.loads(
    Path("data_run2/checksums.json").read_text()
)

print("REPRODUCIBILITY:", "PASS" if first == second else "FAIL")
```

### Verified Reproducibility Result

```text
REPRODUCIBILITY: PASS
Files compared: 14
```

The generator also creates:

- `source_manifest.json` containing generation parameters and record counts.
- `checksums.json` containing SHA-256 checksums of the generated CSV files.

## 13. Automated Testing

Automated tests are located in `tests/test_project.py`.

Run:

```bash
python -m pytest -q
```

Verified result:

```text
2 passed
```

These tests provide basic regression coverage. They do not establish that all database constraints, lifecycle rules, or data-quality requirements have been exhaustively validated.

## 14. Known Limitations

This project is a synthetic-data analytics prototype with the following limitations:

1. The dataset is fully synthetic and does not represent actual industrial measurements.
2. Peak-spike and high-idle detection use fixed thresholds rather than adaptive machine-specific baselines.
3. The tariff check detects incorrect assignments but cannot independently identify timezone conversion as the root cause.
4. Meter-total reconciliation skips days containing missing intervals or invalid energy measurements.
5. Savings estimates are illustrative and are not verified operational savings.
6. Not all documented entity relationships and lifecycle rules are enforced through automated tests.
7. Energy allocation to overlapping production activity is simplified.
8. The project does not provide real-time industrial monitoring or plant-control functionality.

## 15. Data Provenance

All data is generated synthetically using Python.

No private industrial records, third-party datasets, or external telemetry sources are used.

The generator uses a fixed random seed to support reproducibility.

Ground-truth labels are maintained separately from the operational data used by the anomaly detector.

## 16. Future Improvements

Potential enhancements include:

- Machine-specific adaptive anomaly thresholds
- Independent timezone conversion validation
- Expanded foreign-key and lifecycle integrity tests
- Improved meter-to-batch energy allocation
- More detailed tariff-based cost analysis
- Additional energy-efficiency recommendations
- Larger-scale synthetic anomaly scenarios
- Real-time telemetry ingestion
- More comprehensive anomaly detection evaluation

---

**Project Status:** Functional synthetic-data analytics prototype with verified deterministic generation, eight detected injected anomalies, two passing automated tests, and a working local Streamlit dashboard.