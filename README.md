# Smart Energy Analytics & Waste Detection

A reproducible, fully synthetic manufacturing energy telemetry challenge implementation. **Prototype:** not intended for real plant control decisions.

## Setup (Python 3.10+)

```bash
pip install -r requirements.txt
python -m src.generator --out data --meters 20 --days 90 --batches 2000 --seed 20261022
python -m src.analyze --data data
pytest -q
streamlit run app.py
```

For a fast smoke test use `--meters 20 --days 9 --batches 100`. Data generation may take a few seconds and produces >170,000 interval records at full scale.

## Model

Plant 1:N Meter, Machine, Shift, Tariff and WeatherObservation. Meter 1:N EnergyReading, Meter 1:N MeterSummary. Meter N:M Machine through MeterMachine with effective dates. Machine 1:N ProductionBatch, MaintenanceEvent and StateEvent. Shift 1:N ProductionBatch. EnergyReading optionally references ProductionBatch. Recommendation references Meter and source evidence. All timestamps UTC ISO8601. Power in kW, energy in kWh, cadence 15 minutes. kWh = kW × 0.25h. Tariffs use non-overlapping UTC hour windows and USD/kWh.

## Documented synthetic generation rules

Production batches are assigned to machine-specific time windows. A machine is `running` while a batch is active and otherwise `idle`. Running load is approximately 72% of a machine-specific baseline; idle load 12%. Ambient temperature above 29°C adds cooling load. Small seeded Gaussian noise adds realistic variation. Daily weather follows a diurnal and seasonal cycle. A high-idle case, peak spike, gap, duplicate, wrong machine mapping, unit confusion, tariff mismatch flag, and mismatched reported total are injected after normal calculations. The ground-truth file is **separate** from feature files; the `issue_type` telemetry column is included as a transparency aid and is not suitable as a model feature.

## Known limitations

This is a starter implementation under a one-day deadline. The timezone mismatch flag is directly read by the detector rather than inferred from timezone metadata, so this check is **not independently validated**. Meter summary reconciliation is only checked for a documented test case. SQL DDL and detailed dictionary are included as supporting material. The recommendation savings estimates are illustrative rather than empirically validated. For production use, infer anomalies from raw telemetry and independent tariff metadata, fully reconcile each meter/day, and allocate meter-level energy to overlapping batches more precisely.

## Provenance

No third-party data, private data, or web datasets are used. All generated records are synthetic using fixed seed `20261022`. Reproducibility is verified by SHA-256 file hashes and pytest.
