# Data Dictionary

## 1. Overview

The Smart Energy Analytics & Waste Detection project generates synthetic industrial energy, production, weather, tariff, and maintenance data.

The dataset contains 13 entities, with separate ground-truth files for evaluating anomaly detection.

Identifiers are stable text keys unless otherwise specified. The `EnergyReading` SQL table uses a database-generated integer primary key (`reading_row_id`) so intentionally duplicated reading IDs can be retained for anomaly testing.

Most fields ending in `_id` represent foreign-key references to related entities. Exceptions include primary identifiers and evidence references.

All generated timestamps use UTC ISO 8601 format. Energy consumption, power, production output, and tariff rates must be nonnegative.

A blank `effective_to` value indicates an open-ended assignment.

## 2. Entity Definitions

| Entity | Fields | Validation and Business Rules |
|---|---|---|
| **Plant** | `plant_id` TEXT PK, `name` TEXT, `timezone` TEXT, `status` TEXT | Unique plant identifier; status is `active` or `inactive`. |
| **Meter** | `meter_id` TEXT PK, `plant_id` TEXT FK, `unit` TEXT, `cadence_minutes` INTEGER, `status` TEXT | Unique meter ID; unit must be `kWh`; reading cadence is 15 minutes. |
| **Machine** | `machine_id` TEXT PK, `plant_id` TEXT FK, `name` TEXT, `rated_kw` REAL, `status` TEXT | Unique machine ID; rated power must be greater than zero. |
| **MeterMachine** | `assignment_id` TEXT PK, `meter_id` TEXT FK, `machine_id` TEXT FK, `effective_from` TIMESTAMP, `effective_to` TIMESTAMP optional | Defines time-effective meter-to-machine assignments. Assignment periods for the same meter should not overlap. |
| **EnergyReading** | `reading_row_id` INTEGER SQL PK, `reading_id` TEXT, `meter_id` TEXT FK, `machine_id` TEXT FK, `timestamp` TIMESTAMP, `power_kw` REAL, `energy_kwh` REAL, `state` TEXT, `batch_id` TEXT optional FK, `applied_tariff_id` TEXT FK | Normally one reading per meter and timestamp. A deliberate duplicate is included for anomaly testing. Valid states are `running` and `idle`. Expected energy is approximately `power_kw × 0.25` for a 15-minute interval. The applied tariff must correspond to the reading timestamp. |
| **ProductionBatch** | `batch_id` TEXT PK, `machine_id` TEXT FK, `shift_id` TEXT FK, `start_at` TIMESTAMP, `end_at` TIMESTAMP, `output_units` REAL, `status` TEXT | Batch end time must be after start time. Output must be nonnegative. Supported lifecycle values include `planned`, `completed`, and `cancelled`. |
| **Shift** | `shift_id` TEXT PK, `plant_id` TEXT FK, `name` TEXT, `start_hour` INTEGER, `end_hour` INTEGER | Defines production shifts using hour boundaries. Overnight shifts are supported. |
| **Tariff** | `tariff_id` TEXT PK, `plant_id` TEXT FK, `start_hour` INTEGER, `end_hour` INTEGER, `rate_per_kwh` REAL, `timezone` TEXT, `effective_from` TIMESTAMP, `effective_to` TIMESTAMP | Tariff rates must be nonnegative. Hourly windows must be valid and should not overlap for the same plant and effective period. |
| **WeatherObservation** | `weather_id` TEXT PK, `plant_id` TEXT FK, `timestamp` TIMESTAMP, `temperature_c` REAL | Stores synthetic ambient temperature observations. A plausible temperature range is −40°C to 60°C. |
| **MaintenanceEvent** | `event_id` TEXT PK, `machine_id` TEXT FK, `timestamp` TIMESTAMP, `event_type` TEXT, `details` TEXT | Records maintenance activities such as inspection, repair, or failure. |
| **Recommendation** | `recommendation_id` TEXT PK, `meter_id` TEXT FK, `issue_type` TEXT, `baseline_kwh` REAL, `expected_savings_kwh` REAL, `rate_per_kwh` REAL, `expected_savings_cost` REAL, `evidence_id` TEXT, `status` TEXT | Savings must be nonnegative. Supported recommendation statuses include `proposed`, `approved`, `rejected`, and `implemented`. |
| **MeterSummary** | `summary_id` TEXT PK, `meter_id` TEXT FK, `day` DATE, `reported_kwh` REAL | One summary per meter per day. Reported consumption is compared with aggregated interval readings. |
| **StateEvent** | `state_event_id` TEXT PK, `machine_id` TEXT FK, `timestamp` TIMESTAMP, `old_state` TEXT optional, `new_state` TEXT | Records machine state transitions. Events are append-only in the generated dataset. |

**Note:** `reading_row_id` is defined in the SQL schema but is not included in `EnergyReading.csv`. It is generated when records are inserted into the database.

## 3. Entity Relationships

The dataset uses the following relationships:

- **Plant → Meter:** One plant can have multiple meters.
- **Plant → Machine:** One plant can contain multiple machines.
- **Plant → Shift:** One plant can define multiple production shifts.
- **Plant → Tariff:** One plant can have multiple electricity tariffs.
- **Plant → WeatherObservation:** One plant can have multiple weather observations.
- **Meter ↔ Machine:** A meter is associated with machines through the `MeterMachine` relationship table.
- **Meter → EnergyReading:** One meter produces multiple energy readings.
- **Meter → MeterSummary:** One meter has multiple daily consumption summaries.
- **Meter → Recommendation:** One meter can have multiple recommendations.
- **Machine → ProductionBatch:** One machine can execute multiple production batches.
- **Machine → MaintenanceEvent:** One machine can have multiple maintenance events.
- **Machine → StateEvent:** One machine can have multiple state transitions.
- **Shift → ProductionBatch:** One shift can contain multiple production batches.
- **ProductionBatch → EnergyReading:** A production batch can be associated with multiple energy readings.
- **Tariff → EnergyReading:** Each generated energy reading references an applied tariff through `applied_tariff_id`.

Meter-machine relationships are validated using the reading timestamp and the assignment's effective dates.

## 4. Energy Measurement Rules

Energy readings are generated at 15-minute intervals.

The expected relationship between power and energy is:

**Energy (kWh) = Power (kW) × Time (hours)**

For a 15-minute interval:

**Energy (kWh) = Power (kW) × 0.25**

Example:

If a machine consumes 20 kW for 15 minutes:

`20 × 0.25 = 5 kWh`

The anomaly detector compares reported energy against the calculated value using a numerical tolerance.

## 5. Tariff Validation

Electricity tariffs contain:

- A tariff identifier.
- A plant identifier.
- A start hour and end hour.
- A rate per kWh.
- A timezone.
- Effective start and end timestamps.

Each energy reading contains an `applied_tariff_id`.

The anomaly detector calculates the expected tariff using the reading timestamp and the tariff's effective period and hourly window.

If the applied tariff differs from the expected tariff, the reading is flagged as `tariff_timezone_mismatch`.

**Limitation:** The current implementation detects an incorrect tariff assignment. It does not independently establish that a timezone conversion caused the discrepancy. The generated dataset uses UTC timestamps and UTC tariffs.

## 6. Injected Data Anomalies

The generator deliberately introduces eight ground-truth anomaly cases.

| Anomaly | Description | Detection Method |
|---|---|---|
| `meter_gap` | A scheduled meter reading is missing. | Compare observed timestamps against the expected 15-minute cadence. |
| `peak_spike` | A machine experiences unusually high power demand. | Flag readings exceeding the configured peak-power threshold. |
| `high_idle` | A machine consumes excessive power while idle. | Compare idle-state power with the configured threshold. |
| `unit_confusion` | An energy value incorrectly uses the power value. | Validate `energy_kwh ≈ power_kw × 0.25`. |
| `hierarchy_violation` | A reading references a machine not assigned to its meter. | Validate the meter-machine relationship at the reading timestamp. |
| `duplicate_reading` | A meter reading is intentionally duplicated. | Identify repeated meter/timestamp combinations. |
| `tariff_timezone_mismatch` | A reading is assigned an incorrect tariff. | Compare the applied tariff against the expected tariff window. |
| `meter_total_mismatch` | A daily reported total differs from the sum of interval readings. | Reconcile daily totals against recorded interval consumption. |

The injected anomaly labels are stored separately from the energy readings.

## 7. Ground-Truth Files

The project generates two ground-truth files:

- `ground_truth.csv`
- `ground_truth.json`

Each ground-truth record contains:

| Field | Description |
|---|---|
| `issue_type` | Type of injected anomaly. |
| `record_id` | Identifier of the affected reading or summary. |
| `meter_id` | Meter associated with the anomaly. |
| `timestamp` | Timestamp or date associated with the anomaly. |
| `expected_action` | Suggested action for handling the anomaly. |

Ground-truth labels are not included in `EnergyReading.csv`.

The anomaly detector uses the generated operational data and validation rules rather than directly reading the labels.

Ground-truth files are used during evaluation to calculate precision, recall, and F1-score.

## 8. Recommendations and Estimated Savings

The `Recommendation` entity stores suggested actions based on identified energy or data-quality issues.

The main financial fields are:

| Field | Description |
|---|---|
| `baseline_kwh` | Energy consumption used as the reference for an estimate. |
| `expected_savings_kwh` | Estimated avoidable energy consumption. |
| `rate_per_kwh` | Applicable electricity tariff rate. |
| `expected_savings_cost` | Estimated monetary savings. |
| `evidence_id` | Identifier of the supporting energy reading. |
| `status` | Recommendation lifecycle status. |

Estimated monetary savings are calculated as:

**Expected savings cost = Expected savings (kWh) × Tariff rate**

The current generator calculates an estimated avoidable energy amount for the injected high-idle event.

Other recommendation types use zero direct energy savings rather than assuming that every data-quality correction reduces consumption.

These estimates are illustrative and are not verified savings from implemented operational changes.

## 9. Data Integrity and Validation

The project defines the following validation expectations:

1. Primary identifiers should be unique, except for the intentionally duplicated `reading_id`.
2. Foreign-key references should identify existing entities.
3. Meter-machine assignments should be valid for their effective periods.
4. Energy readings should follow the configured 15-minute cadence.
5. Power and energy measurements should be nonnegative.
6. Production batch end timestamps should be later than start timestamps.
7. Tariff windows should not overlap for the same effective period.
8. Daily meter totals should reconcile with interval-level consumption.
9. Machine state transitions should remain chronologically ordered.
10. Repeated generation with identical inputs should produce identical CSV outputs.

The dataset deliberately violates selected expectations to test anomaly detection. These violations are documented in the separate ground-truth files.

**Validation scope:** These are data-quality rules and expectations. Not every rule is currently enforced by a database constraint or automated test.

## 10. Reproducibility

The dataset is generated using a fixed random seed.

Example command:

```bash
python -m src.generator --out data --meters 20 --days 90 --batches 2000 --seed 20261022
```

The default configuration generates:

| Dataset | Record Count |
|---|---:|
| Plant | 1 |
| Meter | 20 |
| Machine | 21 |
| MeterMachine | 20 |
| Shift | 3 |
| Tariff | 4 |
| WeatherObservation | 8,640 |
| ProductionBatch | 2,000 |
| EnergyReading | 172,800 |
| MaintenanceEvent | 1 |
| Recommendation | 7 |
| MeterSummary | 1,800 |
| StateEvent | 4,019 |

The generated outputs also include:

- `source_manifest.json` — Generation parameters and record counts.
- `checksums.json` — SHA-256 checksums for generated CSV files.
- `ground_truth.csv` — Injected anomaly labels.
- `ground_truth.json` — JSON representation of injected anomalies.

Two independent runs using the same seed and parameters produced matching checksums for all 14 generated CSV files.

## 11. Anomaly Detection Evaluation

Run the anomaly detector using:

```bash
python -m src.analyze --data data
```

The verified results for the default synthetic dataset are:

| Metric | Result |
|---|---:|
| Ground-truth anomalies | 8 |
| Predictions | 8 |
| True positives | 8 |
| False positives | 0 |
| False negatives | 0 |
| Precision | 1.0 |
| Recall | 1.0 |
| F1-score | 1.0 |

These results describe performance on the eight deliberately injected synthetic anomalies.

They should not be interpreted as proof of equivalent performance on unseen datasets or real industrial systems.

## 12. Known Limitations

The current implementation has several limitations:

- It uses fully synthetic data rather than real industrial measurements.
- Peak and high-idle detection rely on fixed thresholds.
- Tariff validation checks incorrect assignments but does not identify the root cause of a timezone error.
- Daily reconciliation skips days containing missing intervals or invalid energy measurements.
- Only the high-idle recommendation includes a quantified avoidable-energy estimate.
- Some lifecycle and relationship rules are documented but not fully enforced by automated tests.
- The project is a reproducible demonstration rather than a production-ready industrial monitoring system.