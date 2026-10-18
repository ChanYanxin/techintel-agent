"""Deterministic and auditable laboratory CSV analysis; not an AI4S model."""
from __future__ import annotations

import csv
import math
from pathlib import Path
from .config import experiments_path

REQUIRED = {"sample_id", "material", "family", "conductivity_s_cm", "temperature_c"}


def analyze_experiments(min_conductivity: float = 0.0, path: Path | None = None) -> dict:
    if not math.isfinite(min_conductivity) or min_conductivity < 0:
        raise ValueError("min_conductivity must be finite and non-negative")
    file = path or experiments_path()
    with file.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not REQUIRED.issubset(set(reader.fieldnames)):
            raise ValueError("Missing CSV required headers")
        samples = []
        for row in reader:
            val = float(row["conductivity_s_cm"])
            temp = float(row["temperature_c"])
            if not all(map(math.isfinite, (val, temp))) or val < 0:
                raise ValueError("Invalid experiment row")
            if val >= min_conductivity:
                samples.append({"sample_id": row["sample_id"], "material": row["material"],
                                "family": row["family"], "conductivity_s_cm": val,
                                "temperature_c": temp})
    samples.sort(key=lambda x: (-x["conductivity_s_cm"], x["sample_id"]))
    temperatures = sorted(set(x["temperature_c"] for x in samples))
    return {"total_matching": len(samples), "threshold_s_cm": min_conductivity,
            "samples": samples, "temperature_values_c": temperatures,
            "comparable_temperatures": len(temperatures) <= 1,
            "data_provenance": "synthetic CSV demo; not laboratory observations"}
