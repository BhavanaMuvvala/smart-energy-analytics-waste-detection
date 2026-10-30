# Data dictionary

All identifiers are immutable text primary keys unless noted; `*_id` references are foreign keys to the corresponding named entity. Blank `effective_to` means active indefinitely. All timestamps are UTC ISO8601; timestamps must be ordered, rates and energy nonnegative, and `status` values constrained by the documented lifecycle.

| Entity | Fields (type; required unless marked optional) | Validation |
|---|---|---|
| Plant | plant_id TEXT, name TEXT, timezone TEXT, status TEXT | Unique ID; status active/inactive |
| Meter | meter_id TEXT, plant_id TEXT FK, unit TEXT, cadence_minutes INT, status TEXT | Unique ID; unit=kWh; cadence=15 |
| Machine | machine_id TEXT, plant_id TEXT FK, name TEXT, rated_kw REAL, status TEXT | rated_kw>0 |
| MeterMachine | assignment_id TEXT, meter_id TEXT FK, machine_id TEXT FK, effective_from TIMESTAMP, effective_to TIMESTAMP optional | no overlapping assignment for a meter |
| EnergyReading | reading_id TEXT, meter_id TEXT FK, machine_id TEXT FK, timestamp TIMESTAMP, power_kw REAL, energy_kwh REAL, state TEXT, batch_id TEXT optional FK, issue_type TEXT optional | normal reading ID unique; deliberate duplicate labelled; running/idle; kWh≈kW×0.25 |
| ProductionBatch | batch_id TEXT, machine_id TEXT FK, shift_id TEXT FK, start_at TIMESTAMP, end_at TIMESTAMP, output_units REAL, status TEXT | end>start; output_units>=0; completed/planned/cancelled |
| Shift | shift_id TEXT, plant_id TEXT FK, name TEXT, start_hour INT, end_hour INT | hours 0–23; overnight allowed |
| Tariff | tariff_id TEXT, plant_id TEXT FK, start_hour INT, end_hour INT, rate_per_kwh REAL, timezone TEXT, effective_from TIMESTAMP, effective_to TIMESTAMP | hours 0–24, rate>=0, no overlap |
| WeatherObservation | weather_id TEXT, plant_id TEXT FK, timestamp TIMESTAMP, temperature_c REAL | plausible temperature -40 to 60°C |
| MaintenanceEvent | event_id TEXT, machine_id TEXT FK, timestamp TIMESTAMP, event_type TEXT, details TEXT | event_type inspection/repair/failure |
| Recommendation | recommendation_id TEXT, meter_id TEXT FK, issue_type TEXT, baseline_kwh REAL, expected_savings_kwh REAL, rate_per_kwh REAL, expected_savings_cost REAL, evidence_id TEXT, status TEXT | nonnegative savings, proposed/approved/rejected/implemented |
| MeterSummary | summary_id TEXT, meter_id TEXT FK, day DATE, reported_kwh REAL | meter/day unique; reconciled to interval sum |
| StateEvent | state_event_id TEXT, machine_id TEXT FK, timestamp TIMESTAMP, old_state TEXT optional, new_state TEXT | append-only state transitions |

Relationships: Plant 1:N Meter/Machine/Shift/Tariff/WeatherObservation; Meter N:M Machine through MeterMachine; Meter 1:N EnergyReading/MeterSummary/Recommendation; Machine 1:N ProductionBatch/MaintenanceEvent/StateEvent; Shift 1:N ProductionBatch. EnergyReading N:1 optional ProductionBatch. Time-effective assignments are resolved at reading timestamps.
