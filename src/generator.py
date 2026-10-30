import argparse
import csv
import hashlib
import json
import math
import random

from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED = 20261022
START = datetime(2026, 1, 1, tzinfo=timezone.utc)

FIELDS = {
    "Plant": ["plant_id", "name", "timezone", "status"],
    "Meter": ["meter_id", "plant_id", "unit", "cadence_minutes", "status"],
    "Machine": ["machine_id", "plant_id", "name", "rated_kw", "status"],
    "MeterMachine": [
        "assignment_id", "meter_id", "machine_id",
        "effective_from", "effective_to"
    ],
    "Shift": ["shift_id", "plant_id", "name", "start_hour", "end_hour"],
    "Tariff": [
        "tariff_id", "plant_id", "start_hour", "end_hour",
        "rate_per_kwh", "timezone", "effective_from", "effective_to"
    ],
    "WeatherObservation": [
        "weather_id", "plant_id", "timestamp", "temperature_c"
    ],
    "ProductionBatch": [
        "batch_id", "machine_id", "shift_id", "start_at",
        "end_at", "output_units", "status"
    ],
    "EnergyReading": [
        "reading_id", "meter_id", "machine_id", "timestamp",
        "power_kw", "energy_kwh", "state", "batch_id",
        "applied_tariff_id"
    ],
    "MaintenanceEvent": [
        "event_id", "machine_id", "timestamp", "event_type", "details"
    ],
    "Recommendation": [
        "recommendation_id", "meter_id", "issue_type",
        "baseline_kwh", "expected_savings_kwh", "rate_per_kwh",
        "expected_savings_cost", "evidence_id", "status"
    ],
    "MeterSummary": [
        "summary_id", "meter_id", "day", "reported_kwh"
    ],
    "StateEvent": [
        "state_event_id", "machine_id", "timestamp",
        "old_state", "new_state"
    ],
}


def write_csv(folder, name, rows):
    with (folder / (name + ".csv")).open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS[name])
        writer.writeheader()
        writer.writerows(rows)


def build(out, meters=20, days=90, batches=2000, seed=SEED):

    if meters < 7 or days < 9:
        raise ValueError(
            "This anomaly configuration requires at least "
            "7 meters and 9 days."
        )

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    interval = timedelta(minutes=15)

    plant = "PLT-001"

    plants = [{
        "plant_id": plant,
        "name": "Synthetic Assembly Plant",
        "timezone": "UTC",
        "status": "active"
    }]

    meter_ids = [
        f"MTR-{plant}-{i:03d}"
        for i in range(1, meters + 1)
    ]

    machine_ids = [
        f"MCH-{plant}-{i:03d}"
        for i in range(1, meters + 2)
    ]

    meter_rows = [
        {
            "meter_id": meter_id,
            "plant_id": plant,
            "unit": "kWh",
            "cadence_minutes": 15,
            "status": "active"
        }
        for meter_id in meter_ids
    ]

    machine_rows = [
        {
            "machine_id": machine_id,
            "plant_id": plant,
            "name": f"Assembly Machine {i}",
            "rated_kw": round(12 + (i % 6) * 3.5, 2),
            "status": "active"
        }
        for i, machine_id in enumerate(machine_ids, 1)
    ]

    assignments = [
        {
            "assignment_id": f"ASN-{i:05d}",
            "meter_id": meter_id,
            "machine_id": machine_ids[i - 1],
            "effective_from": START.isoformat(),
            "effective_to": ""
        }
        for i, meter_id in enumerate(meter_ids, 1)
    ]

    shifts = [
        {
            "shift_id": f"SHF-{i + 1}",
            "plant_id": plant,
            "name": name,
            "start_hour": start,
            "end_hour": end
        }
        for i, (name, start, end) in enumerate([
            ("Morning", 6, 14),
            ("Evening", 14, 22),
            ("Night", 22, 6)
        ])
    ]

    tariffs = [
        {
            "tariff_id": f"TAR-2026-{i:03d}",
            "plant_id": plant,
            "start_hour": start,
            "end_hour": end,
            "rate_per_kwh": rate,
            "timezone": "UTC",
            "effective_from": START.isoformat(),
            "effective_to": (
                START + timedelta(days=days)
            ).isoformat()
        }
        for i, (start, end, rate) in enumerate([
            (0, 6, 0.09),
            (6, 17, 0.14),
            (17, 22, 0.24),
            (22, 24, 0.11)
        ], 1)
    ]

    def shift_for(dt):
        if 6 <= dt.hour < 14:
            return "SHF-1"
        if 14 <= dt.hour < 22:
            return "SHF-2"
        return "SHF-3"

    def tariff_for(dt):
        return next(
            t for t in tariffs
            if int(t["start_hour"]) <= dt.hour < int(t["end_hour"])
        )

    total_intervals = days * 96

    batch_rows = []
    batch_at = {}

    for i in range(batches):

        idx = min(
            total_intervals - 2,
            (i * total_intervals) // max(1, batches)
        )

        machine_index = i % meters
        dt = START + idx * interval
        end = dt + timedelta(hours=1)

        batch_id = f"BATCH-2026-{i + 1:06d}"

        batch_rows.append({
            "batch_id": batch_id,
            "machine_id": machine_ids[machine_index],
            "shift_id": shift_for(dt),
            "start_at": dt.isoformat(),
            "end_at": end.isoformat(),
            "output_units": round(35 + 20 * rng.random(), 2),
            "status": "completed"
        })

        for step in range(4):
            batch_at[(machine_index, idx + step)] = batch_id

    weather = []

    for idx in range(total_intervals):

        dt = START + idx * interval

        temperature = round(
            23
            + 7 * math.sin(2 * math.pi * (dt.hour - 8) / 24)
            + 3 * math.sin(
                2 * math.pi * dt.timetuple().tm_yday / 365
            )
            + rng.gauss(0, 0.5),
            2
        )

        weather.append({
            "weather_id": f"WTH-{idx + 1:07d}",
            "plant_id": plant,
            "timestamp": dt.isoformat(),
            "temperature_c": temperature
        })

    readings = []
    summaries = []
    events = []
    truth = []
    recommendations = []

    # Deliberate synthetic anomaly locations
    gap = (0, 10)
    spike = (1, 120)
    idle = (2, 250)
    unit = (3, 400)
    hierarchy = (4, 550)
    duplicate = (5, 700)
    timezone_error = (6, 800)

    anomaly_points = {
        "meter_gap": gap,
        "peak_spike": spike,
        "high_idle": idle,
        "unit_confusion": unit,
        "hierarchy_violation": hierarchy,
        "duplicate_reading": duplicate,
        "tariff_timezone_mismatch": timezone_error
    }

    for machine_index, meter_id in enumerate(meter_ids):

        daily = {}
        previous_state = ""

        for idx in range(total_intervals):

            dt = START + idx * interval
            day = dt.date().isoformat()

            batch_id = batch_at.get(
                (machine_index, idx), ""
            )

            state = "running" if batch_id else "idle"

            if state != previous_state:

                events.append({
                    "state_event_id": (
                        f"STE-{len(events) + 1:08d}"
                    ),
                    "machine_id": machine_ids[machine_index],
                    "timestamp": dt.isoformat(),
                    "old_state": previous_state,
                    "new_state": state
                })

                previous_state = state

            base = 12 + (machine_index % 6) * 3.5

            temperature = float(
                weather[idx]["temperature_c"]
            )

            power_kw = max(
                0.2,
                base * (0.72 if batch_id else 0.12)
                + max(temperature - 29, 0) * 0.12
                + rng.gauss(0, 0.45)
            )

            # Inject a measurable peak demand spike
            if (machine_index, idx) == spike:
                power_kw = max(70.0, base * 3.8)

            # Inject excessive idle consumption
            if (machine_index, idx) == idle:
                power_kw = base * 0.95

            energy_kwh = round(power_kw * 0.25, 5)
            power_kw = round(power_kw, 5)

            reading_id = (
                f"ENG-{meter_id}-"
                f"{dt.strftime('%Y%m%dT%H%M%SZ')}"
            )

            daily[day] = daily.get(day, 0) + energy_kwh

            # Missing interval
            if (machine_index, idx) == gap:

                truth.append({
                    "issue_type": "meter_gap",
                    "record_id": reading_id,
                    "meter_id": meter_id,
                    "timestamp": dt.isoformat(),
                    "expected_action": "flag_missing_interval"
                })

                continue

            machine_id = machine_ids[machine_index]
            measured_energy = energy_kwh

            # kW/kWh confusion
            if (machine_index, idx) == unit:
                measured_energy = power_kw

            # Invalid meter-machine relationship
            if (machine_index, idx) == hierarchy:
                machine_id = machine_ids[-1]

            applied_tariff = tariff_for(dt)["tariff_id"]

            # Simulate incorrect tariff-window assignment.
            # This is independently detectable from UTC time.
            if (machine_index, idx) == timezone_error:

                if applied_tariff != tariffs[0]["tariff_id"]:
                    applied_tariff = tariffs[0]["tariff_id"]
                else:
                    applied_tariff = tariffs[-1]["tariff_id"]

            row = {
                "reading_id": reading_id,
                "meter_id": meter_id,
                "machine_id": machine_id,
                "timestamp": dt.isoformat(),
                "power_kw": power_kw,
                "energy_kwh": measured_energy,
                "state": state,
                "batch_id": batch_id,
                "applied_tariff_id": applied_tariff
            }

            readings.append(row)

            anomaly_labels = {
                spike: "peak_spike",
                idle: "high_idle",
                unit: "unit_confusion",
                hierarchy: "hierarchy_violation",
                timezone_error: "tariff_timezone_mismatch"
            }

            if (machine_index, idx) in anomaly_labels:

                truth.append({
                    "issue_type": anomaly_labels[
                        (machine_index, idx)
                    ],
                    "record_id": reading_id,
                    "meter_id": meter_id,
                    "timestamp": dt.isoformat(),
                    "expected_action": "investigate_and_correct"
                })

            # Duplicate reading
            if (machine_index, idx) == duplicate:

                readings.append(dict(row))

                truth.append({
                    "issue_type": "duplicate_reading",
                    "record_id": reading_id,
                    "meter_id": meter_id,
                    "timestamp": dt.isoformat(),
                    "expected_action": "deduplicate"
                })

        for day, total in sorted(daily.items()):

            reported = round(total, 5)

            # Deliberate mismatch on a separate day
            if (
                machine_index == 0
                and day == (
                    START + timedelta(days=2)
                ).date().isoformat()
            ):

                reported = round(reported + 10, 5)

                truth.append({
                    "issue_type": "meter_total_mismatch",
                    "record_id": f"SUM-{meter_id}-{day}",
                    "meter_id": meter_id,
                    "timestamp": day,
                    "expected_action": "reconcile_meter_total"
                })

            summaries.append({
                "summary_id": f"SUM-{meter_id}-{day}",
                "meter_id": meter_id,
                "day": day,
                "reported_kwh": reported
            })

    # Recommendations
    for i, (label, point) in enumerate(
        anomaly_points.items(), 1
    ):

        machine_index, idx = point

        if machine_index >= meters or idx >= total_intervals:
            continue

        dt = START + idx * interval

        reading_id = (
            f"ENG-{meter_ids[machine_index]}-"
            f"{dt.strftime('%Y%m%dT%H%M%SZ')}"
        )

        baseline = 0.0
        savings = 0.0

        tariff_rate = float(
            tariff_for(dt)["rate_per_kwh"]
        )

        # Quantified savings for excessive idle load
        if label == "high_idle":

            actual = next(
                float(row["energy_kwh"])
                for row in readings
                if row["reading_id"] == reading_id
            )

            normal_idle = round(
                (
                    12 + (machine_index % 6) * 3.5
                ) * 0.12 * 0.25,
                5
            )

            baseline = round(actual, 4)

            savings = round(
                max(0.0, actual - normal_idle),
                4
            )

        recommendations.append({
            "recommendation_id": (
                f"REC-2026-{i:06d}"
            ),
            "meter_id": meter_ids[machine_index],
            "issue_type": label,
            "baseline_kwh": baseline,
            "expected_savings_kwh": savings,
            "rate_per_kwh": tariff_rate,
            "expected_savings_cost": round(
                savings * tariff_rate, 4
            ),
            "evidence_id": reading_id,
            "status": "proposed"
        })

    maintenance = [{
        "event_id": "MNT-000001",
        "machine_id": machine_ids[0],
        "timestamp": (
            START + timedelta(days=5)
        ).isoformat(),
        "event_type": "inspection",
        "details": "Scheduled condition check"
    }]

    data = {
        "Plant": plants,
        "Meter": meter_rows,
        "Machine": machine_rows,
        "MeterMachine": assignments,
        "Shift": shifts,
        "Tariff": tariffs,
        "WeatherObservation": weather,
        "ProductionBatch": batch_rows,
        "EnergyReading": readings,
        "MaintenanceEvent": maintenance,
        "Recommendation": recommendations,
        "MeterSummary": summaries,
        "StateEvent": events
    }

    for name, rows in data.items():
        write_csv(out, name, rows)

    # Separate ground truth
    with (out / "ground_truth.csv").open(
        "w", newline="", encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "issue_type",
                "record_id",
                "meter_id",
                "timestamp",
                "expected_action"
            ]
        )

        writer.writeheader()
        writer.writerows(truth)

    (out / "ground_truth.json").write_text(
        json.dumps(truth, indent=2),
        encoding="utf-8"
    )

    manifest = {
        "seed": seed,
        "meters": meters,
        "days": days,
        "batches": batches,
        "interval_minutes": 15,
        "expected_intervals": meters * total_intervals,
        "counts": {
            name: len(rows)
            for name, rows in data.items()
        },
        "ground_truth_count": len(truth),
        "source": "fully synthetic; no external datasets"
    }

    (out / "source_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8"
    )

    checksums = {
        path.name: hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(out.glob("*.csv"))
    }

    (out / "checksums.json").write_text(
        json.dumps(checksums, indent=2),
        encoding="utf-8"
    )

    return manifest


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--out", default="data")
    parser.add_argument("--meters", type=int, default=20)
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--batches", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=SEED)

    args = parser.parse_args()

    print(
        json.dumps(
            build(
                args.out,
                args.meters,
                args.days,
                args.batches,
                args.seed
            ),
            indent=2
        )
    )