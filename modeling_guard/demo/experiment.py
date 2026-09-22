"""Tiny software acceptance fixture. No contest data, fitting, or training.

data.csv contains five explicitly synthetic reference/prediction pairs.
The fixture exercises a metric gate; its values are not research evidence.
"""

import csv
import json
from pathlib import Path

with Path("data.csv").open(encoding="utf-8", newline="") as stream:
    rows = list(csv.DictReader(stream))
errors = [abs(float(row["reference"]) - float(row["prediction"])) for row in rows]
mae = sum(errors) / len(errors)
Path("metrics.json").write_text(json.dumps({"mae": mae, "synthetic": True}, indent=2) + "\n", encoding="utf-8")
print(f"Synthetic acceptance fixture: {len(rows)} pairs, MAE = {mae:.2f}")
print("No model was trained. This is a software workflow demonstration.")
