import argparse
import csv
import json

from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


CADENCE = timedelta(minutes=15)
TOLERANCE = 0.01


def load(path):
    """Load CSV data."""

    with open(
        path,
        newline="",
        encoding="utf-8"
    ) as file:

        return list(csv.DictReader(file))


def detect(folder):
    """Detect anomalies using independent business rules."""

    folder = Path(folder)

    readings = load(folder / "EnergyReading.csv")
    meters = load(folder / "Meter.csv")
    assignments = load(folder / "MeterMachine.csv")
    summaries = load(folder / "MeterSummary.csv")
    tariffs = load(folder / "Tariff.csv")

    found = []
    seen = set()

    by_meter = defaultdict(set)
    energy_sums = defaultdict(float)

    invalid_days = set()
    gap_days = set()

    assignment_by_meter = defaultdict(list)

    for assignment in assignments:
        assignment_by_meter[
            assignment["meter_id"]
        ].append(assignment)

    def flag(issue_type, record_id, meter_id, timestamp):

        found.append({
            "issue_type": issue_type,
            "record_id": record_id,
            "meter_id": meter_id,
            "timestamp": timestamp
        })

    # -------------------------------------
    # 1. ENERGY READING VALIDATION
    # -------------------------------------

    for reading in readings:

        meter_id = reading["meter_id"]
        timestamp = reading["timestamp"]
        reading_id = reading["reading_id"]

        machine_id = reading["machine_id"]

        dt = datetime.fromisoformat(timestamp)

        day = dt.date().isoformat()

        key = (meter_id, timestamp)

        # Duplicate detection
        if key in seen:

            flag(
                "duplicate_reading",
                reading_id,
                meter_id,
                timestamp
            )

            continue

        seen.add(key)

        by_meter[meter_id].add(dt)

        power_kw = float(reading["power_kw"])
        energy_kwh = float(reading["energy_kwh"])

        energy_sums[(meter_id, day)] += energy_kwh

        # ---------------------------------
        # Unit validation
        # ---------------------------------

        expected_energy = power_kw * 0.25

        if abs(energy_kwh - expected_energy) > TOLERANCE:

            flag(
                "unit_confusion",
                reading_id,
                meter_id,
                timestamp
            )

            invalid_days.add((meter_id, day))

        # ---------------------------------
        # Meter-machine hierarchy
        # ---------------------------------

        valid_assignment = any(

            assignment["machine_id"] == machine_id

            and dt >= datetime.fromisoformat(
                assignment["effective_from"]
            )

            and (
                not assignment["effective_to"]

                or dt < datetime.fromisoformat(
                    assignment["effective_to"]
                )
            )

            for assignment in assignment_by_meter[meter_id]
        )

        if not valid_assignment:

            flag(
                "hierarchy_violation",
                reading_id,
                meter_id,
                timestamp
            )

        # ---------------------------------
        # High idle consumption
        # ---------------------------------

        if (
            reading["state"] == "idle"
            and 10 < power_kw <= 65
        ):

            flag(
                "high_idle",
                reading_id,
                meter_id,
                timestamp
            )

        # ---------------------------------
        # Peak demand spike
        # ---------------------------------

        if power_kw > 65:

            flag(
                "peak_spike",
                reading_id,
                meter_id,
                timestamp
            )

        # ---------------------------------
        # Tariff validation
        # ---------------------------------

        applicable_tariffs = [

            tariff for tariff in tariffs

            if datetime.fromisoformat(
                tariff["effective_from"]
            ) <= dt

            < datetime.fromisoformat(
                tariff["effective_to"]
            )

            and int(tariff["start_hour"])
            <= dt.hour
            < int(tariff["end_hour"])
        ]

        if (
            len(applicable_tariffs) == 1
            and reading.get("applied_tariff_id")
        ):

            correct_tariff = applicable_tariffs[0]["tariff_id"]

            applied_tariff = reading["applied_tariff_id"]

            if applied_tariff != correct_tariff:

                flag(
                    "tariff_timezone_mismatch",
                    reading_id,
                    meter_id,
                    timestamp
                )

    # -------------------------------------
    # 2. MISSING INTERVAL DETECTION
    # -------------------------------------

    for meter in meters:

        meter_id = meter["meter_id"]

        meter_days = sorted(
            summary["day"]
            for summary in summaries
            if summary["meter_id"] == meter_id
        )

        if not meter_days:
            continue

        first = datetime.fromisoformat(
            meter_days[0] + "T00:00:00+00:00"
        )

        last = datetime.fromisoformat(
            meter_days[-1] + "T00:00:00+00:00"
        ) + timedelta(days=1)

        current = first

        while current < last:

            if current not in by_meter[meter_id]:

                missing_id = (
                    f"ENG-{meter_id}-"
                    f"{current.strftime('%Y%m%dT%H%M%SZ')}"
                )

                flag(
                    "meter_gap",
                    missing_id,
                    meter_id,
                    current.isoformat()
                )

                gap_days.add(
                    (
                        meter_id,
                        current.date().isoformat()
                    )
                )

            current += CADENCE

    # -------------------------------------
    # 3. METER TOTAL RECONCILIATION
    # -------------------------------------

    for summary in summaries:

        meter_id = summary["meter_id"]
        day = summary["day"]

        key = (meter_id, day)

        # Incomplete or invalid days require separate
        # reconciliation rather than mismatch classification.
        if key in gap_days or key in invalid_days:
            continue

        reported = float(summary["reported_kwh"])

        calculated = energy_sums.get(key, 0.0)

        difference = abs(reported - calculated)

        if difference > TOLERANCE:

            flag(
                "meter_total_mismatch",
                summary["summary_id"],
                meter_id,
                day
            )

    # -------------------------------------
    # 4. REMOVE DUPLICATE DETECTIONS
    # -------------------------------------

    unique = {
        (
            anomaly["issue_type"],
            anomaly["record_id"]
        ): anomaly

        for anomaly in found
    }

    return list(unique.values())


# -----------------------------------------
# 5. EVALUATION METRICS
# -----------------------------------------

def evaluate(folder):

    folder = Path(folder)

    truth = load(folder / "ground_truth.csv")

    predictions = detect(folder)

    actual = {
        (
            row["issue_type"],
            row["record_id"]
        )
        for row in truth
    }

    predicted = {
        (
            row["issue_type"],
            row["record_id"]
        )
        for row in predictions
    }

    true_positive = len(actual & predicted)

    false_positive = len(predicted - actual)

    false_negative = len(actual - predicted)

    precision = (
        true_positive / len(predicted)
        if predicted
        else 0.0
    )

    recall = (
        true_positive / len(actual)
        if actual
        else 0.0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "ground_truth": len(actual),
        "predictions": len(predicted),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4)
    }


# -----------------------------------------
# 6. MAIN
# -----------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data",
        default="data"
    )

    args = parser.parse_args()

    results = evaluate(args.data)

    print(
        json.dumps(
            results,
            indent=2
        )
    )